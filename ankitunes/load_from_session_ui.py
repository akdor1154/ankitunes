from __future__ import annotations

from PyQt5.QtCore import (
    QMetaObject,
    QObject,
    QRegExp,
    QRunnable,
    QThread,
    QTimer,
    pyqtSignal,
    pyqtSlot,
    Qt,
)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QWidget
from .vendor import qtwaitingspinner

from anki.notes import Note
import aqt
from aqt.main import AnkiQt
from aqt.addcards import AddCards

from . import col_note_type
from .col_note_type import TNTMigrator, NoteFields
from . import load_from_session
from .load_from_session import GrabResult
from .util import mw
from .result import Result, Ok, Err

from typing import *

if TYPE_CHECKING:
	from anki.models import NotetypeId


class URIContainer(QWidget):
	uriField: QLineEdit
	uriSpinner: qtwaitingspinner.QtWaitingSpinner

	gotTuneURI = pyqtSignal(str, name="gotTuneURI")
	_lastURIEmit: Optional[str] = None

	_loading: bool = False
	_loadingReset: bool = False
	_loadingURI: Optional[str] = None

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(parent)

		# widgets
		uriLayout = QHBoxLayout()

		uriLabel = QLabel(self)
		uriLabel.setText("Quick add from TheSession.org")

		uriField = QLineEdit(self)
		uriField.setPlaceholderText("e.g. https://thesession.org/tunes/1#setting69")
		uriField.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

		uriSpinner = qtwaitingspinner.QtWaitingSpinner(self, centerOnParent=False)
		# uriSpinner.start()

		uriLayout.addWidget(uriLabel)
		uriLayout.addWidget(uriField)
		uriLayout.addWidget(uriSpinner)

		self.setLayout(uriLayout)

		# save widgets
		self.uriField = uriField
		self.uriSpinner = uriSpinner

		# validation
		VALID_REGEX = (
			r"(https?://)?"
			+ r"(www\.)?thesession.org"
			+ load_from_session.PATH_REGEX.pattern
			+ rf"(#{load_from_session.FRAGMENT_REGEX.pattern})?"
		)

		uriValidator = QRegExpValidator(QRegExp(VALID_REGEX), self)
		uriField.setValidator(uriValidator)
		uriField.textChanged.connect(self.onTextChanged)  # type: ignore
		self.onTextChanged()  # type: ignore # mypy shows the stype of a slot as a str, not a callable

		self.setLoading(False)

	@pyqtSlot()
	def onTextChanged(self) -> None:
		self._update()
		self._maybeEmitURI()

	@pyqtSlot()
	def onTextFinishedEditing(self) -> None:
		self._maybeEmitURI()

	def _maybeEmitURI(self) -> None:
		if not self.uriField.hasAcceptableInput():
			return

		currentText = self.uriField.text()

		if currentText == self._lastURIEmit:
			return

		self.gotTuneURI.emit(currentText)

	def _update(self) -> None:
		if self.uriField.hasAcceptableInput() or self.uriField.text() == "":
			self.uriField.setStyleSheet("")
		else:
			self.uriField.setStyleSheet("background-color: #ffbbaa")

		if self._loadingReset:
			self.uriSpinner._currentCounter = 0
			self._loadingReset = False

		if self._loading:
			self.uriSpinner.start()
		else:
			self.uriSpinner.stop()

	def setLoading(self, loading: bool) -> None:
		self._loading = loading
		if loading:
			self._loadingReset = True
		self._update()


