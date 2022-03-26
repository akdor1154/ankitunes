from __future__ import annotations
from anki.collection import SearchNode, Collection as AnkiCollection
from . import col_note_type
from typing import *
from .util import mw
from .tunes.data import cooleys, cup_of_tea
from .col_note_type import NoteFields
import anki.notes
import aqt.gui_hooks
import aqt

if TYPE_CHECKING:
	from anki.decks import DeckConfigDict

DECK_NAME = "Tunes"


def setup_deck(col: AnkiCollection, deck_id: Optional[int] = None) -> int:

	if deck_id is None:
		# create deck
		deck_id = col.decks.id(DECK_NAME, create=True)
		assert deck_id is not None

	deck = col.decks.get(deck_id, default=False)
	assert deck is not None

	# get existing config
	config: Optional[DeckConfigDict] = next(
		(
			conf
			for conf in col.decks.all_config()
			if conf.get("other", {}).get("ankitunes", False) == True
		),
		None,
	)

	# if no existing config
	if config is None:
		config_id = deck.get("conf", None)
		if config_id is not None:
			config = col.decks.get_config(config_id)
		# if no config attached to deck
		else:
			config = col.decks.add_config("AnkiTunes")

	assert config is not None

	# manage config
	config["other"] = config.get("other", {})
	config["other"]["ankitunes"] = True

	# set new steps intervals
	config["new"] = config.get("new", {})
	config["new"]["delays"] = [1, 10, 480, 1440]

	# set reviews intervals
	config["rev"] = config.get("rev", {})
	config["rev"]["per_day"] = 20
	config["rev"]["max_ivl"] = 30  # days

	col.decks.update_config(config)

	deck["conf"] = config["id"]
	deck["name"] = DECK_NAME
	col.decks.update(deck)

	col.save()

	return deck_id


T = TypeVar("T")


def not_none(thing: Optional[T]) -> T:
	assert thing is not None
	return thing


def setup_cards(col: AnkiCollection, deck_id: int) -> None:

	deck: Dict[str, Any] = not_none(col.decks.get(deck_id, default=False))

	nt = col_note_type.migrate(col)

	notes = [cooleys, cup_of_tea]

	# add notes
	def toAnkiNote(note: NoteFields) -> Optional[anki.notes.Note]:
		"""creates a new note. Returns None if a note with this name already exists."""
		existing = col.find_notes(f'"Name:{note["Name"]}"', SearchNode(deck=deck["name"]))

		if len(existing) > 0:
			return None

		n = anki.notes.Note(col=col, model=nt)
		for fieldName, fieldValue in note.items():
			# https://github.com/python/mypy/issues/7981 would remove the need for this
			assert isinstance(fieldValue, str)
			n[fieldName] = fieldValue
		return n

	ankiNotes = [toAnkiNote(note) for note in notes]

	for an in ankiNotes:
		if an is None:
			continue
		col.add_note(an, deck_id=deck_id)

	col.save()


def onboard(col: AnkiCollection) -> None:
	# always set up a Tunes deck
	deck_id = setup_deck(col)

	deck = col.decks.get(deck_id, default=False)
	assert deck is not None

	# if the deck already has some notes
	notes = col.find_notes(col.build_search_string(SearchNode(deck=deck["name"])))
	if len(notes) > 0:
		# abort
		return

	# else add some cards
	setup_cards(col, deck_id)

	# and set it as the default
	col.decks.select(deck_id)
	col.save()


def _hook() -> None:
	col = mw().col
	assert col is not None
	onboard(col)
	mw().deckBrowser.refresh()


def setup() -> None:
	aqt.gui_hooks.profile_did_open.append(_hook)
