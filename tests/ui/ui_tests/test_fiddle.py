from typing import *
import aqt
import aqt.gui_hooks
from pytestqt.qtbot import QtBot
import pytest
from ankitunes.result import Result, Ok, Err
from .data import notes
from anki.notes import Note

from .. import wait_hook


@pytest.mark.fiddle("Interactive debugging only")
def test_interactive(qtbot: QtBot, anki_running: aqt.AnkiApp) -> None:

	mw = aqt.mw
	assert mw is not None

	import ankitunes
	import ankitunes.col_note_type

	qtbot.add_widget(aqt.mw)
	mw.show()

	with wait_hook(qtbot, aqt.gui_hooks.main_window_did_init):
		pass

	col = mw.col
	assert col is not None

	migrator = ankitunes.col_note_type.TNTMigrator(col.models)

	vers_result = migrator.get_current_version()
	assert isinstance(vers_result, Ok)

	ver, nt = vers_result.value
	assert ver == ankitunes.col_note_type.TNTVersion.V2

	assert nt is not None

	# move to deck browser and wait
	with wait_hook(qtbot, aqt.gui_hooks.deck_browser_did_render):

		mw.moveToState("deckBrowser")

	qtbot.stop()
