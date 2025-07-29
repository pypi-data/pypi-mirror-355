from typing import Optional, AsyncIterator
from abc import ABC, abstractmethod

class StreamResource(ABC):
    def __init__(self, content_type: Optional[str], filename: Optional[str]):
        self.content_type = content_type or "application/octet-stream"
        self.filename = filename

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self):
        return self._iterate_stream()

    @abstractmethod
    def get_stream(self):
        pass
    
    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def _iterate_stream(self) -> AsyncIterator[bytes]:
        pass
