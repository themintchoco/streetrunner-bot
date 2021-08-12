import asyncio
import concurrent.futures
import urllib

import aiohttp
from marshmallow import Schema, post_load
from marshmallow.schema import SchemaMeta


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
        if query is None:
            query = {}
        if params is None:
            params = {}
        self._params = params
        self._query = query
        self._data = None

    def __getattr__(self, attr):
        for cls in self.__class__.__subclasses__():
            if cls.__name__ == attr:
                return lambda params={}, *args, **kwargs: cls({**self._params, **params}, *args, **kwargs)

        raise AttributeError

    async def api_get(self, *args, **kwargs):
        for endpoint in self.__endpoints__:
            try:
                url = endpoint.format(
                    **{k: urllib.parse.quote(str(v), safe='') for k, v in self._params.items() if v is not None})
            except KeyError:
                continue

            if query := urllib.parse.urlencode(self._query):
                url += '?' + query

            async with aiohttp.ClientSession(raise_for_status=True) as s:
                async with s.get(url, *args, **kwargs) as r:
                    return await r.json()

        raise

    @post_load
    def make_data(self, data, **kwargs):
        return ApiData(data)

    async def apreload(self):
        await self.adata
        return self

    def preload(self):
        self.data
        return self

    @property
    async def adata(self):
        if not self._data:
            self._data = self.load(await self.api_get())

        return self._data

    @property
    def data(self):
        def helper():
            return asyncio.run_coroutine_threadsafe(self.adata).result()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, self.adata).result()
