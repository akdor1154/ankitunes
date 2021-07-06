import os
import shutil
import tempfile
import time

import atexit
import pytest

from typing import *

import anki.collection

os.environ["ANKITUNES_TESTING"] = "1"  # warnings are now exceptions

_masterFilePath: Optional[str] = None


def _getMasterFilePath() -> str:
	global _masterFilePath
	if _masterFilePath is None:
		with tempfile.NamedTemporaryFile(suffix=".anki2", delete=True) as tf:
			pass
		_masterFilePath = tf.name

		tempCollection = anki.collection.Collection(_masterFilePath)
		tempCollection.close(downgrade=False)

		def cleanup() -> None:
			if _masterFilePath is None:
				raise Exception("cleaned up empty _masterFilePath")
			os.unlink(_masterFilePath)

		atexit.register(cleanup)

	return _masterFilePath


# Creating new decks is expensive. Just do it once, and then spin off
# copies from the master.
@pytest.fixture
def empty_collection() -> Generator[anki.collection.Collection, None, None]:
	with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as tf:
		shutil.copy(_getMasterFilePath(), tf.name)
	col = anki.collection.Collection(tf.name)
	yield col
	col.close(downgrade=False)
	os.unlink(col.path)


import _pytest.config.argparsing


def pytest_addoption(parser: _pytest.config.argparsing.Parser) -> None:
	parser.addoption("--fiddle", action="store_true")

	parser.addoption("--ankiaddon", action="store")
