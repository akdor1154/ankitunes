from pytestqt.qtbot import QtBot
from contextlib import contextmanager
from typing import *

H = TypeVar('H')


class AnkiHook(Protocol[H]):
	_hooks: List[H]

	def append(self, hook: H) -> Any:
		...

	def remove(self, hook: H) -> Any:
		...


@contextmanager
def wait_hook(qtbot: QtBot, hook: AnkiHook[Any]) -> Generator[None, None, None]:
	with qtbot.wait_callback() as cb:
		hook.append(cb)
		yield
	hook.remove(cb)
