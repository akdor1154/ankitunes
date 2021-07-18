# scenarios
from typing import *
from textwrap import dedent
from anki.cards import Card
from anki.collection import Collection as ACollection, SearchNode
from anki.decks import Deck
from anki.models import Field, ModelManager
import anki.notes
import anki.cards
from ankitunes.col_note_type import TNTMigrator, NoteFields
from ankitunes.result import Result, Ok

from ankitunes.tunes.data import cooleys, cup_of_tea


notes = [cooleys, cup_of_tea]


def test_migration_data_integrity(empty_collection: ACollection) -> None:
	col = empty_collection
	deck_id = col.decks.id("Test Deck", create=True)
	assert deck_id is not None
	mn = ModelManager(col)
	migrator = TNTMigrator(mn)

	# migrate to v1
	v1nt = migrator.migrate_v0_to_v1(None).unwrap()
	migrator.migrate_template(v1nt)
	mn.save(v1nt)

	# save
	col.save()

	# add notes
	def toAnkiNote(note: NoteFields) -> anki.notes.Note:
		n = anki.notes.Note(col=col, model=v1nt)
		for fieldName, fieldValue in note.items():
			n[fieldName] = fieldValue  # type: ignore
		return n

	ankiNotes = [toAnkiNote(note) for note in notes]

	for an in ankiNotes:
		col.add_note(an, deck_id=deck_id)

	# save
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
	assert len(retrieved_note_ids) == len(notes), "Missing notes!"

	card_ids = [
		card_id for note_id in retrieved_note_ids for card_id in col.card_ids_of_note(note_id)
	]
	assert len(card_ids) == len(notes) * len(nt["tmpls"]), "Missing cards!"

	retrieved_notes = [col.getNote(note_id) for note_id in retrieved_note_ids]
	cards = [col.getCard(card_id) for card_id in card_ids]

	for originalNote in notes:
		retrievedNote = next(
			n
			for n in retrieved_notes
			if all(n[field] == fieldValue for field, fieldValue in originalNote.items())
		)
		assert retrievedNote is not None
		assert retrievedNote.model() == nt

	for card in cards:
		assert card.ord == nt["tmpls"][0]["ord"]
