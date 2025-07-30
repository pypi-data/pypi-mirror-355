#!/usr/bin/env python3
from datetime import datetime, timezone


def test():
    dt = datetime.now()

    print('non UTC:')
    print(dt)

    print('\nUTC:')
    print(now())
    print(to_str(now()))
    print(now_str())
    print(from_str(to_str(now())))

    print('\nlocalized:')
    print(dt.tzinfo)
    dt = dt.replace(tzinfo=timezone.utc)
    print(dt)


def now() -> datetime:
    return datetime.now(timezone.utc)


def now_str() -> str:
    return to_str(now())


def to_str(dt: datetime) -> str:
    return dt.strftime(fmt())


def from_str(dt_str: str) -> datetime:
    dt = datetime.strptime(dt_str, fmt())
    return dt.replace(tzinfo=timezone.utc)


def fmt() -> str:
    return '%Y%m%dT%H%M%S'


def fmt_len() -> int:
    return 13


if __name__ == '__main__':
    test()
