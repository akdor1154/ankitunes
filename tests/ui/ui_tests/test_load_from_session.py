from re import A, L
from traceback import print_exc
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QListWidget
from anki.collection import SearchNode
from anki.notes import Note

import aqt
import aqt.studydeck
import aqt.addcards
from pytestqt.qtbot import QtBot
import time
import ankitunes.col_note_type
import ankitunes.load_from_session_ui
from ankitunes.col_note_type import NoteFields
from ankitunes.result import Result, Ok, Err
from textwrap import dedent
from typing import *
import aqt.gui_hooks
import json
import pytestqt.exceptions
import functools

import threading

import os

from .. import wait_hook
from .data import notes

SHITTY_WAIT_MS = 200


def test_load_from_session_ui(anki_running: None, qtbot: QtBot) -> None:
	mw = aqt.mw
	assert mw is not None
	mw.show()

	col = mw.col
	assert col is not None

	nt = ankitunes.col_note_type.get_ankitunes_nt(col.models)

	deck = col.decks.byName("Tunes")
	assert deck is not None
	deck_id: int = deck["id"]

	# click the add button
	with wait_hook(qtbot, aqt.gui_hooks.add_cards_did_init) as cb:
		mw.onAddCard()
	add_window: ankitunes.load_from_session_ui.MyAddCards = cb.args[0]

	assert add_window.uriContainer is not None

	def select_model_with_name(model_name: str) -> None:
		class DealWithStupidBlockingDialog(threading.Thread):
			result: Optional[bool] = None
			chooser: Optional[aqt.studydeck.StudyDeck] = None
			cb: Callable[[], None] = None

			def __init__(self, *args, cb, **kwargs):
				super().__init__(*args, **kwargs)
				self.cb = cb

			def in_a_thread(self) -> None:
				def get_chooser() -> aqt.studydeck.StudyDeck:
					parent = add_window.notetype_chooser._widget
					dialog = next(
						(c for c in parent.children() if isinstance(c, aqt.studydeck.StudyDeck)), None
					)
					assert dialog is not None
					assert dialog.isVisible()
					return dialog

				def chooser_is_open() -> None:
					get_chooser()
					return None

				print("qtbot.waitUntil")
				qtbot.waitUntil(chooser_is_open)
				print("wait done")
				chooser = self.chooser = get_chooser()
				print("got chooser")

				i = chooser.names.index(model_name)
				chooser.form.list.setCurrentRow(i)
				chooser.accept()
				print("done")

			def run(self) -> None:
				try:
					self.in_a_thread()
					self.result = True
					self.cb()
				except:
					print_exc()
					self.result = False
					if self.chooser is not None:
						self.chooser.reject()
					raise

			def join(self, timeout: Optional[float] = None) -> None:
				super().join(timeout=timeout)
				assert self.result is True


		with qtbot.wait_callback() as cb:

			t = DealWithStupidBlockingDialog(None, name="oh plz", cb=cb)

			t.start()

			# switch to note type, this will block until window closes
			add_window.notetype_chooser.button.click()

		# this should already be done, just in case
		t.join()

	select_model_with_name("Basic")

	assert (
		add_window.uriContainer.isHidden()
	), "URI grabber was shown with a non anki tune note type"

	with wait_hook(qtbot, aqt.gui_hooks.editor_did_load_note):
		select_model_with_name("AnkiTune")

	assert (
		add_window.uriContainer.isVisible()
	), "URI grabber was not shown with the ankitune note type"

	try:
		# this fires a bunch of times, let's let them all finish before we wait for the proper one:
		while True:
			with wait_hook(qtbot, aqt.gui_hooks.editor_did_load_note, timeout=50):
				pass
	except pytestqt.exceptions.TimeoutError:
		# done
		pass

	with wait_hook(qtbot, aqt.gui_hooks.editor_did_load_note):
		add_window.uriContainer.uriField.setText(
			"https://thesession.org/tunes/20714#setting41112"
		)

	print("gotcha")

	note = add_window.editor.note
	assert note is not None

	from pprint import pprint

	pprint(dict(note))

	# write assertions this way so we are forced to update this
	# test when we make future changes to note type schema
	expectations: NoteFields = {
		"Name": "The Green Cake",
		"Key": "Amajor",
		"Tune Type": "reel",
		"ABC": dedent(
			"""\
		F2EF AFAB|cffe c2 BA|B3A B/c/d cB|AcBA BAFE|<br />
		 F2EF AFAB|cffe c2 BA|a3b afef|ecBc A2 BA:|"""
		),
		"Link": "https://thesession.org/tunes/20714#setting41112",
	}

	for field, val in expectations.items():
		assert isinstance(val, str)
		if field == "ABC":
			continue
		assert note[field] == val
	assert expectations["ABC"] in note["ABC"]

	with wait_hook(qtbot, aqt.gui_hooks.add_cards_did_add_note):
		add_window.addButton.click()

	add_window.closeButton.click()

	note_ids = col.find_notes(col.build_search_string(SearchNode(deck=deck["name"])))
	notes = [col.getNote(nid) for nid in note_ids]

	assert "The Green Cake" in [n["Name"] for n in notes]
