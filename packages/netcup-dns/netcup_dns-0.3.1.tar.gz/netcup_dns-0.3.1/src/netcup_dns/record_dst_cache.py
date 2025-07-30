import json
from datetime import timedelta
from pathlib import Path

from netcup_dns import datetime_util


class RecordDestinationCache:
    def __init__(self, cache_dir: Path, cache_validity_seconds: int):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir.joinpath('record_destinations.json')

        self.cache_validity_seconds = cache_validity_seconds

        self.data: dict[str, tuple[str, str]] | None = None

    def get(self, domain: str, hostname: str, type_: str) -> str | None:
        data = self.read_from_file()
        key = self._data_key(domain, hostname, type_)
        date_str, destination = data.get(key, (None, None))

        if destination is None:
            return None

        # Check if cached destination is still valid.
        dt = datetime_util.from_str(date_str)
        time_difference = datetime_util.now() - dt
        zero = timedelta()
        max_difference = timedelta(seconds=self.cache_validity_seconds)
        #
        if time_difference <= zero:
            raise ValueError('Invalid dates')
        if time_difference >= max_difference:
            # This cache entry is outdated.
            return None

        return destination

    def set(self, domain: str, hostname: str, type_: str, destination: str):
        if self.data is None:
            raise Exception('Can only modify data after it has been read first.')

        key = self._data_key(domain, hostname, type_)
        self.data[key] = (datetime_util.now_str(), destination)

    @staticmethod
    def _data_key(domain, hostname, type_) -> str:
        return f'{hostname}.{domain}.{type_}'

    def read_from_file(self) -> dict[str, tuple[str, str]]:
        if self.data is not None:
            return self.data

        if self.cache_file.exists():
            data = json.loads(self.cache_file.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError(f'Expected to read a dict from json file, but got {type(data)} instead.')
            self.data = data
        else:
            self.data = {}

        return self.data

    def write_to_file(self):
        if self.data is None:
            raise Exception('Can only write data after it has been read first.')

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.data), encoding='utf-8')
