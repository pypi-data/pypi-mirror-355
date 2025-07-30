#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import ipaddress
import json
from functools import lru_cache
from pathlib import Path
from typing import Type

import requests
from nc_dnsapi import Client, DNSRecord

from netcup_dns import union
from netcup_dns.exception import UnknownIPException, MultipleRecordsException
from netcup_dns.record_dst_cache import RecordDestinationCache

from netcup_dns.print_util import print_info, print_err


def main():
    """
    The main effort is done by https://github.com/nbuchwitz/nc_dnsapi
    """
    args = parse_args()
    cfg_files: list[Path] = args.cfg_files
    cache: RecordDestinationCache | None = args.cache

    dicts = [json.loads(cfg_file.read_text()) for cfg_file in cfg_files]
    cfg = union.union(dicts)

    customer = cfg['customer']
    api_key = cfg['api_key']
    api_password = cfg['api_password']

    entries = cfg['records']
    with Client(customer, api_key, api_password) as api:
        for entry in entries:
            domain = entry['domain']
            hostname = entry['hostname']
            type_ = entry['type'].upper()

            if type_ == 'A':
                # Lazy: Only determine external IPv4 if an A record shall be updated.
                try:
                    destination = external_ipv4()
                except UnknownIPException as e:
                    print_err(str(e))
                    exit(1)
            elif type_ == 'AAAA':
                # Lazy: Only determine external IPv6 if an AAAA record shall be updated.
                try:
                    destination = external_ipv6()
                except UnknownIPException as e:
                    print_err(str(e))
                    exit(1)
            else:
                raise ValueError(f'DNS record type {type_} is not supported.')

            if update_record_destination(api, domain, hostname, type_, destination, cache):
                print_info(f'Set {hostname}.{domain} {type_} record to {destination}')
            else:
                print_info(f'The {hostname}.{domain} {type_} record points already to {destination}')


def parse_args():
    parser = argparse.ArgumentParser(prog='netcup-dns',
                                     description='Update DNS A/AAAA records with your current external IP address'
                                                 ' using the netcup DNS API.')
    parser.add_argument('--config',
                        help='Path to one or more .json configuration files.',
                        dest='cfg_files',
                        default=Path('/etc/netcup-dns/config.json'),
                        nargs='+',
                        type=Path)
    parser.add_argument('--cache-directory',
                        help='Path to cache directory. Retrieved and updated DNS records are cached there.',
                        dest='cache_dir',
                        default=Path.home().joinpath('.netcup-dns/cache'),
                        type=Path)
    parser.add_argument('--cache-validity-seconds',
                        help='Value in seconds for how long cached DNS records are valid.'
                             ' Set to `0` to disable caching.',
                        dest='cache_validity_seconds',
                        default=86400,
                        type=int)
    args = parser.parse_args()

    args.cfg_files: list[Path]
    for file in args.cfg_files:
        if not file.is_file():
            raise Exception(f'The given config file does not exist: {file.absolute()}')
        if not file.name.endswith('.json'):
            raise Exception(f'Expected a JSON config file with file extension .json: {file}')
    args.cache_validity_seconds: int
    if args.cache_validity_seconds < 0:
        raise Exception(f'A negative cache validity duration is not allowed: {args.cache_validity_seconds}')

    args.cache = RecordDestinationCache | None
    if args.cache_validity_seconds == 0:
        # Disable caching.
        args.cache = None
    else:
        args.cache = RecordDestinationCache(args.cache_dir, args.cache_validity_seconds)

    return args


def update_record_destination(api: Client, domain: str, hostname: str, type_: str, destination: str,
                              cache: RecordDestinationCache = None) -> bool:
    """
    Updates the `destination` of the DNS record identified by `domain`, `hostname` and `type`.

    :param api: API client object
    :param domain:
    :param hostname:
    :param type_: A or AAAA
    :param destination: IPv4 (if `type_` = A) or IPv6 (if `type_` = AAAA)
    :param cache:
    :return: True if `destination` differs from the old destination or if a new DNS record was created.
    """
    # If caching is enabled.
    if cache is not None:
        # If a valid cache entry is available, check if the destination is still the same.
        # If this is the case, we do not need to do anything else.
        if cache.get(domain, hostname, type_) == destination:
            return False

    try:
        record = get_record(api, domain, hostname, type_)
        changed = record.destination != destination
        if changed:
            record.destination = destination
            # The destination has changed, so we update the DNS record.
            api.update_dns_record(domain, record)
    except MissingRecordsException as e:
        # The DNS record does not yet exist. So we create a new one.
        record = DNSRecord(domain=domain, hostname=hostname, type=type_, destination=destination)
        changed = True
        api.add_dns_record(domain, record)

    # Either we verified that the destination is still identical, or we created/updated the DNS record.
    # Therefore, we can reset the cache timeout.
    cache.set(domain, hostname, type_, destination)
    cache.write_to_file()

    return changed


