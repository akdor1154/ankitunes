from dataclasses import dataclass
from typing import *

from anki.notes import Note
from tests.conftest import empty_collection

import anki
import anki.models
import anki.collection

from anki.notes import Note
from anki.cards import Card
from anki.models import NoteType, ModelManager
from anki.collection import Collection as AnkiCollection

import pytest

import contextlib

import ankitunes.col_note_type as NT
import ankitunes.tune_reviewer as reviewer
from ankitunes.result import Result, Ok, Err

from ankitunes.tunes.data import cooleys, cup_of_tea


@pytest.fixture
def mn(empty_collection: AnkiCollection) -> ModelManager:
	mn = ModelManager(empty_collection)

	m = NT.TNTMigrator(mn)
	m.setup_tune_note_type()

	return mn


@contextlib.contextmanager
def setupNoteType(mn: ModelManager) -> Generator[NoteType, None, None]:
	basic = mn.by_name("Basic")
	assert basic is not None
	nt = mn.copy(basic)
	yield nt
	mn.save(nt)


@dataclass
class ColAndStuff:
	col: AnkiCollection
	cooleys: Card
	cup_of_tea: Card
	some_other_note: Card


# Todo: share this with other tests when there are som,e
@pytest.fixture
def initialized_collection(
	empty_collection: AnkiCollection, mn: ModelManager
) -> Generator[ColAndStuff, None, None]:
	col = empty_collection

	m = NT.TNTMigrator(mn)

	basic_nt = mn.by_name("Basic")
	assert basic_nt is not None

	ankitunes_nt = mn.by_name(
		"AnkiTune"
	)  # TODO: will need to change if TNT_NAME becomes configurable
	assert ankitunes_nt is not None

	# add notes
	def toNote(note: Dict[str, Any], nt: NoteType) -> Note:
		n = anki.notes.Note(col=col, model=nt)
		for fieldName, fieldValue in note.items():
			n[fieldName] = fieldValue
		return n

	tune = toNote(cast(Dict[str, Any], cooleys), ankitunes_nt)
	tune2 = toNote(cast(Dict[str, Any], cup_of_tea), ankitunes_nt)
	not_tune = toNote({"Front": "Chao", "Back": "Hello"}, basic_nt)

	deck_id = col.decks.id("Test Deck", create=True)
	assert deck_id is not None

	for an in [tune, tune2, not_tune]:
		col.add_note(an, deck_id=deck_id)

	# save
	col.save()

	[cooleys_card, cup_of_tea_card, not_tune_card] = [
		col.getCard(n.card_ids()[0]) for n in [tune, tune2, not_tune]
	]

	yield ColAndStuff(col, cooleys_card, cup_of_tea_card, not_tune_card)

	col.close()


def test_create_set(initialized_collection: ColAndStuff) -> None:
	reviewer.is_reviewing_tunes = True
	html = reviewer.on_card_will_show_qn(
		"<html>Cooleys</html>",
		initialized_collection.cooleys,
		"reviewQuestion",
		initialized_collection.col,
		2,
	)
	assert "Cooleys" in html
	assert "Cup of Tea" in html

	html = reviewer.on_card_will_show_ans(
		"<html>Cooleys</html>", initialized_collection.cooleys, "reviewAnswer"
	)
	assert "Cooleys" in html
	assert "Cup of Tea" in html


def test_dont_crash_on_non_ankitunes_card(initialized_collection: ColAndStuff) -> None:
	html = reviewer.on_card_will_show_qn(
		"<html>Chao</html>",
		initialized_collection.some_other_note,
		"reviewQuestion",
		initialized_collection.col,
		2,
	)
	assert "Chao" in html
	html = reviewer.on_card_will_show_ans(
		"<html>Chao</html>", initialized_collection.some_other_note, "reviewAnswer"
	)
	assert "Chao" in html
