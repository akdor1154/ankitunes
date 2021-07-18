from typing import *
from textwrap import dedent
from ankitunes.col_note_type import NoteFields_v1

cooleys_v1: NoteFields_v1 = {
	"Name": "Cooleys",
	"Tune Type": "em reel",
	"ABC": dedent(
		"""
		X: 1
		T: Cooley's
		R: reel
		M: 4/4
		L: 1/8
		K: Edor
		|:D2|EBBA B2 EB|B2 AB dBAG|FDAD BDAD|FDAD dAFD|
		EBBA B2 EB|B2 AB defg|afec dBAF|DEFD E2:|
		|:gf|eB B2 efge|eB B2 gedB|A2 FA DAFA|A2 FA defg|
		eB B2 eBgB|eB B2 defg|afec dBAF|DEFD E2:|
	"""
	),
	"Link": "https://thesession.org/tunes/1#setting1",
}


cup_of_tea_v1: NoteFields_v1 = {
	"Name": "The Cup of Tea",
	"Tune Type": "Edor reel",
	"ABC": dedent(
		"""
		X: 1
		T: The Cup Of Tea
		R: reel
		M: 4/4
		L: 1/8
		K: Edor
		|:BAGF GEEF|GEBE GEEA|BAGF GEEG|FDAD FDDA|
		BAGF GEEF|GEBE GEEA|B2 BA GABc|dBAG FD D2:|
		K:D
		|:d2 eg fdec|d2 eg fB B2|d2 eg fdec|dBAG FD D2|
		d2 eg fdec|dfaf g2 fg|afge fdec|dBAG FD D2:|
		|:FAdA FABA|FAdA FEE2|FAdA FABc|dBAG FD D2|
		FAdA FABA|FAde fee2|fdec dBAF|GBAG FD D2:|
	"""
	),
	"Link": "https://thesession.org/tunes/20#setting20",
}
