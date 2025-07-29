from typing import Any, List, Optional, Union

from clipped.utils.lists import to_list
from clipped.utils.paths import get_files_in_path


def hash_value(value: Any, hash_length: Optional[int] = 12) -> str:
    import hashlib

    value = hashlib.md5(str(value).encode("utf-8")).hexdigest()
    return value[:hash_length] if hash_length is not None else value


def hash_file(
    filepath: str,
    hash_length: int = 12,
    chunk_size: int = 64 * 1024,
    hash_md5: Any = None,
    digest: bool = True,
) -> Union[any, str]:
    import hashlib

    hash_md5 = hash_md5 or hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()[:hash_length] if digest else hash_md5


def hash_files(
    filepaths: List[str],
    hash_length: int = 12,
    chunk_size: int = 64 * 1024,
    hash_md5: Any = None,
    digest: bool = True,
) -> Union[any, str]:
    import hashlib

    hash_md5 = hash_md5 or hashlib.md5()
    filepaths = to_list(filepaths, check_none=True)
    for filepath in filepaths:
        hash_md5 = hash_file(
            filepath=filepath,
            hash_length=hash_length,
            chunk_size=chunk_size,
            hash_md5=hash_md5,
            digest=False,
        )
    return hash_md5.hexdigest()[:hash_length] if digest else hash_md5


def hash_dir(
    dirpath: str,
    exclude: Optional[List[str]] = None,
    hash_length: int = 12,
    chunk_size: int = 64 * 1024,
    hash_md5: Any = None,
    digest: bool = True,
) -> Union[any, str]:
    filepaths = get_files_in_path(path=dirpath, exclude=exclude)
    return hash_files(
        filepaths=filepaths,
        hash_length=hash_length,
        chunk_size=chunk_size,
        hash_md5=hash_md5,
        digest=digest,
    )
