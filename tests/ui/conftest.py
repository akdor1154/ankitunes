# https://github.com/krassowski/anki_testing/blob/master/anki_testing.py

import tempfile
from contextlib import contextmanager
from typing import *
import os
import os.path
import sys

import pytest
from _pytest.config import apply_warning_filters, Config as PytestConfig

import pytestqt.qtbot
import pytestqt.exceptions
from pytestqt.qtbot import QtBot

import anki
import anki.collection
import aqt
import aqt.addons
from aqt.profiles import ProfileManager
from aqt.main import AnkiQt

from . import wait_hook


@contextmanager
def temporary_user(
	dir_name: str, name: str = "__Temporary Test User__", lang: str = "en_US"
) -> Generator[Tuple[ProfileManager, str], None, None]:

	# prevent popping up language selection dialog
	original = ProfileManager.setDefaultLang

	def set_default_lang(self: ProfileManager, idx: int) -> None:
		self.setLang(lang)

	ProfileManager.setDefaultLang = set_default_lang  # type: ignore

	pm = ProfileManager(base=dir_name)

	pm.setupMeta()

	# create profile no matter what (since we are starting in a unique temp directory)
	pm.create(name)

	# this needs to be called explicitly
	pm.setDefaultLang(0)

	pm.name = name

	try:
		yield pm, name
	finally:
		# cleanup
		pm.remove(name)
		ProfileManager.setDefaultLang = original  # type: ignore


@contextmanager
def temporary_dir() -> Generator[str, None, None]:
	# create a true unique temporary directory at every startup
	with tempfile.TemporaryDirectory(suffix="anki") as tempdir:
		yield tempdir


@pytest.fixture(scope="session")
def ankiaddon_cmd(request: pytest.FixtureRequest) -> Any:
	return request.config.getoption("--ankiaddon")


def _install_ankitunes_direct(profile_dir: str) -> None:
	import importlib

	ankitunesSpec = importlib.util.find_spec("ankitunes")
	assert ankitunesSpec is not None
	assert ankitunesSpec.origin is not None

	ankitunes_dir = os.path.dirname(ankitunesSpec.origin)

	assert os.path.exists(ankitunes_dir)

	addons_dir = os.path.join(profile_dir, "addons21")
	os.makedirs(addons_dir, exist_ok=True)

	ankitunes_addon_dir = os.path.join(addons_dir, "ankitunes")
	assert not os.path.exists(ankitunes_addon_dir)

	os.symlink(src=ankitunes_dir, dst=ankitunes_addon_dir)


def _install_ankitunes(
	argv: List[str], profile_dir: str, ankiaddon_path: Optional[str]
) -> List[str]:
	d = os.path.dirname(__file__)
	while not os.path.exists(os.path.join(d, "pyproject.toml")):
		oldD = d
		d = os.path.dirname(d)
		if d == oldD:
			raise Exception("couldn't find project root")

	if ankiaddon_path is not None:

		def installAddon(self: AnkiQt, path: str, startup: bool = False) -> None:
			print("boo")
			from aqt.addons import installAddonPackages

			installAddonPackages(
				self.addonManager,
				[path],
				warn=False,  # True,
				advise_restart=not startup,
				strictly_modal=False,  # startup,
				parent=None if startup else self,
			)

		AnkiQt.installAddon = installAddon  # type: ignore

		return argv + [ankiaddon_path]
	else:
		_install_ankitunes_direct(profile_dir)
		return argv


from typing import NamedTuple


@pytest.fixture(scope="session")
def fix_qt() -> Generator[None, None, None]:
	if "xvfb" not in os.environ.get("XAUTHORITY", ""):
		yield
		return

	if os.environ.get("XDG_SESSION_TYPE") == "wayland":
		print("overridding wayland session to run tests under xvfb")
		os.environ["QT_QPA_PLATFORM"] = "xcb"

	with with_wm():
		yield


