import json
from typing import *

import aqt

import aqt.gui_hooks
import aqt.overview

from . import tuneReviewer
from .util import mw

class TuneOverview:
	#static
	instance: Optional['TuneOverview'] = None

	#member
	overview: aqt.overview.Overview

	def __init__(self, overview: aqt.overview.Overview) -> None:
		self.overview = overview

	@staticmethod
	def ensure_exists(overview: aqt.overview.Overview) -> 'TuneOverview':
		if TuneOverview.instance is None:
			TuneOverview.instance = TuneOverview(overview)
		return TuneOverview.instance

	def _linkHandler(self, url: str) -> bool:
		if url == "study_sets":
			# TODO enable set mode
			return self.overview._linkHandler("study")
		else:
			return self.overview._linkHandler(url)

	def overview_did_refresh(self) -> None:
		reviewSetsButton = mw().button(
			"study_sets",
			"Practice Sets",
			id="study_sets"
		)
		self.overview.web.eval(f'''
			const studyButton = document.getElementById('study');
			const parent = studyButton.parentNode;
			parent.innerHTML += {json.dumps(reviewSetsButton)};
		''')
		return

	@staticmethod
	def static_overview_did_refresh(overview: aqt.overview.Overview) -> None:
		return TuneOverview.ensure_exists(overview).overview_did_refresh()

	def webview_did_receive_js_message(self, handled: Tuple[bool, Any], message: str) -> Tuple[bool, Any]:
		# Private API call to _linkHandler is currently required.
		# if Anki ever change to have
		#   overview.study()
		# or even better
		#  (this handler can modify the cmd that gets processed)
		# then _linkHandler() call can be removed.
		if message == 'study_sets':
			tuneReviewer.is_reviewing_tunes = True
			self.overview._linkHandler('study')
			return (True, None)
		elif message == 'study':
			tuneReviewer.is_reviewing_tunes = False
			self.overview._linkHandler('study')
			return (True, None)

		return handled

	@staticmethod
	def static_webview_did_receive_js_message(handled: Tuple[bool, Any], message: str, context: Any) -> Tuple[bool, Any]:
		if not isinstance(context, aqt.overview.Overview):
			return handled

		return TuneOverview.ensure_exists(context).webview_did_receive_js_message(handled, message)


aqt.gui_hooks.overview_did_refresh.append(TuneOverview.static_overview_did_refresh)

aqt.gui_hooks.webview_did_receive_js_message.append(TuneOverview.static_webview_did_receive_js_message)

