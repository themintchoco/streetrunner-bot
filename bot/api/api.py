import asyncio
import concurrent.futures
import datetime
import hashlib
import json
import urllib

import aiohttp
from marshmallow import Schema, post_load
from marshmallow.schema import SchemaMeta

from store.RedisClient import RedisClient


class ApiSchemaBase(SchemaMeta):
    def __new__(cls, name, bases, attrs):
        paths = attrs.pop('__endpoints__', None)
        endpoints = []

        for base in bases:
            if isinstance(base, ApiSchemaBase):
                for endpoint in base.__endpoints__:
                    endpoints.extend(urllib.parse.urljoin(endpoint, path) for path in (paths if paths else ['']))

        if not endpoints and paths:
            endpoints = paths

        attrs['__endpoints__'] = endpoints
        return super().__new__(cls, name, bases, attrs)


class ApiData(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError


class ApiSchema(Schema, metaclass=ApiSchemaBase):
    def __init__(self, params=None, query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._params = params if params else {}
        self._query = query if query else {}
        self._data = None

    def __getattr__(self, attr):
        for cls in self.__class__.__subclasses__():
            if cls.__name__ == attr:
                return lambda params={}, *args, **kwargs: cls({**self._params, **params}, *args, **kwargs)

        raise AttributeError

    async def api_get(self, *args, **kwargs):
        conn = RedisClient().conn

        for endpoint in self.__endpoints__:
            try:
                url = endpoint.format(
                    **{k: urllib.parse.quote(str(v), safe='') for k, v in self._params.items() if v is not None})
            except KeyError:
                continue

            cache_key = hashlib.md5((url + json.dumps(self._query, sort_keys=True)).encode()).hexdigest()
            if cached := await conn.get(f'api:{cache_key}'):
                return json.loads(cached)

            if query := urllib.parse.urlencode(self._query):
                url += '?' + query

            async with aiohttp.ClientSession(raise_for_status=True) as s:
                async with s.get(url, *args, **kwargs) as r:
                    result = await r.text()
                    await conn.set(f'api:{cache_key}', result, ex=30)
                    return json.loads(result)

        raise

    @post_load
    def make_data(self, data, **kwargs):
        return ApiData(data)

    async def preload(self):
        await self.data
        return self

    @property
    async def data(self):
        if not self._data:
            self._data = self.load(await self.api_get())

        return self._data
