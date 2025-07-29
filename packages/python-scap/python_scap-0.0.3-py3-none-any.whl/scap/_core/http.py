from typing import TypedDict
import logging
import zipfile
import io
import os
import re

from httpx import AsyncClient, Client, Response

log = logging.getLogger(__name__)


class ResponseItem(TypedDict):
    filename: str
    content:  bytes


class ClientMixin:

    @staticmethod
    def unzip(content: bytes) -> list[ResponseItem]:
        log.info('Unzipping response')

        output = list()
        buffer = io.BytesIO(content)

        with zipfile.ZipFile(buffer) as zf:
            for filename in zf.namelist():
                with zf.open(filename) as file:
                    output.append({
                        'filename': filename,
                        'content': file.read(),
                    })

        return output

    def get_filename(self, response: Response) -> str:
        if (cd := response.headers.get('content-disposition')):
            if (match := re.search(r'filename\*?=([^;]+)', cd)):
                filename = match.group(1).strip().strip('"')
                if filename.lower().startswith("utf-8''"):
                    filename = filename[7:]
                return filename

        return os.path.basename(response.url.path)

    def _response(self, response: Response) -> list[ResponseItem]:
        response.raise_for_status()

        if response.headers.get('content-type') == 'application/x-zip-compressed':
            return self.unzip(response.content)
        else:
            return [{
                'filename': self.get_filename(response),
                'content': response.content,
            }]


class BaseClient(ClientMixin, Client):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('follow_redirects', True)
        super().__init__(*args, **kwargs)

    def request(self, method, url, **kwargs) -> list[ResponseItem]:
        log.info('Downloading %s', url)

        response = super().request(method, url, **kwargs)
        return self._response(response)


class AsyncBaseClient(ClientMixin, AsyncClient):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('follow_redirects', True)
        super().__init__(*args, **kwargs)

    async def request(self, method, url, **kwargs) -> list[ResponseItem]:
        log.info('Downloading %s', url)

        response = await super().request(method, url, **kwargs)
        return self._response(response)


class NvdClient(BaseClient):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('base_url', 'https://nvd.nist.gov/feeds/')
        super().__init__(*args, **kwargs)
