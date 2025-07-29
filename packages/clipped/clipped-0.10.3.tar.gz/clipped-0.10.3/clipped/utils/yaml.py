import yaml

from typing import TextIO, Union

try:
    from yaml import CSafeDumper as _SafeDumper
    from yaml import CSafeLoader as _SafeLoader
except ImportError:
    from yaml import SafeDumper as _SafeDumper
    from yaml import SafeLoader as _SafeLoader


def dump(data, stream=None):
    return yaml.dump(
        data,
        stream=stream,
        Dumper=_SafeDumper,
        default_flow_style=False,
        allow_unicode=True,
    )


def safe_load(filepath: Union[str, TextIO]):
    return yaml.load(filepath, Loader=_SafeLoader)
