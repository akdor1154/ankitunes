try:
	import aqt
	assert aqt.mw is not None

	from . import tune_overview
	from . import tune_reviewer
except (ImportError, AssertionError):
	pass