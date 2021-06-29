

import aqt
import aqt.gui_hooks
from aqt.qt import debug
import aqt.webview
from anki.cards import Card
from anki.collection import BuiltinSort, SearchNode, Collection as AnkiCollection

import aqt.reviewer
import anki.collection
import anki.sched
import anki.schedv2

import random
import json
from typing import *

from .util import mw
from .col_note_type import is_ankitunes_nt

HTML = NewType('HTML', str)
Scheduler = Union[anki.sched.Scheduler, anki.schedv2.Scheduler]

class FocusCardProtocol(Protocol):
	_ankitunes_set: Sequence[Card]

# https://github.com/python/typing/issues/213
class FocusCard(Card, FocusCardProtocol):
	pass

## Magic Global State
is_reviewing_tunes = False


## Webview Hooks

def set_up_reviewer_bottom(web_content: aqt.webview.WebContent, context: Any) -> None:
	if not isinstance(context, aqt.reviewer.ReviewerBottomBar):
		return

	addon_package = mw().addonManager.addonFromModule(__name__)
	web_content.js.append(f'/_addons/{addon_package}/web/dist/reviewer_bottom/reviewer_bottom.js')
	return

## Question

def turn_card_into_set(focus_card: FocusCard, col: anki.collection.Collection) -> Sequence[Card]:

	focus_note = focus_card.note()

	# get extra cards from scheduler
	tune_type_val = focus_note['Tune Type']
	key, tune_type = tune_type_val.split(' ', 1)

	# readability
	def join(a: Union[str, SearchNode], op: anki.collection.SearchJoiner, b: Union[str, SearchNode]) -> SearchNode:
		return col.group_searches(a, b, joiner=op)

	SET_NUM_TUNES = 3

	deck = col.decks.get(focus_card.did)
	if deck is None:
		# TODO
		raise Exception('No deck!')

	deck_name = deck['name']

	search = (
		col.group_searches(
			join(
				f'"Tune Type:* {tune_type}"',
				'OR',
				f'"Tune Type:{tune_type}"',
			),
			SearchNode(negated=SearchNode(nid=focus_card.nid)),
			SearchNode(deck=deck_name),
			joiner='AND'
		)
	)
	search_str = col.build_search_string(search)
	print(f'searching for {search_str}')

	search_limit = SET_NUM_TUNES - 1

	other_ids = col.find_cards(
		search_str,
		order=f'RANDOM() limit {search_limit}'
	)
	print(f'found {other_ids=}')
	others = (col.getCard(card_id) for card_id in other_ids)

	# add with focus card and turn into a shuffled set
	set_cards = [focus_card, *others]
	random.shuffle(set_cards)

	# attach set to focus card
	focus_card._ankitunes_set = set_cards

	# return set
	return set_cards

def format_set_question(cards: Sequence[Card]) -> HTML:
	return HTML(
		'\n'.join(card.q() for card in cards)
	)

def on_card_will_show_qn(q: str, card: Card, show_type: str, /, col: Optional[AnkiCollection] = None) -> HTML:
	if not is_reviewing_tunes:
		return HTML(q)
	if show_type != 'reviewQuestion':
		return HTML(q)
	if not is_ankitunes_nt(card.model()):
		return HTML(q)

	# for testing..
	col = col or mw().col

	cards = turn_card_into_set(cast(FocusCard, card), col)
	newQ = format_set_question(cards)

	return newQ


## Answer

alpha = 'abcdefghijklmnopqrstuvwxyz'
def random_str(len: int=8) -> str:
	import random
	return ''.join(random.choices(alpha, k=len))

def get_set_from_base_card(focus_card: FocusCard) -> Sequence[Card]:
	return focus_card._ankitunes_set

def format_set_answers(cards: Sequence[Card]) -> HTML:
	answerHtml = (card.answer() for card in cards)
	replacedAnswerHtml = (
		html.replace('__ABC_ID__', random_str())
		for html in answerHtml
	)
	return HTML(
		'\n'.join(replacedAnswerHtml)
	)

def update_answer_buttons(focus_card: Card) -> None:
	note = focus_card.note()
	Name = 'Name'
	if Name not in note:
		# TODO
		raise Exception(f'`{Name}` field missing!')

	name = note[Name]
	html = f'<p>How hard was {name}?</p>'
	mw().reviewer.bottom.web.eval(f'ankitunes_add_answer_context({json.dumps(html)})')
	mw().reviewer.bottom.web.adjustHeightToFit()


def on_card_will_show_ans(ans: str, focus_card: Card, show_type: str) -> HTML:
	if not is_reviewing_tunes:
		return HTML(ans)

	if show_type != 'reviewAnswer':
		return HTML(ans)

	cards = get_set_from_base_card(cast(FocusCard, focus_card))
	newAns = format_set_answers(cards)

	return newAns

def on_reviewer_did_show_ans(focus_card: Card) -> None:
	update_answer_buttons(focus_card)

def on_main_window_did_init() -> None:
	mw().addonManager.setWebExports(__name__, r"web/dist/.*")


def setup() -> None:
	aqt.gui_hooks.webview_will_set_content.append(set_up_reviewer_bottom)

	aqt.gui_hooks.card_will_show.append(on_card_will_show_qn)

	aqt.gui_hooks.card_will_show.append(on_card_will_show_ans)

	aqt.gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_ans)

	aqt.gui_hooks.main_window_did_init.append(on_main_window_did_init)
