# netcup-dns

Update DNS A/AAAA records with your current external IP address using the netcup DNS API.

## Installation

Install release from PyPI (https://pypi.org/project/netcup-dns/):

```shell
pip install netcup-dns
```

Install release from TestPyPI (https://test.pypi.org/project/netcup-dns/):

```shell
pip install -i https://test.pypi.org/simple/ netcup-dns
```

Build and install on Arch Linux:

```shell
make
```

Build and install with `pip`:

```shell
make install-pip
```

## Configuration

For each netcup customer, create a `.json` configuration file inside `/etc/netcup-dpns`.

There is an [example configuration](cfg/example.json).

## Usage

```
usage: netcup-dns [-h] [--config CFG_FILES [CFG_FILES ...]]
                  [--cache-directory CACHE_DIR]
                  [--cache-validity-seconds CACHE_VALIDITY_SECONDS]

Update DNS A/AAAA records with your current external IP address using the
netcup DNS API.

options:
  -h, --help            show this help message and exit
  --config CFG_FILES [CFG_FILES ...]
                        Path to one or more .json configuration files.
  --cache-directory CACHE_DIR
                        Path to cache directory. Retrieved and updated DNS
                        records are cached there.
  --cache-validity-seconds CACHE_VALIDITY_SECONDS
                        Value in seconds for how long cached DNS records are
                        valid. Set to `0` to disable caching.
```

### Examples

Both examples use the same effective configuration. In the second case, personal information such as the API password is stored in a separate configuration file. 

```shell
netcup-dns --config ./cfg/example.json
netcup-dns --config ./cfg/public.json ./cfg/secret.json
```

## TODOs

API backend:

- Currently: nc-dnsapi
  - https://pypi.org/project/nc-dnsapi/
  - https://github.com/nbuchwitz/nc_dnsapi
- Alternatives:
  - https://github.com/johndoe31415/dnssync_nc

Alternative external IP detection:

```python
def external_ip_upnp():
    """
    https://stackoverflow.com/a/41385033

    Didn't work for me. Even after double checking fritz.box settings:

    fritz.box > Heimnetz > Netzwerk > Statusinformationen über UPnP übertragen
    """
    import miniupnpc
    u = miniupnpc.UPnP()
    u.discoverdelay = 1000
    u.discover()
    u.selectigd()
    print('external ip address: {}'.format(u.externalipaddress()))
```
