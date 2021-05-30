try:
	import aqt
	assert aqt.mw is not None

	from . import tune_overview
	from . import tune_reviewer
	from . import col_note_type

except (ImportError, AssertionError):
	pass