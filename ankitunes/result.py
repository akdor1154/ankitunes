from typing import *

T = TypeVar('T')
E = TypeVar('E')

class Ok(Generic[T]):
	value: T
	def __init__(self, val: T) -> None:
		self.value = val

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Ok):
			return super().__eq__(other)

		return bool(self.value == other.value)

	def __repr__(self) -> str:
		return f'Ok({repr(self.value)})'

class Err(Generic[E]):
	err_value: E
	def __init__(self, val: E) -> None:
		self.err_value = val

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Err):
			return super().__eq__(other)

		return bool(self.err_value == other.err_value)

	def __repr__(self) -> str:
		return f'Ok({repr(self.err_value)})'

Result = Union[Ok[T], Err[E]]