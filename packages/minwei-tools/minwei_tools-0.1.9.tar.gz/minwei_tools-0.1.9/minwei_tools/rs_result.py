from __future__ import annotations
from typing import Generic, Union, TypeVar, Callable

T = TypeVar('T')
E = TypeVar('E')

class Result(Generic[T, E]):
    __value : T = None
    __error : E = None
    __match_args__ = ('value',)

    @property
    def value(self) -> Union[T, E]:
        return self.__value if self.is_ok() else self.__error
    
    @property
    def error(self) -> Union[T, E]:
        return self.__error if self.is_err() else self.__value
    
    @value.setter
    def value(self, value: T) -> None:
        self.__value = value

    @error.setter
    def error(self, value: E) -> None:
        self.__error = value

    def is_ok(self) -> bool:
        return isinstance(self, Ok)
    
    def is_err(self) -> bool:
        return isinstance(self, Err)
    
    def unwrap(self) -> T:
        if self.is_ok():
            return self.value
        raise ValueError("Called unwrap on an Err value")
    
    def unwrap_err(self) -> E:
        if self.is_err():
            return self.error
        raise ValueError("Called unwrap_err on an Ok value")
    
    def map(self, func: Callable[[T], T]) -> Result[T, E]:
        if self.is_ok():
            return Ok(func(self.value))
        return self  # Return the Err unchanged

    def map_err(self, func: Callable[[E], E]) -> Result[T, E]:
        if self.is_err():
            return Err(func(self.error))
        return self  # Return the Ok unchanged

    def and_then(self, func: Callable[[T], Result[T, E]]) -> Result[T, E]:
        if self.is_ok():
            return Ok(func(self.value))
        return self  # Return the Err unchanged

    def or_else(self, func: Callable[[E], Result[T, E]]) -> Result[T, E]:
        if self.is_err():
            return Err(func(self.error))
        return self  # Return the Ok unchanged

    def __str__(self) -> str:
        if self.is_ok():
            return f"Ok({self.value})"
        return f"Err(\"{self.error}\")"

class Ok(Result, Generic[T, E]):
    def __init__(self, value: T) -> None:
        self.value = value

class Err(Result, Generic[T, E]):
    def __init__(self, error: E) -> None:
        self.error = error
