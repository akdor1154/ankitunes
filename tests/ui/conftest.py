# https://github.com/krassowski/anki_testing/blob/master/anki_testing.py

# coding: utf-8
from posix import environ
import shutil
import tempfile
from contextlib import contextmanager
from typing import *

import os
import os.path

import sys
from warnings import warn

import pytest
from  pytestqt.qtbot import QtBot

import aqt
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
	import importlib
	ankitunesSpec = importlib.util.find_spec('ankitunes')

	ankitunes_dir = os.path.dirname(ankitunesSpec.origin)

	assert os.path.exists(ankitunes_dir)

	addons_dir = os.path.join(profile_dir, 'addons21')
	os.makedirs(addons_dir, exist_ok=True)

	ankitunes_addon_dir = os.path.join(addons_dir, 'ankitunes')
	assert not os.path.exists(ankitunes_addon_dir)

	os.symlink(src=ankitunes_dir, dst=ankitunes_addon_dir)

from typing import NamedTuple

@pytest.fixture(scope='session')
def fix_qt(*args, **kwargs) -> None:
	if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
		print('overridding wayland session to run tests under xvfb')
		os.environ['QT_QPA_PLATFORM'] = 'xcb'
	return

@pytest.fixture(scope='session')
def qapp(fix_qt, qapp):
	yield qapp

def clean_hooks() -> None:
	if 'anki.hooks' in sys.modules:
		import anki.hooks
		for name, maybeHook in vars(anki.hooks).items():
			if hasattr(maybeHook, '_hooks'):
				maybeHook._hooks = []
	if 'aqt.gui_hooks' in sys.modules:
		import aqt.gui_hooks
		for name, maybeHook in vars(aqt.gui_hooks).items():
			if hasattr(maybeHook, '_hooks'):
				maybeHook._hooks = []

	# delete ankitunes module - we need to re-import it to
	# reload all its hooks if necessary.
	if 'ankitunes' in sys.modules:
		del sys.modules['ankitunes']

@contextmanager
def with_wm():
	import subprocess
	import signal
	wm = subprocess.Popen(['openbox'], encoding='utf-8')
	yield
	wm.send_signal(signal.SIGTERM)
	wm.wait()
	if wm.returncode != 0:
		raise subprocess.CalledProcessError(wm.returncode, wm.args)

def screenshot():
	import subprocess

	subprocess.run(
		'scrot',
		shell=True,
		check=True
	)


@pytest.fixture
def anki_running(qtbot: QtBot, install_ankitunes: bool = True) -> Generator[aqt.AnkiApp, None, None]:

	clean_hooks()

	import aqt
	from aqt import _run
	from aqt import AnkiApp

	# don't use the second instance mechanism, start a new instance every time
	def mock_secondInstance(self: AnkiApp) -> bool:
		return False

	AnkiApp.secondInstance = mock_secondInstance

	import os

	# we need a new user for the test
	with with_wm():
		with temporary_dir() as dir_name:
			if install_ankitunes:
				_install_ankitunes(dir_name)
			with temporary_user(dir_name) as user_name:
				argv=["anki", "-p", user_name, "-b", dir_name]
				print(f'running anki with argv={argv}')
				app = _run(argv=argv, exec=False)
				assert app is not None
				try:
					qtbot.addWidget(aqt.mw)
					yield app
				finally:
					# clean up what was spoiled
					app.closeAllWindows()


	# remove hooks added during app initialization
	from anki import hooks
	hooks._hooks = {}

	# test_nextIvl will fail on some systems if the locales are not restored
	import locale
	locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

import argparse

def pytest_runtest_setup(item):
	fiddle_marks = list(item.iter_markers(name='fiddle'))
	is_fiddle = (len(fiddle_marks) > 0)
	if item.config.getoption('--fiddle'):
		if not is_fiddle:
			pytest.skip('Fiddles only')
	else:
		if is_fiddle:
			pytest.skip('Disabling fiddles')