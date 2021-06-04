# https://github.com/krassowski/anki_testing/blob/master/anki_testing.py

# coding: utf-8
import shutil
import tempfile
from contextlib import contextmanager
from typing import *

import os
import os.path

import sys
from warnings import warn

import aqt
from aqt import _run
from aqt import AnkiApp
from aqt.profiles import ProfileManager


@contextmanager
def temporary_user(dir_name, name="__Temporary Test User__", lang="en_US") -> Generator[str, None, None]:

	# prevent popping up language selection dialog
	original = ProfileManager.setDefaultLang

	def set_default_lang(self: ProfileManager, idx: int) -> None:
		self.setLang(lang)

	ProfileManager.setDefaultLang = set_default_lang

	pm = ProfileManager(base=dir_name)

	pm.setupMeta()

	# create profile no matter what (since we are starting in a unique temp directory)
	pm.create(name)

	# this needs to be called explicitly
	pm.setDefaultLang(0)

	pm.name = name

	try:
		yield name
	finally:
		# cleanup
		pm.remove(name)
		ProfileManager.setDefaultLang = original


@contextmanager
def temporary_dir() -> Generator[str, None, None]:
	# create a true unique temporary directory at every startup
	with tempfile.TemporaryDirectory(suffix='anki') as tempdir:
		yield tempdir


def _install_ankitunes(profile_dir: str) -> None:

	ankitunes_dir = os.path.join(os.getcwd(), 'ankitunes')
	assert os.path.exists(ankitunes_dir)

	addons_dir = os.path.join(profile_dir, 'addons21')
	os.makedirs(addons_dir, exist_ok=True)

	ankitunes_addon_dir = os.path.join(addons_dir, 'ankitunes')
	assert not os.path.exists(ankitunes_addon_dir)

	os.symlink(src=ankitunes_dir, dst=ankitunes_addon_dir)

@contextmanager
def anki_running(install_ankitunes: bool = True) -> Generator[AnkiApp, None, None]:

	# don't use the second instance mechanism, start a new instance every time
	def mock_secondInstance(self: AnkiApp):
		return False

	AnkiApp.secondInstance = mock_secondInstance

	# we need a new user for the test
	with temporary_dir() as dir_name:
		if install_ankitunes:
			_install_ankitunes(dir_name)
		with temporary_user(dir_name) as user_name:
			argv=["anki", "-p", user_name, "-b", dir_name]
			print(f'running anki with argv={argv}')
			app = _run(argv=argv, exec=False)
			assert app is not None
			try:
				yield app
			finally:
				# clean up what was spoiled
				aqt.mw.cleanupAndExit()

	# remove hooks added during app initialization
	from anki import hooks
	hooks._hooks = {}

	# test_nextIvl will fail on some systems if the locales are not restored
	import locale
	locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

