from enum import Enum, auto, IntEnum
from typing import *

if TYPE_CHECKING:
	from typing_extensions import TypeGuard

import anki
import re
import functools

from anki.collection import Collection as AnkiCollection
from anki.models import NoteType, ModelManager
from anki.notes import Note
import aqt
import aqt.gui_hooks

from .col_card_type import TemplateMigrator, TPL_VER_KEY
from .util import mw
from .errors import ErrorMode, error

from .result import Result, Ok, Err

import logging

logger = logging.getLogger(__name__)

# TNT - Tune Note Type


NoteFields_v1 = TypedDict(
	"NoteFields_v1", {"Name": str, "Tune Type": str, "ABC": str, "Link": str}
)

NoteFields_v2 = TypedDict(
	"NoteFields_v2", {"Name": str, "Key": str, "Tune Type": str, "ABC": str, "Link": str}
)


NoteFields = NoteFields_v1

# TODO: allow configuration of this.
TNT_NAME = "AnkiTune"


class TNTVersion(IntEnum):
	V1 = 1
	# V2 = 2


class FakeVersion(IntEnum):
	NotExist = 0


VersionResult = Union[Tuple[FakeVersion, None], Tuple[TNTVersion, NoteType]]


class VersionErr:
	class ExistsUnmanaged(NamedTuple):
		msg: str = "Note type exists but is not managed by AnkiTunes"

	class ExistsUnknown(NamedTuple):
		version: int
		msg: str = "Note type version is not known to this version of AnkiTunes"


_VersionErr = Union[VersionErr.ExistsUnmanaged, VersionErr.ExistsUnknown]

NT_KEY = "ankitunes_nt"
NT_VER_KEY = "ankitunes_nt_version"


class MigrationErr:
	class NameTaken(NamedTuple):
		name: str

		@property
		def msg(self) -> str:
			return f"Note type with name {self.name} already exists but is unmanaged by AnkiTunes! Please rename it.."


_MigrationErr = Union[MigrationErr.NameTaken]

# Migrations have probably had the shit overengineered out of them..
# but this is one thing I will try to get right on iteration 0 and not
# be stuck recovering user data on iteration 2..

# TNTMigration has a bunch of methods, e.g.
# migration_v0_to_v1(self, nt) -> nt
# They are registered with the @migration decorator,
# checked for sanity, and stored in _migrations.
Migration = Callable[["TNTMigrator", NoteType], Result[NoteType, _MigrationErr]]

_migrations: Dict[TNTVersion, Migration] = {}

F = TypeVar("F", bound=Migration)

NAME_REGEXP = re.compile(r"migrate_v(?P<from>\d+)_to_v(?P<to>\d+)")


def migration(migrateFn: F) -> F:
	if (match := NAME_REGEXP.fullmatch((migrateFn.__name__))) is None:
		raise Exception(f"Bad migration name: {migrateFn.__name__}")
	v_from, v_to = map(int, (match.group("from"), match.group("to")))
	assert v_to == v_from + 1, f"{migrateFn.__name__} needs to be migrate_vn_to_vn+1."
	ver = TNTVersion(v_to)
	_migrations[ver] = migrateFn
	return migrateFn


