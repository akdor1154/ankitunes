import anki
from aqt.addons import AddonManager
from anki.models import ModelManager, NoteType, Template as AnkiTemplate
from .util import mw
from string import Template as pyTemplate
from textwrap import dedent
from typing import *
import sys

TEMPLATE_NAME = 'Tune'
TPL_VER_KEY = 'ankitunes_tpl'

question = '''
<h1>{{Name}}</h1>

<h2>{{Tune Type}}</h2>
'''


def answer(addon_package: str) -> str:
	return pyTemplate(
			dedent(
					'''
		{{FrontSide}}

		<hr id=answer>

		{{Link}}

		{{#ABC}}

		<pre id="__ABC_ID__" class="abcSource">
		{{ABC}}
		</pre>

		<div class="renderedAbc __ABC_ID__"></div>

		<script defer src="/_addons/${addon_package}/web/dist/card_template/template.js"></script>

		{{/ABC}}
	'''
			)
	).substitute(addon_package=addon_package)


class TemplateMigrator:
	mn: ModelManager

	def __init__(self, mn: ModelManager) -> None:
		self.mn = mn

	def build_template(self) -> AnkiTemplate:

		addon_package = AddonManager.addonFromModule(
				cast(AddonManager, None), __name__
		)

		t = self.mn.new_template(TEMPLATE_NAME)
		t['qfmt'] = question
		t['afmt'] = answer(addon_package)
		t['other'] = {TPL_VER_KEY: True}  # type: ignore
		return t
