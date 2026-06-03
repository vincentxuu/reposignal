from typing import Protocol
from pathlib import Path

import polars as pl


class Extractor(Protocol):
    name: str
    file_glob: str

    def extract(self, raw_dir: Path) -> pl.DataFrame: ...
