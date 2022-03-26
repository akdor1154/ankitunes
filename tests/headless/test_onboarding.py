import anki.notes
from anki.collection import Collection as AnkiCollection, SearchNode
from ankitunes.welcome_wizard import onboard


def test_empty_profile(empty_collection: AnkiCollection) -> None:
	"on an empty profile, check new deck and cards get created"
	col = empty_collection
	onboard(col)

	deck = col.decks.byName("Tunes")
	assert deck is not None

	note_ids = col.find_notes(col.build_search_string(SearchNode(deck=deck["name"])))
	assert len(note_ids) == 2

	notes = [col.getNote(id) for id in note_ids]

	cooleys = next(n for n in notes if n["Name"] == "Cooleys")
	assert cooleys is not None

	cup_of_tea = next(n for n in notes if n["Name"] == "The Cup of Tea")
	assert cup_of_tea is not None

	current_deck_id = col.decks.selected()
	assert current_deck_id == deck["id"]


def test_profile_with_deck_and_cards(empty_collection: AnkiCollection) -> None:
	"on a profile with an existing deck with some cards, check no cards get created"
	# setup
	col = empty_collection

	deck_id = col.decks.id("Tunes", create=True)
	assert deck_id is not None
	deck = col.decks.get(deck_id)
	assert deck is not None

	default_model = col.models.byName("Basic")

	note = anki.notes.Note(col, default_model)
	note["Front"] = "front"
	note["Back"] = "back"

	col.add_note(note, deck_id)

	# act
	onboard(col)

	# assert
	note_ids = col.find_notes(col.build_search_string(SearchNode(deck=deck["name"])))
	assert len(note_ids) == 1, "onboard mucked with a deck that it should have left alone"

	retrieved_note = col.getNote(note_ids[0])
	assert retrieved_note.id == note.id


def test_empty_profile_deck_config(empty_collection: AnkiCollection) -> None:
	"on an empty profile, check deck config gets created"
	col = empty_collection
	onboard(col)

	deck = col.decks.byName("Tunes")
	assert deck is not None

	conf = col.decks.confForDid(deck["id"])
	assert conf is not None

	assert conf["other"]["ankitunes"] == True


# on an profile with an existing deck with nested (unmanaged) config, check config gets set
def test_profile_existing_deck_config(empty_collection: AnkiCollection) -> None:
	"on an profile with an existing deck with nested (unmanaged) config, check config gets set"

	col = empty_collection

	deck_id = col.decks.id("Tunes", create=True)
	assert deck_id is not None
	deck = col.decks.get(deck_id)
	assert deck is not None

	onboard(col)

	deck = col.decks.byName("Tunes")
	assert deck is not None

	conf = col.decks.confForDid(deck["id"])
	assert conf is not None

	assert conf["other"]["ankitunes"] == True


# on a profile with an existing deck with linked config, check config gets set
def test_profile_existing_linked_deck_config(empty_collection: AnkiCollection) -> None:
	"on an profile with an existing deck with nested (unmanaged) config, check config gets set"

	col = empty_collection

	deck_id = col.decks.id("Tunes", create=True)
	assert deck_id is not None
	deck = col.decks.get(deck_id)
	assert deck is not None

	conf = col.decks.confForDid(deck["id"])
	conf["other"] = {"ankitunes": False}

	col.decks.setConf(conf, deck_id)

	assert col.decks.confForDid(deck["id"])["other"] == {"ankitunes": False}

	onboard(col)

	deck = col.decks.byName("Tunes")
	assert deck is not None

	conf = col.decks.confForDid(deck["id"])
	assert conf is not None

	assert conf["other"]["ankitunes"] == True
