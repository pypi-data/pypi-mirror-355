"""Async client for SVO semantic chunker microservice."""

__version__ = "0.2.6"

import aiohttp
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ChunkerClient:
    def __init__(self, url: str = "http://localhost", port: int = 8009):
        self.base_url = f"{url.rstrip('/')}: {port}"
        self.base_url = f"{url.rstrip('/')}: {port}".replace(': ', ':')
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def get_openapi_schema(self) -> Any:
        url = f"{self.base_url}/openapi.json"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    def parse_chunk(self, chunk) -> 'SemanticChunk':
        from chunk_metadata_adapter import SemanticChunk
        if isinstance(chunk, SemanticChunk):
            return chunk
        obj, err = SemanticChunk.validate_and_fill({k: v for k, v in chunk.items() if k in SemanticChunk.model_fields})
        if err:
            error_fields = err.get('fields')
            if error_fields:
                raise ValueError(f"Chunk does not validate against chunk_metadata_adapter.SemanticChunk: {err['error']}\nFields: {error_fields}\nChunk: {chunk}")
            else:
                raise ValueError(f"Chunk does not validate against chunk_metadata_adapter.SemanticChunk: {err}\nChunk: {chunk}")
        return obj

    async def chunk_text(self, text: str, **params) -> List['SemanticChunk']:
        url = f"{self.base_url}/cmd"
        payload = {
            "jsonrpc": "2.0",
            "method": "chunk",
            "params": {"text": text, **params},
            "id": 1
        }
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            chunks = data.get("result", {}).get("chunks", [])
            return [self.parse_chunk(chunk) for chunk in chunks]

    async def get_help(self, cmdname: Optional[str] = None) -> Any:
        url = f"{self.base_url}/cmd"
        payload = {
            "jsonrpc": "2.0",
            "method": "help",
            "id": 1
        }
        if cmdname:
            payload["params"] = {"cmdname": cmdname}
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def health(self) -> Any:
        url = f"{self.base_url}/cmd"
        payload = {
            "jsonrpc": "2.0",
            "method": "health",
            "id": 1
        }
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()

    def reconstruct_text(self, chunks: List['SemanticChunk']) -> str:
        """
        Reconstruct the original text from a list of SemanticChunk objects.
        Склеивает текст из чанков в исходном порядке.
        """
        sorted_chunks = sorted(
            chunks,
            key=lambda c: c.ordinal if getattr(c, 'ordinal', None) is not None else chunks.index(c)
        )
        return ''.join(chunk.text for chunk in sorted_chunks if getattr(chunk, 'text', None)) 