import io
import pathlib


def load(file: pathlib.Path | str | io.IOBase) -> io.BytesIO:
    file_to_upload: io.BytesIO

    if isinstance(file, str):
        file = pathlib.Path(file)

    if isinstance(file, pathlib.Path):
        with open(str(file), "rb") as f:
            file_to_upload = io.BytesIO(f.read())

    elif isinstance(file, io.TextIOBase):
        file_to_upload = io.BytesIO(file.read().encode("utf-8"))

    elif isinstance(file, io.BufferedIOBase):
        file_to_upload = io.BytesIO(file.read())

    else:
        raise ValueError(
            "Invalid file type - must be a pathlib.Path, a file-like object or a string"
        )

    return file_to_upload
