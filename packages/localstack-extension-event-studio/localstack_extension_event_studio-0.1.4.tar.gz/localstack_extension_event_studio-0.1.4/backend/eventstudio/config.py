import os
from pathlib import Path
from typing import Final,Union
BASE_URL:Final[str]='http://localhost:4566/_extension/eventstudio'
API_PREFIX:Final[str]='/api'
EVENTS:Final[str]='/events'
ALL_EVENTS:Final[str]='/events/all'
DB_EVENTS:Final[str]='/events/db'
TRACES:Final[str]='/traces'
REPLAY:Final[str]='/replay'
ALL_ERRORS:Final[str]='/errors/all'
DB_ERRORS:Final[str]='/errors/db'
PACKAGE_ROOT:Final[Path]=Path(__file__).parents[2]
DATABASE_NAME:Final[str]='event_studio.db'
DATABASE_PATH:Final[Union[str,Path]]=DATABASE_NAME if DATABASE_NAME==''else PACKAGE_ROOT/DATABASE_NAME
PERSISTENCE:Final[bool]=os.environ.get('PERSISTENCE','false').lower()=='true'
def get_full_url(endpoint):return f"{BASE_URL}{API_PREFIX}/v1{endpoint}"
def get_relative_url(endpoint):return f"{API_PREFIX}/v1{endpoint}"
def get_full_url_v2(endpoint):return f"{BASE_URL}{API_PREFIX}/v2{endpoint}"
def get_relative_url_v2(endpoint):return f"{API_PREFIX}/v2{endpoint}"