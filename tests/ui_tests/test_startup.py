from PyQt5 import QtWebEngineWidgets
from anki.models import NoteTypeNameIDUseCount
from anki.notes import Note
from .. import anki_testing
import aqt
from pytestqt.qtbot import QtBot
import time
from ankitunes.result import Result, Ok, Err
from textwrap import dedent
from typing import *
import aqt.gui_hooks


Note_v1 = TypedDict('Note_v1', {
	'Name': str,
	'Tune Type': str,
	'ABC': str,
	'Link': str
})

notes: List[Note_v1] = [
	{
		'Name': "Cooley's",
		'Tune Type': 'em reel',
		'ABC': dedent('''
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
		'''),
		'Link': 'https://thesession.org/tunes/1#setting1'
	},
	{
		'Name': 'The Cup of Tea',
		'Tune Type': 'Edor reel',
		'ABC': dedent('''
			X: 1
			T: The Cup Of Tea
			R: reel
			M: 4/4
			L: 1/8
			K: Edor
			|:BAGF GEEF|GEBE GEEA|BAGF GEEG|FDAD FDDA|
			BAGF GEEF|GEBE GEEA|B2 BA GABc|dBAG FD D2:|
			K:D
			|:d2 eg fdec|d2 eg fB B2|d2 eg fdec|dBAG FD D2|
			d2 eg fdec|dfaf g2 fg|afge fdec|dBAG FD D2:|
			|:FAdA FABA|FAdA FEE2|FAdA FABc|dBAG FD D2|
			FAdA FABA|FAde fee2|fdec dBAF|GBAG FD D2:|
		'''),
		'Link': 'https://thesession.org/tunes/20#setting20'
	}
]

def test_ui(qtbot: QtBot) -> None:
	with anki_testing.anki_running() as app:
		mw = aqt.mw
		assert mw is not None

		import ankitunes
		import ankitunes.col_note_type

		qtbot.add_widget(aqt.mw)
		mw.show()

		with qtbot.waitCallback() as cb:
			aqt.gui_hooks.main_window_did_init.append(cb)

		col = mw.col
		assert col is not None

		migrator = ankitunes.col_note_type.TNTMigrator(col.models)

		vers_result = migrator.get_current_version()
		assert isinstance(vers_result, Ok)

		ver, nt = vers_result.value
		assert ver == ankitunes.col_note_type.TNTVersion.V1

		assert nt is not None

		deck_id = col.decks.id('Test Desk', create=True)
		assert deck_id is not None

		for note_input in notes:
			n = Note(col,  nt)
			for field, val in note_input.items():
				n[field] = val
			col.add_note(n, deck_id)

		col.save()

		# move to deck browser and wait
		with qtbot.waitCallback() as cb:
			aqt.gui_hooks.deck_browser_did_render.append(cb)

			mw.moveToState("deckBrowser")


		# move to deck overview and wait
		with qtbot.waitCallback() as cb:
			aqt.gui_hooks.overview_did_refresh.append(cb)

			mw.deckBrowser._selDeck(deck_id)


		# wait for overview web to render
		with qtbot.waitCallback() as cb:
			mw.overview.web.evalWithCallback(";", cb)


		# check the set button is there
		with qtbot.waitCallback() as cb:
			mw.overview.web.page().findText('Practice Sets', resultCallback=cb)
		assert cb.args == [True]

		# click study sets
		mw.overview.web.eval('''
			document.getElementById('study_sets').click()
		''')

		# wait for the reviewer to show
		with qtbot.waitCallback() as cb:
			aqt.gui_hooks.reviewer_did_show_question.append(cb)

		# wait for reviewer webview
		with qtbot.waitCallback() as cb:
			mw.reviewer.web.evalWithCallback(";", cb)

		qtbot.wait(100)

		# check both tunes are there
		with qtbot.waitCallback() as cb:
			mw.reviewer.web.page().findText('Cooley\'s', resultCallback=cb)
		assert cb.args == [True]

		with qtbot.waitCallback() as cb:
			mw.reviewer.web.page().findText('The Cup of Tea', resultCallback=cb)
		assert cb.args == [True]

		# click the answer button
		mw.reviewer.bottom.web.eval('''
			document.getElementById('ansbut').click()
		''')

		# wait for them notes
		qtbot.wait(500)


		# check both tunes are there
		with qtbot.waitCallback() as cb:
			mw.reviewer.web.page().findText('Cooley\'s', resultCallback=cb)
		assert cb.args == [True]

		with qtbot.waitCallback() as cb:
			mw.reviewer.web.page().findText('The Cup of Tea', resultCallback=cb)
		assert cb.args == [True]