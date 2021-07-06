import ankitunes
from ankitunes.load_from_session import get_from_thesession, GrabError, GrabResult
from typing import *
import unittest.mock
import urllib.request
from ankitunes.result import Result, Ok, Err
from contextlib import contextmanager


@contextmanager
def mock_urlopen(
	body: Optional[str] = None, raises: Optional[Exception] = None
) -> Generator[None, None, None]:
	if not ((body is None) ^ (raises is None)):
		raise TypeError("Exactly one of body or raises must be None")
	unittest.mock.Mock(spec_set=urllib.request)
	if body is not None:
		urlopen_mock = unittest.mock.Mock(spec_set=urllib.request.urlopen)
		urlopen_mock = unittest.mock.mock_open(urlopen_mock, read_data=body.encode("utf-8"))
	elif raises is not None:
		urlopen_mock = unittest.mock.Mock(spec_set=urllib.request.urlopen, side_effect=raises)
	else:
		raise Exception("Impossible!")
	with unittest.mock.patch("urllib.request.urlopen", urlopen_mock):
		yield


def test_successful_load() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.org/tunes/1")
	assert isinstance(result, Ok), f"{result.err_value.msg}"
	tune = result.value
	assert tune.name == "Some Tune"


def test_successful_load_setting() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.org/tunes/1#setting1")
	assert isinstance(result, Ok), f"{result.err_value.msg}"
	tune = result.value
	assert tune.name == "Some Tune"


def test_bad_uri() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https:\\thesession.org/tunes/1")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.BadUrl("https:\\thesession.org/tunes/1")


def test_bad_domain() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.borg/tunes/1")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.BadUrl("https://thesession.borg/tunes/1")


def test_bad_path() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.org/tunes/abc")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.BadUrl("https://thesession.org/tunes/abc")


def test_bad_setting() -> None:
	with mock_urlopen(
		'{"id": 0, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.org/tunes/1#set")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.BadUrl("https://thesession.org/tunes/1#set")


def test_timeout() -> None:
	e = Exception("bang")
	with mock_urlopen(raises=e):
		result = get_from_thesession("https://thesession.org/tunes/1#setting1")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.NetworkError("https://thesession.org/tunes/1?format=json", e)


def test_bad_json() -> None:
	with mock_urlopen("{"):
		result = get_from_thesession("https://thesession.org/tunes/1#setting1")
	assert isinstance(result, Err)
	val = result.err_value
	assert val == GrabError.JSONError("https://thesession.org/tunes/1?format=json", b"{")


def test_api_bad() -> None:
	with mock_urlopen("{}"):
		result = get_from_thesession("https://thesession.org/tunes/1#setting1")
	assert isinstance(result, Err)
	val = result.err_value
	assert isinstance(val, GrabError.APISpecError)


def test_no_setting() -> None:
	with mock_urlopen(
		'{"id": 1, "name":"Some Tune", "type": "reel", "settings": [{"abc": "abc", "key": "Cmajor"}]}'
	):
		result = get_from_thesession("https://thesession.org/tunes/1#setting2")
	assert isinstance(result, Err)
	val = result.err_value
	assert isinstance(val, GrabError.NoSuchSetting)


def test_real_cooleys() -> None:
	result = get_from_thesession("https://thesession.org/tunes/1#setting2")
	assert isinstance(result, Ok)
	tune = result.value
	assert tune == GrabResult(
		name="Cooley's",
		key="Eminor",
		type="reel",
		abc=(
			"|:F|CGGC G2 CG|G2 FG BGFE|(3DCB, FB, GB,FB,|DB,DF BFDB,|! CGGC G2 CG|G2 FG Bcde|fdcd BGFB|B,CDF C3:|! "
			"|:d|cG ~G2 cede| cG ~G2 ecBG|(3FGF DF B,FDF|GFDF Bcde|! cG ~G2 cede| cG ~G2 Bcde| fdcd BGFB| B,CDF C3:|"
		),
	)
