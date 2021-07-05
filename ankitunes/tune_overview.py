import json
from typing import *

import aqt

import aqt.gui_hooks
import aqt.overview
import aqt.webview

from . import tune_reviewer
from .util import mw


class TuneOverview:
	#member
	overview: aqt.overview.Overview

	def __init__(self, overview: aqt.overview.Overview) -> None:
		self.overview = overview

	def overview_did_set_content(
			self, web_content: aqt.webview.WebContent
	) -> None:
		reviewSetsButton = mw().button(
				"study_sets", "Practice Sets", id="study_sets"
		)
		# if this grows beyond more than 3 lines then turn it into TS and inject into a handler
		# with the webview_set_content hook
		web_content.body += f'''
			<script type="text/javascript">
				const studyButton = document.getElementById('study');
				const parent = studyButton.parentNode;
				parent.innerHTML += {json.dumps(reviewSetsButton)};
			</script>
		'''

	@staticmethod
	def static_overview_did_set_content(
			content: aqt.webview.WebContent, context: Any
	) -> None:
		if not isinstance(context, aqt.overview.Overview):
			return
		return TuneOverview(context).overview_did_set_content(content)

	def webview_did_receive_js_message(
			self, handled: Tuple[bool, Any], message: str
	) -> Tuple[bool, Any]:
		# Private API call to _linkHandler is currently required.
		# if Anki ever change to have
		#   overview.study()
		# or even better
		#  (this handler can modify the cmd that gets processed)
		# then _linkHandler() call can be removed.
		if message == 'study_sets':
			tune_reviewer.is_reviewing_tunes = True
			self.overview._linkHandler('study')
			return (True, None)
		elif message == 'study':
			tune_reviewer.is_reviewing_tunes = False
			self.overview._linkHandler('study')
			return (True, None)

		return handled

	@staticmethod
	def static_webview_did_receive_js_message(
			handled: Tuple[bool, Any], message: str, context: Any
	) -> Tuple[bool, Any]:
		if not isinstance(context, aqt.overview.Overview):
			return handled

		return TuneOverview(context
												).webview_did_receive_js_message(handled, message)


def setup() -> None:
	aqt.gui_hooks.webview_will_set_content.append(
			TuneOverview.static_overview_did_set_content
	)

	aqt.gui_hooks.webview_did_receive_js_message.append(
			TuneOverview.static_webview_did_receive_js_message
	)
