import anki
from anki.models import ModelManager, NoteType

TEMPLATE_NAME = 'Tune'
TPL_VER_KEY = 'ankitunes_nt_version'

answer = '''
{{FrontSide}}

<hr id=answer>

{{Tune}}
{{Link}}

{{#abc}}

<pre id="abcSource">
{{abc}}
</pre>

<div id="renderedAbc"></div>

{{/abc}}
'''

class TemplateMigrator:
	mn: ModelManager
	def __init__(self, mn: ModelManager) -> None:
		self.mn = mn

	def build_template(self) -> None:
		t = self.mn.new_template(TEMPLATE_NAME)
		t['']

	def migrate_template(self, nt: NoteType) -> None:
		'''Updates the template in nt to be our Tune renderer. nt is assumed to be our Tune.'''

		# Search templates for any managed by us.
		existing_templates = [
			(i, t) for i, t in enumerate(nt['tmpls'])
			if t.get('other', {})[TPL_VER_KEY] == 'ankitunes_nt_version'
		]

		if len(existing_templates) > 1:
			raise Exception('Multiple Ankitunes-managed templates detected. Aborting.')

		our_template = self.build_template()

		# if existing template, update it
		if len(existing_templates) == 1:
			i, old_t = existing_templates[0]
			nt['tmpls'][i] = our_template

		# else append
		self.mn.add_template(nt, our_template)

		self.mn.save(nt)