from profiles.working.addons21.ankitunes.col_note_type import TNTVersion
from typing import *
from tests.utils import empty_collection

import anki
import anki.models
import anki.collection

from anki.models import NoteType, ModelManager
from anki.collection import Collection as AnkiCollection

import pytest

from . import utils

import contextlib

import ankitunes.col_note_type as NT
from ankitunes.result import Result, Ok, Err

@pytest.fixture
def mn(empty_collection: AnkiCollection) -> ModelManager:
	return ModelManager(empty_collection)


def test_get_version_empty(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)
	vers = m.get_current_version()
	assert vers == Ok((NT.FakeVersion.NotExist, None))

# Will need to change if becomes configurable
TNT_NAME = 'AnkiTune'

@contextlib.contextmanager
def setupNoteType(mn: ModelManager) -> Generator[NoteType, None, None]:
	basic = mn.byName('Basic')
	assert basic is not None
	nt = mn.copy(basic)
	yield nt
	mn.save(nt)

def test_get_version_exist_unmanaged_1(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME

	vers = m.get_current_version()
	assert vers == Ok((NT.FakeVersion.NotExist, None))

	migrate_res = m.migrate(vers.unwrap())
	assert migrate_res == Err(NT.MigrationErr.NameTaken(TNT_NAME))

def test_get_version_exist_unmanaged_2(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = {'something': 'or other'}

	vers = m.get_current_version()
	assert vers == Ok((NT.FakeVersion.NotExist, None))

	migrate_res = m.migrate(vers.unwrap())
	assert migrate_res == Err(NT.MigrationErr.NameTaken(TNT_NAME))

def test_get_version_exist_unknown(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = nt.get('other', {})
		nt['other']['ankitunes_nt'] = True
		nt['other']['ankitunes_nt_version'] = 66

	vers = m.get_current_version()
	assert vers == Err(NT.VersionErr.ExistsUnknown(66))

def test_get_version_exist_known(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = nt.get('other', {})
		nt['other']['ankitunes_nt'] = True
		nt['other']['ankitunes_nt_version'] = 1

	vers = m.get_current_version()
	assert vers == Ok((NT.TNTVersion.V1, nt))

@pytest.mark.parametrize(
	"version",
	TNTVersion
)
def test_migrate_version(mn: ModelManager, version: TNTVersion) -> None:
	m = NT.TNTMigrator(mn)

	_nt: Optional[NoteType] = None
	current_version = 0
	for current_version in range(version):
		next_version = current_version+1
		migrator = getattr(m, f'migrate_v{current_version}_to_v{next_version}')
		_nt = migrator(_nt).unwrap()
		mn.save(cast(NoteType, _nt))

	nt = mn.byName(TNT_NAME)

	assert m.get_current_version() == Ok((version, nt))

def test_migrate(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	m.setup_tune_note_type()

	nt = mn.byName(TNT_NAME)
	assert m.get_current_version() == Ok((NT.TNTVersion.V1, nt))

	assert nt is not None
	assert len(nt['tmpls']) == 1