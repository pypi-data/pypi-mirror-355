from typing import Annotated
from datetime import datetime
from uuid import UUID
import re

from scap._core.schema import BaseSchema, CamelBaseSchema, model_validator
from scap._core._types import StrEnum, AnyUrl, RegexString


_RE_ALNUM   = r'[A-Za-z0-9\-\._]'
_RE_ESC     = r'(?:\\[\\\*\?!"#\$%&\'\(\)\+,/:;<=>@\[\]\^`\{\|}~])'
_RE_ATOM    = rf'(?:\?*|\*?)(?:{_RE_ALNUM}|{_RE_ESC})+(?:\?*|\*?)'
_RE_COMPLEX = rf'(?:{_RE_ATOM}|[\*\-])'

# for `langugage` prop, but some CPEs don't follow RFC 5646
# _RE_LANG = r'(?:[A-Za-z]{2,3}(?:-[A-Za-z]{2}|-[0-9]{3})?|[\*\-])'


class CpeName(RegexString):
    '''CPE Name URI.
    '''
    __example__ = (
        'cpe:2.3:part:vendor:product:version:update:edition:'
        'language:sw_edition:target_sw:target_hw:other'
    )
    __pattern__ = re.compile(rf'''
        cpe:2\.3:
        (?P<part>[aho\*\-]):
        (?P<vendor>{_RE_COMPLEX}):
        (?P<product>{_RE_COMPLEX}):
        (?P<version>{_RE_COMPLEX}):
        (?P<update>{_RE_COMPLEX}):
        (?P<edition>{_RE_COMPLEX}):
        (?P<language>{_RE_COMPLEX}):
        (?P<sw_edition>{_RE_COMPLEX}):
        (?P<target_sw>{_RE_COMPLEX}):
        (?P<target_hw>{_RE_COMPLEX}):
        (?P<other>{_RE_COMPLEX})
    ''', re.VERBOSE)


class ReferenceType(StrEnum):
    '''Internet resource for CPE.
    '''
    ADVISORY   = 'Advisory'
    CHANGE_LOG = 'Change Log'
    PRODUCT    = 'Product'
    PROJECT    = 'Project'
    VENDOR     = 'Vendor'
    VERSION    = 'Version'


class CpeReference(BaseSchema):
    ref:  Annotated[str, AnyUrl]
    type: ReferenceType | None = None


class BaseCpe(CamelBaseSchema):
    '''Base class for CPE items.

    Attributes:
        name: CPE Name string.
        id:   UUID of the CPE Name.
    '''
    id:   UUID
    name: CpeName

    def __init__(sel, **data):
        data.setdefault('name', data.pop('cpeName', None))
        data.setdefault('id', data.pop('cpeNameId', None))
        super().__init__(**data)


class CpeItem(BaseCpe):
    '''The CpeItem element denotes a single CPE Name.

    Attributes:
        title:      Title of the CPE item.
        deprecated: Whether the item is deprecated.
    '''
    part:          str
    vendor:        str
    product:       str
    version:       str
    deprecated:    bool
    created:       datetime
    last_modified: datetime
    title:         str
    refs:          list[CpeReference] | None = None
    deprecated_by: list[BaseCpe] | None = None
    deprecates:    list[BaseCpe] | None = None

    @model_validator(mode='before')
    @classmethod
    def get_title(cls, data):

        if isinstance(data, dict):
            data = CpeName(data['name']).dict() | data
            if 'titles' in data:
                data['title'] = [t['title'] for t in data['titles'] if t['lang'] == 'en'][0]
        return data
