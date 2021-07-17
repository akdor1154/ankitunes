from pytestqt.qtbot import QtBot
from contextlib import contextmanager
from typing import *

from pytestqt.wait_signal import CallbackBlocker

H = TypeVar("H")


class AnkiHook(Protocol[H]):
	_hooks: List[H]

	def append(self, hook: H) -> Any:
		...

	def remove(self, hook: H) -> Any:
		...


import functools


@contextmanager
def wait_hook(
	qtbot: QtBot, hook: AnkiHook[Any], **kwargs: Any
) -> Generator[CallbackBlocker, None, None]:
	try:
		with qtbot.waitCallback(**kwargs) as cb:

			def wrappedCB(*args, **kwargs):
				hook.remove(wrappedCB)
				return cb(*args, **kwargs)

			hook.append(wrappedCB)

			yield cb
	finally:
		hook.remove(wrappedCB)
