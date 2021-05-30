import anki
from anki.models import ModelManager, NoteType, Template as AnkiTemplate
from .util import mw
from string import Template as pyTemplate
from textwrap import dedent
from typing import *
import sys

TEMPLATE_NAME = 'Tune'
TPL_VER_KEY = 'ankitunes_nt_version'

question = '''
<h1>{{Name}}</h1>

<h2>{{Tune Type}}</h2>
'''

def answer(addon_package: str) -> str:
	return pyTemplate(dedent('''
		{{FrontSide}}

		<hr id=answer>

		{{Link}}

		{{#ABC}}

		<pre id="abcSource">
		{{ABC}}
		</pre>

		<div id="renderedAbc"></div>

		<script defer src="/_addons/${addon_package}/web/dist/card_template/template.js" />

		{{/ABC}}
	''')).substitute(addon_package=addon_package)

class TemplateMigrator:
	mn: ModelManager

	def __init__(self, mn: ModelManager) -> None:
		self.mn = mn

	def build_template(self) -> AnkiTemplate:
		# TODO: fix.
		# Breaks in unit test because mw() is unavailable
		if 'pytest' in sys.modules:
			addon_package = 'BOO'
		else:
			addon_package = mw().addonManager.addonFromModule(__name__)
		t = self.mn.new_template(TEMPLATE_NAME)
		t['qfmt'] = question
		t['afmt'] = answer(addon_package)
		t['other'] = {
			TPL_VER_KEY: True
		}
		return t
