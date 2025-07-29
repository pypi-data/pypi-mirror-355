from typing import TYPE_CHECKING, Iterator
from functools import cached_property
from itertools import islice
import logging
import json

from scap._core.http import NvdClient
from scap._core.sql import BaseSqlModel
from scap.schemas.cpe import CpeItem
from scap.sql_models.cpe import SqlCpeItem, SqlCpeDeprecation

if TYPE_CHECKING:
    from sqlalchemy.engine.base import Engine
    from scap._core.http import ResponseItem


log = logging.getLogger(__name__)

logging.getLogger('httpx').setLevel(logging.WARNING)


class NvdCpeClient(NvdClient):
    '''Client for retrieving CPE (Common Platform Enumeration) information
    from the NVD (National Vulnerability Database).
    '''

    @cached_property
    def chunks(self) -> list['ResponseItem']:
        URL = '/json/cpe/2.0/nvdcpe-2.0.zip'
        return self.get(URL)

    def get_cpe_items(self) -> Iterator[CpeItem]:

        for chunk in self.chunks:
            log.info('Processing chunk: %s', chunk['filename'])

            data = json.loads(chunk['content'])

            for product in data['products']:
                # TODO: make dedeplication a method of CpeItem
                # dedup refs
                if (refs := product['cpe'].pop('refs', None)):
                    _refs = set((ref['ref'], ref.get('type')) for ref in refs)
                    refs = [dict(zip(('ref', 'type'), x)) for x in _refs]
                    product['cpe']['refs'] = refs

                # dedup deprecations
                for key in ('deprecatedBy', 'deprecatedById'):
                    if (deprs := product['cpe'].get(key)):
                        _deprs = set((d['cpeName'], d['cpeNameId']) for d in deprs)
                        deprs = [dict(zip(('cpeName', 'cpeNameId'), x)) for x in _deprs]
                        product['cpe'][key] = deprs

                yield CpeItem.model_validate(product['cpe'])


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def populate_database(engine: 'Engine', block_size: int = 5000) -> None:
    '''Populate a database with CPE items from the NVD.
    '''
    from sqlmodel import Session

    BaseSqlModel.metadata.create_all(engine)


    client = NvdCpeClient()

    with Session(engine) as session:

        log.info('Populating CPE items...')
        count = 0
        for block in chunk(client.get_cpe_items(), block_size):
            count += len(block)

            for product in block:
                item = SqlCpeItem(**product.model_dump())
                validated_item = SqlCpeItem.model_validate(item)
                session.add(validated_item)

            session.commit()
            log.info('Added %i CPE items', count)

        log.info('Populating CPE deprecations...')
        count = 0
        for block in chunk(client.get_cpe_items(), block_size):
            count += len(block)

            for product in block:
                for depr in product.deprecated_by or []:
                    dep = SqlCpeDeprecation(
                        deprecated_by_id=depr.id,
                        deprecates_id=product.id,
                    )
                    session.add(dep)

            session.commit()
            log.info('Added %i CPE deprecations', count)