class MyAddCards(AddCards):
	uriContainer: Optional[URIContainer] = None
	tuneGrabber: "TuneGrabber"

	def __init__(self, mw: AnkiQt) -> None:
		super().__init__(mw)

		modelAndDeckIndex = self.form.verticalLayout.indexOf(self.form.horizontalLayout)

		uriContainer = URIContainer(self)

		self.form.verticalLayout.insertWidget(modelAndDeckIndex + 1, uriContainer)

		self.uriContainer = uriContainer

		self.tuneGrabber = TuneGrabber(self.mw, self)
		self.uriContainer.gotTuneURI.connect(self.onNewTuneInput)  # type: ignore
		self.tuneGrabber.done.connect(self.onNewTuneLoaded)  # type: ignore

		# this gets called in super() but we need to call it again to hide/show the uricontainer.
		self.on_notetype_change(self.notetype_chooser.selected_notetype_id)

	def on_notetype_change(self, notetype_id: NotetypeId) -> None:
		super().on_notetype_change(notetype_id)

		if self.uriContainer is None:
			return
		if self.editor.note is None:
			return

		nt = self.editor.note.note_type()

		if nt is not None and col_note_type.is_ankitunes_nt(nt):
			self.uriContainer.show()
		else:
			self.uriContainer.hide()

	@pyqtSlot(str)
	def onNewTuneInput(self, uri: str) -> None:
		if self.uriContainer is None:
			return
		print("onNewTuneInput")
		self.uriContainer.setLoading(True)
		self.tuneGrabber.grab(uri)

	@pyqtSlot(object)
	def onNewTuneLoaded(self, result: GrabResult) -> None:
		print("onNewTuneLoaded")
		if self.uriContainer is None:
			return
		self.uriContainer.setLoading(False)
		if isinstance(result, Err):
			# TODO:
			print("error!")
			print(result.err_value)

		# I slightly mistrust the amount of time thing thing spends as an untyped object
		elif isinstance(result, Ok):
			print("got tune!")
			tune = result.value

			note = self.editor.note
			assert note is not None, "Got a tune, but editor.note was None"
			nt = note.note_type()
			if nt is None or not col_note_type.is_ankitunes_nt(nt):
				print("Got a tune, but the Editor's note wasn't of the Ankitunes note type")
				return

			# protect us from ourselves - we need to update this if note schema changes
			fieldsToWrite: NoteFields = {
				"Name": tune.name,
				"Key": tune.key,
				"Tune Type": tune.type,
				"ABC": tune.abc.replace("\n", "<br />\n"),
				"Link": tune.uri,
			}

			for field, value in fieldsToWrite.items():
				assert isinstance(value, str)
				note[field] = value

			self.editor.loadNote()


class TuneGrabber(QObject):
	_thread: Optional[QThread]
	_grabber: Optional["TuneGrabRunnable"]
	_grabConnection: Optional[QMetaObject.Connection]
	_mw: AnkiQt

	done = pyqtSignal(object, name="done")

	def __init__(self, mw: AnkiQt, parent: QObject) -> None:
		super().__init__(parent)

		self._thread = None
		self._mw = mw

	def grab(self, uri: str) -> None:
		print("tg.grab")
		if self._thread is not None:
			print("abandoning old grab thread!")
			self._clearThread()

		self._thread = QThread(self._mw)
		self._grabber = TuneGrabRunnable(uri)
		self._grabber.moveToThread(self._thread)
		self._thread.started.connect(self._grabber.run)  # type: ignore
		self._thread.finished.connect(self._thread.deleteLater)  # type: ignore
		self._thread.finished.connect(self._grabber.deleteLater)  # type: ignore
		self._grabConnection = self._grabber.done.connect(self._grabDone)  # type: ignore
		self._grabber.done.connect(self._thread.exit)

		self._thread.start()

	def _clearThread(self) -> None:
		if self._grabber is not None and self._grabConnection is not None:
			self._grabber.disconnect(self._grabConnection)  # type: ignore
		self._thread = None
		self._grabber = None
		self._grabConnection = None

	@pyqtSlot(object)
	def _grabDone(self, result: GrabResult) -> None:
		self._clearThread()

		self.done.emit(result)


class TuneGrabRunnable(QObject):
	uri: str
	done = pyqtSignal(object, name="done")

	def __init__(self, uri: str) -> None:
		super().__init__()
		self.uri = uri

	@pyqtSlot()
	def run(self) -> None:
		print("running")
		result = load_from_session.get_from_thesession(self.uri)
		print("loaded!")
		self.done.emit(result)


def on_main_window_did_init() -> None:
	aqt.dialogs.register_dialog("AddCards", MyAddCards)


def setup() -> None:
	aqt.gui_hooks.main_window_did_init.append(on_main_window_did_init)
