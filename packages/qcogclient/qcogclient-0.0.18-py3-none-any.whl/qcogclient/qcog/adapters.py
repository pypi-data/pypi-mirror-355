import io

import pandas as pd


def as_dataframe(data: pd.DataFrame) -> io.BufferedIOBase:
    """
    Convert a pandas DataFrame to a file-like object.
    """
    return io.BytesIO(data.to_csv(index=False).encode("utf-8"))
