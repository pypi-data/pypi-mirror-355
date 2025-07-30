# File generated with docstub

from typing import Any

import numpy as np
import xarray
import xarray as xr
from _typeshed import Incomplete
from xarray import DataTree, open_datatree

from arviz_base.base import dict_to_dataset

__all__ = [
    "convert_to_datatree",
    "convert_to_dataset",
]

def convert_to_datatree(obj: Incomplete, **kwargs: Incomplete) -> xarray.DataTree: ...
def convert_to_dataset(
    obj: Any, *, group: str = ..., **kwargs: dict
) -> xarray.Dataset: ...