class MissingRecordsException(Exception):
    pass


def get_record(api: Client, domain: str, hostname: str, type_: str) -> DNSRecord:
    """
    :param api:
    :param domain:
    :param hostname:
    :param type_:
    :return: The DNS record identified by `domain`, `hostname` and `type`.
    :raises MultipleRecordsException:
    :raises MissingRecordsException:
    """
    records: list[DNSRecord] = api.dns_records(domain)
    record: DNSRecord

    matches = [record for record in records if record.hostname == hostname and record.type == type_]
    if len(matches) == 0:
        raise MissingRecordsException()
    if len(matches) > 1:
        raise MultipleRecordsException(f'Expected one DNSRecord for {hostname}.{domain}, but got {len(matches)}')
    return matches[0]


def ipv4_endpoints() -> list[str]:
    """
    :return: List of services that return your external IPv4 address.
    """
    # IPv4 only.
    endpoints = [
        'https://checkipv4.dedyn.io',
        'https://api.ipify.org',
        'https://v4.ident.me/',
    ]
    # Not sure if they return IPv4 addresses only.
    endpoints += ['https://ipinfo.io/ip', 'https://ifconfig.me/ip']
    return endpoints


def ipv6_endpoints() -> list[str]:
    """
    :return: List of services that return your external IPv6 address.
    """
    # IPv6 only.
    endpoints = [
        'https://checkipv6.dedyn.io',
        'https://api6.ipify.org',
        'https://v6.ident.me/',
        'https://ipv6.icanhazip.com',
    ]
    # Returns either IPv4 or IPv6.
    endpoints += ['https://ifconfig.co/ip']
    # Not sure if they return IPv6.
    endpoints += ['https://ipinfo.io/ip']

    # https://ifconfig.co
    # - if it detects `curl`, only the IP is returned
    # - but on a normal request, a HTML website is given
    # https://ifconfig.co/ip
    # - returns only the ip
    # - `curl -4/-6 https://ifconfig.co/ip` -> returns IPv4/IPv6

    return endpoints


def external_ip(version: Type[ipaddress.IPv4Address | ipaddress.IPv6Address], timeout: float = 5,
                endpoints: list[str] = None) -> str:
    """
    :param version: Weather the public IPv4 or IPv6 address shall be determined.
    :param endpoints: List of webservices that return ones public IP IPv4/IPv6 address.
    :argument timeout: Timeout for each webservice in seconds.
    :return: Public IPv4/IPv6 address.
    :raises UnknownIPException:
    """
    if endpoints is None:
        if version == ipaddress.IPv4Address:
            endpoints = ipv4_endpoints()
        elif version == ipaddress.IPv6Address:
            endpoints = ipv6_endpoints()
        else:
            raise ValueError(f'Invalid argument: {version}')

    if len(endpoints) == 0:
        raise ValueError(f'Invalid argument: {endpoints}')

    for endpoint in endpoints:
        try:
            # Timeout after 5 seconds.
            ip = requests.get(endpoint, timeout=timeout).text.strip()
        except requests.exceptions.RequestException:
            continue

        try:
            # Try to parse the IP address.
            parsed_ip = ipaddress.ip_address(ip)
        except ValueError:
            continue

        # Check if it is actually an IPv4/IPv6 address.
        if not isinstance(parsed_ip, version):
            continue

        # Return IP address as string.
        return parsed_ip.exploded

    version_str = 'IPv4' if version == ipaddress.IPv4Address else 'IPv6'
    raise UnknownIPException(f'Could not determine public {version_str} address.')


@lru_cache(maxsize=None)
def external_ipv4(timeout: float = 5, endpoints: list[str] = None) -> str:
    """
    :param endpoints: List of webservices that return one's public IPv4 address.
    :argument timeout: Timeout for each webservice in seconds.
    :return: Public IPv4 address.
    :raises UnknownIPException:
    """
    return external_ip(ipaddress.IPv4Address, timeout, endpoints)


@lru_cache(maxsize=None)
def external_ipv6(timeout: float = 5, endpoints: list[str] = None) -> str:
    """
    :param endpoints: List of webservices that return one's public IPv6 address.
    :argument timeout: Timeout for each webservice in seconds.
    :return: Public IPv6 address.
    :raises UnknownIPException:
    """
    return external_ip(ipaddress.IPv6Address, timeout, endpoints)


if __name__ == '__main__':
    main()