def clean_hooks() -> None:
	if "anki.hooks" in sys.modules:
		import anki.hooks

		for name, maybeHook in vars(anki.hooks).items():
			if hasattr(maybeHook, "_hooks"):
				maybeHook._hooks = []
	if "aqt.gui_hooks" in sys.modules:
		import aqt.gui_hooks

		for name, maybeHook in vars(aqt.gui_hooks).items():
			if hasattr(maybeHook, "_hooks"):
				maybeHook._hooks = []

	# empty = set()
	# for mod in list(sys.modules)[::-1]:
	# 	if {"aqt", "anki", "ankitunes"}.intersection(mod.split(".")) != empty:
	# 		print(f"deleting {mod}")
	# 		del sys.modules[mod]
	# 	else:
	# 		print(f"left {mod}")

	# delete ankitunes module - we need to re-import it to
	# reload all its hooks if necessary.
	if "ankitunes" in sys.modules:
		del sys.modules["ankitunes"]


@contextmanager
def with_wm() -> Generator[None, None, None]:
	import subprocess
	import signal

	wm = subprocess.Popen(["openbox"], encoding="utf-8")
	yield
	wm.send_signal(signal.SIGTERM)
	wm.wait()
	if wm.returncode != 0:
		raise subprocess.CalledProcessError(wm.returncode, wm.args)


def screenshot(mw: AnkiQt) -> None:
	# import subprocess

	os.makedirs("screenshots", exist_ok=True)
	import datetime
	import itertools

	file = os.path.join("screenshots", f"{datetime.datetime.now()}.png")

	screenshot = mw.screen().grabWindow(mw.winId())
	img = screenshot.toImage()
	img.save(file, "png")


# anki segfaults if it gets run for a second time in the same py execution.
# This would otherwise be a normal per-test fixture.
@pytest.fixture(scope="session")
def qapp(fix_qt) -> Generator[aqt.AnkiApp, None, None]:

	from aqt import AnkiApp

	# don't use the second instance mechanism, start a new instance every time
	def mock_secondInstance(self: AnkiApp) -> bool:
		return False

	AnkiApp.secondInstance = mock_secondInstance  # type: ignore

	app = AnkiApp(argv=["anki", "-p", "DUMMY", "-b", "DUMMY"])

	yield app

	# test_nextIvl will fail on some systems if the locales are not restored
	import locale

	locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())  # type: ignore


@pytest.fixture()
def anki_running(
	qtbot: QtBot,
	qapp: aqt.AnkiApp,
	ankiaddon_cmd: Optional[str],
	install_ankitunes: bool = True,
):

	import aqt
	from aqt import _run
	import aqt.main

	assert aqt.mw is None

	clean_hooks()

	# we need a new user for the test
	with temporary_dir() as dir_name:
		with temporary_user(dir_name) as (pm, user_name):

			argv = ["anki", "-p", user_name, "-b", dir_name]
			argv = _install_ankitunes(argv, dir_name, ankiaddon_cmd)

			print(f"running anki with argv={argv}")

			# lifted from aqt _run
			opts, args = aqt.parseArgs(argv)
			backend = aqt.setupLangAndBackend(pm, qapp, opts.lang, True)

			# i18n & backend

			aqt.mw = aqt.main.AnkiQt(qapp, pm, backend, opts, args)

			with wait_hook(qtbot, aqt.gui_hooks.main_window_did_init):
				pass

			try:
				aqt.mw.show()

				def cleanup(mw: aqt.main.AnkiQt) -> None:
					try:
						with qtbot.wait_callback(timeout=100) as cb:
							mw.closeAllWindows(cb)
					except pytestqt.exceptions.TimeoutError:
						pass
					mw.errorHandler.unload()
					mw.mediaServer.shutdown()

				qtbot.addWidget(aqt.mw, before_close_func=cleanup)

				yield

			finally:
				screenshot(aqt.mw)

	aqt.mw = None

	# remove hooks added during app initialization
	clean_hooks()


def pytest_runtest_setup(item: pytest.Item) -> None:
	fiddle_marks = list(item.iter_markers(name="fiddle"))
	is_fiddle = len(fiddle_marks) > 0
	if item.config.getoption("--fiddle"):
		if not is_fiddle:
			pytest.skip("Fiddles only")
	else:
		if is_fiddle:
			pytest.skip("Disabling fiddles")


def pytest_configure(config: PytestConfig) -> None:
	config.addinivalue_line(
		"markers", 'fiddle: marker for "tests" that stop for manual fiddling'
	)
