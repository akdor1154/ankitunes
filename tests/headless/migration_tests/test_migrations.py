# scenarios
from typing import *
from textwrap import dedent
from anki.cards import Card
from anki.collection import Collection as ACollection, SearchNode
from anki.decks import Deck
from anki.models import Field, ModelManager, NoteType
import anki.notes
import anki.cards
from ankitunes.col_note_type import (
	NoteFields_v1,
	NoteFields_v2,
	TNTMigrator,
	NoteFields,
)
from ankitunes.result import Result, Ok
import functools
import pytest

from .data import cooleys_v1, cup_of_tea_v1


v1_notes = [cooleys_v1, cup_of_tea_v1]


class ColFixture(NamedTuple):
	col: ACollection
	v1nt: NoteType
	migrator: TNTMigrator


@pytest.fixture
def v1_collection_with_notes(empty_collection: ACollection) -> ColFixture:
	return migrate_empty_to_v1(empty_collection, v1_notes)


def migrate_empty_to_v1(
	empty_collection: ACollection, notes: List[NoteFields_v1] = v1_notes
) -> ColFixture:

	col = empty_collection

	deck_id = col.decks.id("Test Deck", create=True)
	assert deck_id is not None

	migrator = TNTMigrator(col.models)

	v1nt = migrator.migrate_v0_to_v1(None).unwrap()
	migrator.migrate_template(v1nt)
	col.models.save(v1nt)

	# add notes
	def to_anki_note(note: NoteFields_v1) -> anki.notes.Note:
		n = anki.notes.Note(col=col, model=v1nt)
		for fieldName, fieldValue in note.items():
			n[fieldName] = fieldValue  # type: ignore
		return n

	ankiNotes = [to_anki_note(note) for note in notes]

	for an in ankiNotes:
		col.add_note(an, deck_id=deck_id)

	col.save()

	return ColFixture(col, v1nt, migrator)


def test_migration_v1_to_v2(v1_collection_with_notes: ColFixture) -> None:
	col, v1nt, migrator = v1_collection_with_notes

	v2nt = migrator.migrate_v1_to_v2(v1nt).unwrap()
	migrator.migrate_template(v2nt)
	col.models.save(v2nt)
	col.save()

	expected_cooleys_v2: NoteFields_v2 = {
		"Name": "Cooleys",
		"Key": "em",
		"Tune Type": "reel",
		"ABC": dedent(
			"""
			X: 1
			T: Cooley's
			R: reel
			M: 4/4
			L: 1/8
			K: Edor
			|:D2|EBBA B2 EB|B2 AB dBAG|FDAD BDAD|FDAD dAFD|
			EBBA B2 EB|B2 AB defg|afec dBAF|DEFD E2:|
			|:gf|eB B2 efge|eB B2 gedB|A2 FA DAFA|A2 FA defg|
			eB B2 eBgB|eB B2 defg|afec dBAF|DEFD E2:|
		"""
		),
		"Link": "https://thesession.org/tunes/1#setting1",
	}

	migrated_notes = [
		col.getNote(nid) for nid in col.find_notes(SearchNode(note="AnkiTune"))
	]
	actual_cooleys_v2 = next(c for c in migrated_notes if c["Name"] == "Cooleys")
	assert dict(actual_cooleys_v2.items()) == expected_cooleys_v2


def test_migration_v1_to_v2_no_key(empty_collection: ACollection) -> None:

	keyless_v1: NoteFields_v1 = {
		"Name": "Keyless",
		"Tune Type": "reel",
		"ABC": dedent(
			"""
			X: 1
			T: Keyless
			R: reel
			|:ABC:|
		"""
		),
		"Link": "https://thesession.org/tunes/1#setting1",
	}

	col, v1nt, migrator = migrate_empty_to_v1(empty_collection, [keyless_v1])

	v2nt = migrator.migrate_v1_to_v2(v1nt).unwrap()
	migrator.migrate_template(v2nt)
	col.models.save(v2nt)
	col.save()

	expected_keyless_v2: NoteFields_v2 = {
		"Name": "Keyless",
		"Key": "",
		"Tune Type": "reel",
		"ABC": dedent(
			"""
			X: 1
			T: Keyless
			R: reel
			|:ABC:|
		"""
		),
		"Link": "https://thesession.org/tunes/1#setting1",
	}

	migrated_notes = [
		col.getNote(nid) for nid in col.find_notes(SearchNode(note="AnkiTune"))
	]
	actual_keyless_v2 = next(c for c in migrated_notes if c["Name"] == "Keyless")
	assert dict(actual_keyless_v2.items()) == expected_keyless_v2


def test_migration_data_integrity(v1_collection_with_notes: ColFixture) -> None:
	""" I had a really weird bug where migrating and then restarting Anki would lead to missing cards. """
	col, _v1nt, _migrator = v1_collection_with_notes

	col.close(save=True)

	col = ACollection(col.path)
	mn = ModelManager(col)
	migrator = TNTMigrator(mn)

	# migrate
	migrator.setup_tune_note_type()

	# save
	nt = col.models.byName("AnkiTune")
	col.save()

	# retrieve
	nt = col.models.byName("AnkiTune")
	assert nt is not None

	retrieved_note_ids = col.find_notes(SearchNode(note="AnkiTune"))
	assert len(retrieved_note_ids) == len(v1_notes), "Missing notes!"

	card_ids = [
		card_id for note_id in retrieved_note_ids for card_id in col.card_ids_of_note(note_id)
	]
	assert len(card_ids) == len(v1_notes) * len(nt["tmpls"]), "Missing cards!"

	retrieved_notes = [col.getNote(note_id) for note_id in retrieved_note_ids]
	cards = [col.getCard(card_id) for card_id in card_ids]

	for originalNote in v1_notes:
		retrievedNote = next(n for n in retrieved_notes if n["Name"] == originalNote["Name"])
		assert retrievedNote.model() == nt

	for card in cards:
		assert card.ord == nt["tmpls"][0]["ord"]
