import pandas as pd
import numpy as np
from pathlib import Path
import os
import urllib.request
import datetime
from typing import Union, Optional

from astdys.util import convert_mjd_to_date, convert_mjd_to_datetime
from astdys.catalog import Catalog

catalog1 = Catalog(
    original_filename='cache/allnum.cat',
    filename='cache/allnum.csv',
    url="https://newton.spacedys.com/~astdys2/catalogs/allnum.cat",
    catalog_type='osculating',
    skip_rows=6,
    columns=['num', 'epoch', 'a', 'e', 'inc', 'Omega', 'omega', 'M', 'del_1', 'del_2', 'del_3'],
    degree_columns=["inc", "Omega", "omega", "M"],
)

catalog2 = Catalog(
    original_filename='cache/all.syn',
    filename='cache/allsyn.csv',
    url="https://newton.spacedys.com/~astdys2/propsynth/all.syn",
    catalog_type='synthetic',
    skip_rows=2,
    columns=['num', 'mag', 'a', 'e', 'sinI', 'n', 'g', 's', 'lce', 'my'],
    degree_columns=["sinI", "n"],
)


class astdys:
    logger = None

    catalogs = {}

    catalogs_configs = {'osculating': catalog1, 'synthetic': catalog2}
    catalog_type = 'osculating'

    @classmethod
    def search(cls, num: Union[int, dict]) -> dict[str, list[Union[str, float]]]:
        if cls.catalog() is None:
            cls.load()

        if isinstance(num, int) or isinstance(num, str):
            num = str(num)
            if num in cls.catalog().index:
                return cls.catalog().loc[num].to_dict()

            return None
        else:
            num_str = [str(n) for n in num]
            filtered_catalog = cls.catalog().loc[cls.catalog().index.intersection(num_str)]
            result = filtered_catalog.to_dict(orient='index')
            return result

    @classmethod
    def search_by_axis(cls, axis: float, sigma=0.1) -> pd.DataFrame:
        if cls.catalog() is None:
            cls.load()
        df = cls.catalog()[(cls.catalog()['a'] >= axis - sigma) & (cls.catalog()['a'] <= axis + sigma)]
        return df

    @classmethod
    def load(cls):
        filename = cls.catalog_full_filename()
        if cls.catalog() is None:
            output_file = Path(filename)
            if not output_file.exists():
                cls.build()

        cls.catalogs[cls.catalog_type] = pd.read_csv(filename, dtype={0: str})
        cls.catalogs[cls.catalog_type]["num"] = cls.catalogs[cls.catalog_type]["num"].astype(str)
        cls.catalogs[cls.catalog_type].set_index('num', inplace=True)

    @classmethod
    def catalog(cls) -> Optional[pd.DataFrame]:
        if cls.catalog_type in cls.catalogs:
            return cls.catalogs[cls.catalog_type]
        return None

    @classmethod
    def set_type(cls, catalog_type: str) -> None:
        if catalog_type in cls.catalogs_configs:
            cls.catalog_type = catalog_type
            cls.load()
        else:
            raise Exception(f"Catalog type {catalog_type} is not supported")

    @classmethod
    def catalog_config(cls) -> Optional[Catalog]:
        if cls.catalog_type in cls.catalogs_configs:
            return cls.catalogs_configs[cls.catalog_type]
        return None

    @classmethod
    def log(cls, text: str) -> None:
        if cls.logger is None:
            print(text)
        else:
            cls.logger.debug(text)

    @classmethod
    def catalog_time(cls) -> str:
        if cls.catalog() is None:
            cls.load()

        elems = cls.search(1)
        return convert_mjd_to_date(elems["epoch"])

    @classmethod
    def datetime(cls) -> datetime.datetime:
        if cls.catalog() is None:
            cls.load()
        elems = cls.search(1)
        return convert_mjd_to_datetime(elems["epoch"])

    @classmethod
    def astdys_full_filename(cls) -> str:
        filename = f"{os.getcwd()}/{cls.catalog_config().original_filename}"
        return filename

    @classmethod
    def catalog_full_filename(cls) -> str:
        filename = f"{os.getcwd()}/{cls.catalog_config().filename}"
        return filename

    @classmethod
    def rebuild(cls):
        input_file = Path(cls.astdys_full_filename())
        if input_file.exists():
            input_file.unlink()
        cls.build()

    @classmethod
    def build(cls):
        input_file = Path(cls.astdys_full_filename())
        if not input_file.exists():
            cls.log("Cannot find AstDyS catalog. Trying to download it...")
            try:
                urllib.request.urlretrieve(cls.catalog_config().url, cls.catalog_config().original_filename)
            except Exception:
                raise Exception(
                    "No input catalog available. Cannot download it too. Put AstDys allnum.cat or allnum.csv in the cache directory!"
                )
            cls.log("Successfully downloaded. Continue working...")

        cat = cls.transform_astdys_catalog()
        cat.to_csv(cls.catalog_full_filename(), index=False)

    @classmethod
    def transform_astdys_catalog(cls):
        catalog = pd.read_csv(
            cls.astdys_full_filename(),
            sep="\\s+",
            header=None,
            skiprows=cls.catalog_config().skip_rows,
            names=cls.catalog_config().columns,
            index_col=False,
        )
        catalog = catalog.replace("'", '', regex=True)
        columns_to_drop = [col for col in catalog.columns if col.startswith('del_')]
        catalog.drop(columns=columns_to_drop, inplace=True)

        for col in cls.catalog_config().degree_columns:
            catalog[col] = catalog[col].map(lambda x: float(x) * np.pi / 180)

        if 'epoch' in catalog.columns:
            columns_except_epoch = [col for col in catalog.columns if col != 'epoch']
            new_column_order = columns_except_epoch + ['epoch']
            catalog = catalog[new_column_order]

        return catalog
