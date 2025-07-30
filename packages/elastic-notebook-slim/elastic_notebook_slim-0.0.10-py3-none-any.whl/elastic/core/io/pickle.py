#/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dill
import pickle

import pandas as pd
# import polars as pl
import inspect, os
from scipy import sparse
import time
import seaborn
import networkx
import matplotlib.pyplot as plt
import types
import mmap
import hashlib

def is_picklable_fast(obj):
    if type(obj) in {types.GeneratorType, mmap.mmap, hashlib.sha256}:
        return False
    return True

def is_picklable(obj):
    """
        Checks whether an object is pickleable.
    """
    if is_exception(obj) or inspect.ismodule(obj):
        return True
    try:
        # This function can crash.
        return _is_picklable_dill(obj)
    except Exception:
        try:
            # Double check with function from pickle module
            return _is_picklable_raw(obj)
        except Exception:
            return False


def is_exception(obj):
    """
        List of objects which _is_picklable_dill returns false (or crashes) but are picklable.
    """
    if hasattr(obj, '__module__') and getattr(obj, '__module__', None).split(".")[0] in {plt.__name__, seaborn.__name__, networkx.__name__, pd.__name__}:
        return True
    exceptions = [pd.core.frame.DataFrame, sparse.csr.csr_matrix]
    return type(obj) in exceptions


def _is_picklable_raw(obj):
    try:
        # dumps can be slow for large objects that can be pickled
        pickle.dumps(obj)
    except Exception:
        return False
    return True


def _is_picklable_dill(obj):
    # compared to _is_picklable_raw, this may be faster
    # however, dill's correctness is worrying because
    #   it currently considers Pandas DataFrame as not
    #   picklable, which is not true
    return dill.pickles(obj)
