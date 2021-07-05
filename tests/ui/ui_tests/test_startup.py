

from anki.notes import Note

import aqt
from pytestqt.qtbot import QtBot
import time
from ankitunes.result import Result, Ok, Err
from textwrap import dedent
from typing import *
import aqt.gui_hooks
import json

import os

from .. import wait_hook
from .data import notes

SHITTY_WAIT_MS = 200

def test_ui(anki_running: aqt.AnkiApp, qtbot: QtBot) -> None:
	mw = aqt.mw
	assert mw is not None

	import ankitunes
	import ankitunes.col_note_type

	mw.show()

	with wait_hook(qtbot, aqt.gui_hooks.main_window_did_init):
		pass

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
	with wait_hook(qtbot, aqt.gui_hooks.deck_browser_did_render):
		mw.moveToState("deckBrowser")


	# move to deck overview and wait
	with wait_hook(qtbot, aqt.gui_hooks.overview_did_refresh):
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
	with wait_hook(qtbot, aqt.gui_hooks.reviewer_did_show_question):
		pass

	# wait for reviewer webview
	with qtbot.waitCallback() as cb:
		mw.reviewer.web.evalWithCallback(";", cb)

	qtbot.wait(SHITTY_WAIT_MS)

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


	# wait for the reviewer to show
	with wait_hook(qtbot, aqt.gui_hooks.reviewer_did_show_answer):
		pass

	# wait for reviewer webview
	with qtbot.waitCallback() as cb:
		mw.reviewer.web.evalWithCallback(";", cb)

	qtbot.wait(SHITTY_WAIT_MS)

	# check both tunes are there
	with qtbot.waitCallback() as cb:
		mw.reviewer.web.page().findText('Cooley\'s', resultCallback=cb)
	assert cb.args == [True]

	with qtbot.waitCallback() as cb:
		mw.reviewer.web.page().findText('The Cup of Tea', resultCallback=cb)
	assert cb.args == [True]

	# check sheet music is there - find a <title> in <svg> with the tune title.
	# tuneName needs to match title in ABC, not title in anki note field.
	def checkForTitleJs(tuneName: str):
		return f'''
			var elems = Array.from(document.querySelectorAll('svg title'));
			var matching = (
				elems
				.filter(e => e.textContent.includes({json.dumps(tuneName)}))
			);
			(matching.length == 1)
		'''


	with qtbot.waitCallback() as cb:
		print(checkForTitleJs('Cooley\'s'))
		mw.reviewer.web.evalWithCallback(checkForTitleJs('Cooley\'s'), cb)
	assert cb.args == [True]


	with qtbot.waitCallback() as cb:
		mw.reviewer.web.evalWithCallback(checkForTitleJs('The Cup Of Tea'), cb)
	assert cb.args == [True]
