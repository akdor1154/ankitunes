from anki.notes import Note
import urllib.parse
from .result import Result, Ok, Err
from typing import *
import re
from dataclasses import dataclass
import urllib.request
import json
import random
import warnings


@dataclass
class GrabbedTune:
	name: str
	key: str
	type: str
	abc: str
	uri: str


class GrabError:
	class BadUrl(NamedTuple):
		url: str

		@property
		def msg(self) -> str:
			return f'{self.url} doesn\'t look like a valid tune URL. Tune URLs should look like "https://thesession.org/tunes/2" or "https://thesession.org/tunes/2#setting1".'

	class NetworkError(NamedTuple):
		url: str
		exception: Exception

		@property
		def msg(self) -> str:
			return f"Network error opening {self.url} - {str(self.exception)}"

	class JSONError(NamedTuple):
		url: str
		body: bytes

		@property
		def msg(self) -> str:
			return f"TheSession.org gave a dodgy response that I couldn't parse. This might be a network problem, try again. Body: {self.body!r}"

	class APISpecError(NamedTuple):
		url: str
		tune: Dict[Any, Any]
		e: Exception

		@property
		def msg(self) -> str:
			from pprint import pformat

			tuneStr = pformat(self.tune)
			return (
				f"TheSession.org gave a confusing response that I couldn't understand. Please raise this as a GitHub issue at https://github.com/akdor1154/ankitunes ."
				f"The response in question: {tuneStr}\n"
				f"The error: {repr(self.e)}"
			)

	class NoSuchSetting(NamedTuple):
		tune: "TheSessionTune"
		setting_id: int

		@property
		def msg(self) -> str:
			url = f"https://thesession.org/tunes/{self.tune.id}"
			return f"There is no such setting {self.setting_id} for the tune {self.tune.name} at {url} ."


_GrabError = Union[
	GrabError.BadUrl,
	GrabError.NetworkError,
	GrabError.JSONError,
	GrabError.APISpecError,
	GrabError.NoSuchSetting,
]

GrabResult = Result[GrabbedTune, _GrabError]

PATH_REGEX = re.compile(r"/tunes/(\d+)/?")
FRAGMENT_REGEX = re.compile(r"setting(\d+)")


def _parse_thesession_url(
	url: str,
) -> Result[Tuple[int, Optional[int]], GrabError.BadUrl]:

	try:
		parsed = urllib.parse.urlsplit(url)
	except ValueError:
		return Err(GrabError.BadUrl(url))

	if parsed.netloc not in {"thesession.org", "www.thesession.org"}:
		return Err(GrabError.BadUrl(url))

	parsed_path = PATH_REGEX.match(parsed.path)
	if parsed_path is None:
		return Err(GrabError.BadUrl(url))

	tune_id = int(parsed_path[1])

	if parsed.fragment == "":
		setting_id = None
	else:
		parsed_fragment = FRAGMENT_REGEX.match(parsed.fragment)
		if parsed_fragment is None:
			return Err(GrabError.BadUrl(url))
		setting_id = int(parsed_fragment[1])

	return Ok((tune_id, setting_id))


def get_from_thesession(url: str) -> Result[GrabbedTune, _GrabError]:
	"Takes a url like https://thesession.org/tunes/2#setting2 and returns the result as a Note."

	parse_result = _parse_thesession_url(url)
	if isinstance(parse_result, Err):
		return parse_result

	tune_id, setting_id = parse_result.value

	return _get_from_thesession(tune_id, setting_id)


def _get_from_thesession(
	tune_id: int, setting_id: Optional[int]
) -> Result[GrabbedTune, _GrabError]:
	tune_result = _retrieve_thesession_tune(tune_id)

	if isinstance(tune_result, Err):
		return tune_result

	tune = tune_result.value

	if setting_id is None:
		i, setting = random.choice(list(enumerate(tune.settings)))
	else:
		try:
			i, setting = next(
				(i, s) for (i, s) in enumerate(tune.settings) if s.id == setting_id
			)
		except StopIteration:
			return Err(GrabError.NoSuchSetting(tune, setting_id))

	uri = f"https://thesession.org/tunes/{tune.id}#setting{setting.id}"
	abc = _process_sessionapi_abc(tune, setting, i)

	return Ok(
		GrabbedTune(name=tune.name, key=setting.key, type=tune.type, abc=abc, uri=uri)
	)


@dataclass
class TheSessionTune:
	id: int
	name: str
	type: str

	@dataclass
	class Setting:
		id: int
		key: str
		abc: str

	settings: List["TheSessionTune.Setting"]


def _retrieve_thesession_tune(tune_id: int) -> Result[TheSessionTune, _GrabError]:
	url = f"https://thesession.org/tunes/{tune_id}?format=json"

	try:
		with urllib.request.urlopen(url) as response:
			body: bytes = response.read()
	except Exception as e:
		return Err(GrabError.NetworkError(url, e))

	try:
		tune_json = json.loads(body)
	except Exception as e:
		return Err(GrabError.JSONError(url, body))

	def assert_str(s: Any) -> str:
		if not isinstance(s, str):
			raise ValueError(f"{s} is not a string!")
		return s

	def assert_int(s: Any) -> int:
		if not isinstance(s, int):
			raise ValueError(f"{s} is not an int!")
		return s

	try:
		tune = TheSessionTune(
			id=assert_int(tune_json["id"]),
			name=assert_str(tune_json["name"]),
			type=assert_str(tune_json["type"]),
			settings=[
				TheSessionTune.Setting(
					id=assert_int(setting_json["id"]),
					key=assert_str(setting_json["key"]),
					abc=assert_str(setting_json["abc"]),
				)
				for setting_json in tune_json["settings"]
			],
		)
	except (KeyError, ValueError) as e:
		return Err(GrabError.APISpecError(url, tune_json, e))

	return Ok(tune)


def _process_sessionapi_abc(
	tune: TheSessionTune, setting: TheSessionTune.Setting, setting_index: int
) -> str:
	timeSig = _getTimeSignature(tune.type)
	timeSigABC = f"\nM: {timeSig}" if timeSig is not None else ""
	NL = "\n"
	return f"""\
X: {setting_index+1}
T: {tune.name}
R: {tune.type}{timeSigABC}
L: 1/8
K: {setting.key}
{setting.abc.replace('!', NL)}
"""


def _getTimeSignature(tuneType: str) -> Optional[str]:
	if tuneType == "reel":
		return "4/4"
	elif tuneType == "jig":
		return "6/8"
	elif tuneType == "slip jig":
		return "9/8"
	elif tuneType == "hornpipe":
		return "4/4"
	elif tuneType == "polka":
		return "2/4"
	elif tuneType == "slide":
		return "12/8"
	elif tuneType == "waltz":
		return "3/4"
	elif tuneType == "barndance":
		return "4/4"
	elif tuneType == "strathspey":
		return "4/4"
	elif tuneType == "three-two":
		return "3/2"
	elif tuneType == "mazurka":
		return "3/4"
	elif tuneType == "march":
		return "4/4"
	else:
		warnings.warn(f"Unknown tune type {tuneType}! Please raise a bug!")
		return None