class TNTMigrator:
	mn: ModelManager

	def __init__(self, mn: ModelManager):
		self.mn = mn

	@staticmethod
	def _get_version(
		note_types: Sequence[NoteType],
	) -> Result[VersionResult, _VersionErr]:
		existing_nts = [nt for nt in note_types if nt.get("other", {}).get(NT_KEY) == True]
		if len(existing_nts) > 1:
			error(
				"I found multiple note types managed by AnkiTunes. I can't deal with this: \n"
				"if you have cloned the AnkiTunes note type yourself, please remove the clone.\n"
				"If you reject the above accusation of guilt, please raise an issue on the AnkiTunes issue tracker.",
				mode=ErrorMode.RAISE,
			)
		if len(existing_nts) == 0:
			return Ok((FakeVersion.NotExist, None))

		existing_nt = existing_nts[0]

		if NT_VER_KEY not in existing_nt["other"]:
			raise Exception(f"Note type {existing_nt.get('name', '[unnamed]')} has no version")
		version: Any = existing_nt["other"][NT_VER_KEY]
		if not isinstance(version, int):
			raise Exception(
				f"Note type {existing_nt.get('name', '[unnamed]')} has corrupt version {version}"
			)

		try:
			typed_version = TNTVersion(version)
			return Ok((typed_version, existing_nt))
		except ValueError:
			return Err(VersionErr.ExistsUnknown(version))

	def get_current_version(self) -> Result[VersionResult, _VersionErr]:
		return TNTMigrator._get_version(self.mn.all())

	def migrate(self, vr: VersionResult) -> Result[NoteType, _MigrationErr]:
		version, nt = vr
		for target_version in sorted(TNTVersion):
			logger.debug(f"target version is {target_version}")
			logger.debug(f"current version is {version}")
			if version >= target_version:
				logger.debug("skipping migration")
				continue

			if not version + 1 == target_version:
				raise Exception("migration invariant check failed!")

			migrate_func = _migrations[target_version]
			logger.info(f"migrating with {migrate_func}")
			migrate_res = migrate_func(self, cast(NoteType, nt))
			if isinstance(migrate_res, Err):
				return migrate_res
			nt = migrate_res.value

			self.mn.save(nt)

		return Ok(cast(NoteType, nt))

	@migration
	def migrate_v0_to_v1(self, nt: Optional[NoteType]) -> Result[NoteType, _MigrationErr]:
		# for v0, nt is always None...

		if nt is not None:
			raise Exception("migration invariant check 2 failed!")

		existing_nt = self.mn.byName(TNT_NAME)
		if existing_nt is not None:
			return Err(MigrationErr.NameTaken(TNT_NAME))

		nt = self.mn.new(TNT_NAME)

		nt["name"] = TNT_NAME
		for field in [
			self.mn.new_field("Name"),
			self.mn.new_field("Tune Type"),
			self.mn.new_field("ABC"),
			self.mn.new_field("Link"),
		]:
			self.mn.add_field(nt, field)

		# we need to do this now as well as after the migration - we want our template
		# to be the only one if we are setting up the card type from scratch.
		nt["tmpls"] = [TemplateMigrator(self.mn).build_template()]
		nt["tmpls"][0]["ord"] = 0

		nt["other"] = nt.get("other", {})
		nt["other"][NT_KEY] = True
		nt["other"][NT_VER_KEY] = 1

		return Ok(nt)

	def migrate_template(self, nt: NoteType) -> None:
		"""Updates the template in nt to be our Tune renderer. nt is assumed to be our Tune."""

		# Search templates for any managed by us.
		existing_templates = [
			(i, t)
			for i, t in enumerate(nt["tmpls"])
			if t.get("other", {}).get(TPL_VER_KEY) == True
		]

		if len(existing_templates) > 1:
			raise Exception("Multiple Ankitunes-managed templates detected. Aborting.")

		our_template = TemplateMigrator(self.mn).build_template()

		# if existing template, update it
		if len(existing_templates) == 1:
			i, old_t = existing_templates[0]

			nt["tmpls"][i] = our_template
			nt["tmpls"][i]["ord"] = old_t["ord"]
		# else append
		else:
			self.mn.add_template(nt, our_template)
			nt["tmpls"][0]["ord"] = 0

		self.mn.save(nt)

	def setup_tune_note_type(self) -> NoteType:

		# if not exist, create
		# if exist, run migrations
		current_version_res = self.get_current_version()

		if not isinstance(current_version_res, Ok):
			from pprint import pprint

			pprint(current_version_res)
			error(
				"AnkiTunes version migration failed. This may be a bug,<br />"
				"or it may be because you went and screwed around with the AnkiTunes-managed<br />"
				"note definitions. If you are sure of your innocence in this matter, please raise a bug.",
				mode=ErrorMode.RAISE,
			)

		migrate_res = self.migrate(current_version_res.value)

		if not isinstance(migrate_res, Ok):
			from pprint import pprint

			pprint(migrate_res)
			raise Exception(
				"AnkiTunes version migration failed. Please raise a bug. Error: "
				+ migrate_res.err_value.msg
			)

		nt = migrate_res.value

		self.migrate_template(nt)

		return nt


for ver in TNTVersion:
	if _migrations.get(ver) is None:
		raise Exception(f"missing migration for {ver}")


def migrate(col: AnkiCollection) -> NoteType:
	mn = col.models
	return TNTMigrator(mn).setup_tune_note_type()


def is_ankitunes_nt(note_type: NoteType) -> "TypeGuard[NoteFields]":
	"tests if note_type is a fully migrated ankitunes notetype"
	ver_result = TNTMigrator._get_version([note_type])
	if isinstance(ver_result, Ok):
		ver, nt = ver_result.value
		return ver is max(v for v in TNTVersion)
	else:
		return False


def get_ankitunes_nt(mn: Optional[ModelManager] = None) -> NoteType:
	mn = mn or mw().col.models
	return TNTMigrator(mn).setup_tune_note_type()


def _hook() -> None:
	col = mw().col
	migrate(col)
	return None


def setup() -> None:
	aqt.gui_hooks.profile_did_open.append(_hook)
