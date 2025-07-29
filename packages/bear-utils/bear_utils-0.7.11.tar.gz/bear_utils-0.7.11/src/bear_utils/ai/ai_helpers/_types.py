from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ... import BaseLogger

T_Response = TypeVar("T_Response")


class ResponseParser(ABC, Generic[T_Response]):
    """Abstract base class for response parsers."""

    @abstractmethod
    async def parse(self, raw_response: dict, logger: BaseLogger) -> T_Response:
        """Parse the raw response into the desired format."""
        pass

    @abstractmethod
    def get_default_response(self) -> T_Response:
        """Return a default response structure."""
        pass
