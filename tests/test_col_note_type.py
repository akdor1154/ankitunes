from typing import Generator
from tests.utils import empty_collection

import anki
import anki.models
import anki.collection

from anki.models import NoteType, ModelManager
from anki.collection import Collection as Collection

import pytest

from . import utils

import contextlib

import ankitunes.col_note_type as NT
from ankitunes.result import Result, Ok, Err

@pytest.fixture
def mn(empty_collection: Collection) -> ModelManager:
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
	assert vers == Err(NT.VersionErr.ExistsUnmanaged())

def test_get_version_exist_unmanaged_2(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = {'something': 'or other'}

	vers = m.get_current_version()
	assert vers == Err(NT.VersionErr.ExistsUnmanaged())

def test_get_version_exist_unknown(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = nt.get('other', {})
		nt['other']['ankitunes_nt_version'] = 66

	vers = m.get_current_version()
	assert vers == Err(NT.VersionErr.ExistsUnknown(66))

def test_get_version_exist_known(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	with setupNoteType(mn) as nt:
		nt['name'] = TNT_NAME
		nt['other'] = nt.get('other', {})
		nt['other']['ankitunes_nt_version'] = 1

	vers = m.get_current_version()
	assert vers == Ok((NT.TNTVersion.V1, nt))



def test_migrate_v0_to_v1(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	m.migrate_v0_to_v1(None)

	nt = mn.byName(TNT_NAME)

	assert m.get_current_version() == Ok((NT.TNTVersion.V1, nt))

def test_migrate(mn: ModelManager) -> None:
	m = NT.TNTMigrator(mn)

	m.setup_tune_note_type()

	nt = mn.byName(TNT_NAME)
	assert m.get_current_version() == Ok((NT.TNTVersion.V1, nt))

	assert len(nt['tmpls']) == 1