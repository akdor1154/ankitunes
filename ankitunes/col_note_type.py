from enum import Enum, auto, IntEnum
from typing import *

import anki
import re
import functools

from anki.models import NoteType, ModelManager
from anki.notes import Note

from .result import Result, Ok, Err

# TNT - Tune Note Type

# TODO: allow configuration of this.
TNT_NAME = 'Tune'


class TNTVersion(IntEnum):
	V1 = 1
	#V2 = 2

class FakeVersion(IntEnum):
	NotExist = 0

VersionResult = Union[
	Tuple[FakeVersion, None],
	Tuple[TNTVersion, NoteType]
]


class VersionErr:
	class ExistsUnmanaged(NamedTuple):
		msg: str = 'Note type exists but is not managed by AnkiTunes'
	class ExistsUnknown(NamedTuple):
		version: int
		msg: str = 'Note type version is not known to this version of AnkiTunes'

_VersionErr = Union[VersionErr.ExistsUnmanaged, VersionErr.ExistsUnknown]

NT_VER_KEY = 'ankitunes_nt_version'

# Migrations have probably had the shit overengineered out of them..
# but this is one thing I will try to get right on iteration 0 and not
# be stuck recovering user data on iteration 2..

# TNTMigration has a bunch of methods, e.g.
# migration_v0_to_v1(self, nt) -> nt
# They are registered with the @migration decorator,
# checked for sanity, and stored in _migrations.
Migration = Callable[['TNTMigrator', NoteType], NoteType]

_migrations: Dict[TNTVersion, Migration] = {}

F = TypeVar('F', bound=Migration)

NAME_REGEXP = re.compile(r'migrate_v(?P<from>\d+)_to_v(?P<to>\d+)')
def migration(migrateFn: F) -> F:
	if (match := NAME_REGEXP.fullmatch((migrateFn.__name__))) is None:
		raise Exception(f'Bad migration name: {migrateFn.__name__}')
	v_from, v_to = map(int, (match.group('from'), match.group('to')))
	assert v_to == v_from + 1, f'{migrateFn.__name__} needs to be migrate_vn_to_vn+1.'
	ver = TNTVersion(v_to)
	_migrations[ver] = migrateFn
	return migrateFn

class TNTMigrator:
	mn: ModelManager

	def __init__(self, mn: ModelManager):
		self.mn = mn

	def get_current_version(self) -> Result[VersionResult, _VersionErr]:
		existing_nt = self.mn.byName(TNT_NAME)
		if existing_nt is None:
			return Ok((FakeVersion.NotExist, None))
		if "other" not in existing_nt:
			return Err(VersionErr.ExistsUnmanaged())
		if NT_VER_KEY not in existing_nt["other"]:
			return Err(VersionErr.ExistsUnmanaged())

		version: Any = existing_nt["other"][NT_VER_KEY]
		if not isinstance(version, int):
			raise Exception(f"Note type {existing_nt.get('name', '[unnamed]')} has corrupt version {version}")

		try:
			typed_version = TNTVersion(version)
			return Ok((typed_version, existing_nt))
		except ValueError:
			return Err(VersionErr.ExistsUnknown(version))

	def migrate(self, vr: VersionResult) -> None:
		version, nt = vr
		for target_version in sorted(TNTVersion):
			if version >= target_version:
				continue

			if not version+1 == target_version:
				raise Exception('migration invariant check failed!')

			migrate_func = _migrations[target_version]

			nt = migrate_func(self, cast(NoteType, nt))

	@migration
	def migrate_v0_to_v1(self, nt: Optional[NoteType]) -> NoteType:
		# for v0, nt is always None...
		if nt is not None:
			raise Exception('migration invariant check 2 failed!')

		basic = self.mn.byName('Basic')
		if basic is None:
			raise Exception('couldn\'t get Basic card type')

		nt = self.mn.copy(basic)

		nt['name'] = TNT_NAME
		for field in [
			self.mn.new_field('Tune Type'),
			self.mn.new_field('ABC'),
			self.mn.new_field('Link')
		]:
			self.mn.add_field(nt,  field)

		nt['other'] = nt.get('other', {})
		nt['other'][NT_VER] = 1

		self.mn.save(nt)
		return nt

	def setup_tune_note_type(self) -> None:
		#if not exist, create
		#if exist, run migrations
		current_version_res = self.get_current_version()

		if not isinstance(current_version_res, Ok):
			#TODO error handling
			raise Exception('bang')

		self.migrate(current_version_res.value)

for ver in TNTVersion:
	if _migrations.get(ver) is None:
		raise Exception(f'missing migration for {ver}')