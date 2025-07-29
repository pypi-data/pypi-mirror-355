from typing import Generic, TypeVar
from pydantic import BaseModel

A = TypeVar('A')
B = TypeVar('B')

class KotlinPair(BaseModel, Generic[A, B]):
    first: A
    second: B
