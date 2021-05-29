import aqt

def mw() -> aqt.AnkiQt:
	if not aqt.mw:
		raise Exception('Main Window doesn\'t exist!')
	return aqt.mw