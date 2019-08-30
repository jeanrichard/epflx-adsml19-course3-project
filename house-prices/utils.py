# -*- coding: utf-8 -*-
"""\
Miscellaneous utilities for this project.
"""

# Standard library:
import collections
import functools
import json
import typing as T
import warnings

# 3rd party:
import numpy as np
import pandas as pd

#
# Utilities related to the definitions of the variables
#

# The attributes of a variable:
Attrs = T.Dict[str, T.Any]


def load_variables(path: str) -> T.Dict[str, Attrs]:
    """\
    Loads the definitions of the variables from a JSON file.
    """
    
    def make_pair(definition):
        name = definition['name']
        attrs = {
            'kind': definition['kind']
        }
        if 'values' in definition:
            attrs['values'] = definition['values']
        return (name, attrs)
    
    with open(path, 'r') as f:
        definitions = json.load(f)
        pairs = [make_pair(definition) for definition in definitions]
        return collections.OrderedDict(pairs)       


def is_qualitative(attrs: Attrs) -> bool:
    """\
    Returns ``True`` if the given attributes describe a qualitative variable; returns ``False``
    otherwise.
    """
    return attrs['kind'] in ['Nominal', 'Ordinal']


def is_quantitative(attrs: Attrs) -> bool:
    """\
    Returns ``True`` if the given attributes describe a quantitative variable; returns ``False``
    otherwise.
    """
    return attrs['kind'] in ['Discrete', 'Continuous']


#
# Utilities related to data cleaning
#


def count_null(series: pd.Series) -> int:
    """\
    Returns the number of null/na values in a series.
    """
    return series.isna().sum()


def count_invalid(series: pd.Series, values: T.List[str]) -> int:
    """\
    Returns the number of invalid values found in a series.
    """
    return (~series.isin(values)).sum()


def get_unique_invalid(series: pd.Series, values: T.List[str]) -> np.ndarray:
    """\
    Returns the unique invalid values found in a series.
    """
    invalid = series.loc[~series.isin(values)]
    return invalid.unique()


def replace_invalid(series: pd.Series,
                    values: T.List[str],
                    replacements: T.Mapping[str, str]) -> pd.Series:
    """\
    Replaces invalid values found in a series.
    """
    invalid = series.loc[~series.isin(values)]
    replaced = invalid.map(replacements)
    series.loc[replaced.index] = replaced
    return series


def mode(series: pd.Series, default: T.Any=None):
    """\
    Ignores null/na values in a series and computes the mode. If the mode is not defined (i.e. 
    the series contains only null/na values), returns ``default``.
    """
    mode = series.mode(dropna=True)
    return default if mode.empty else mode.iloc[0]


def median(series: pd.Series, default: float=np.nan):
    """\
    Ignores null/na values in a series and computes the median. If the median is not defined (i.e.
    the series contains only null/na values), returns ``default``.
    """
    with warnings.catch_warnings():
        # RuntimeWarning: Mean of empty slice
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        median = series.median(skipna=True)
    return default if np.isnan(median) else median


def fillna_with_mode_by(df: pd.DataFrame, name: str, by: str) -> pd.DataFrame:
    """\
    Fills null/na values in the ``df[name]`` column. Groups the ``df[name]`` values into subsets
    using the ``df[by]`` values. If the mode is defined on a given subset, uses it to fill null/na
    values. Otherwise, uses the mode overall.
    """
    mode_overall = mode(df[name], None)
    assert mode_overall is not None
    df[name] = df.groupby(by=by)[name].transform(
        lambda series: series.fillna(mode(series, mode_overall)))
    return df


def fillna_with_median_by(df: pd.DataFrame, name: str, by: str) -> pd.DataFrame:
    """\
    Fills null/na values in the ``df[name]`` column. Groups the ``df[name]`` values into subsets
    using the ``df[by]`` values. If the median is defined on a given subset, uses it to fill null/na
    values. Otherwise, uses the median overall.
    """
    median_overall = median(df[name], np.nan)
    assert not np.isnan(median_overall)
    df[name] = df.groupby(by=by)[name].transform(
        lambda series: series.fillna(median(series, median_overall)))
    return df


def get_mode_by(df: pd.DataFrame, name: str, by: str) -> pd.Series:
    """\
    Returns a series, indexed by unique values of ``df[by]``. Groups the ``df[name]`` values into
    subsets using the ``df[by]`` values. If the mode is defined on a given subset, uses it to
    populate the series. Otherwise, uses the mode overall.
    """
    mode_overall = mode(df[name], None)
    assert mode_overall is not None
    mode_by = df.groupby(by=by)[name].agg(lambda series: mode(series, mode_overall))
    return mode_by


def get_median_by(df: pd.DataFrame, name: str, by: str) -> pd.Series:
    """\
    Returns a series, indexed by unique values of ``df[by]``. Groups the ``df[name]`` values into
    subsets using the ``df[by]`` values. If the median is defined on a given subset, uses it to
    populate the series. Otherwise, uses the median overall.
    """
    median_overall = median(df[name], np.nan)
    assert not np.isnan(median_overall)
    median_by = df.groupby(by=by)[name].agg(lambda series: median(series, median_overall))
    return median_by


def categorize(df: pd.DataFrame,
               rules: T.Tuple[str, str, str, T.Callable[[T.Any], bool]]) -> T.Tuple[pd.DataFrame, pd.DataFrame]:
    """\
    Categorizes values according to rules. Each rule is of the form ``(column-name, 
    label-if-predicate, label-if-not-predicate, predicate)``.
    """
    data = {}
    columns = []
    for name, label, notlabel, predicate in rules:
        columns.append(name)
        series = (df[name]
                  .mask(df[name].isna(), 'null')
                  .mask(df[name].notna() & predicate(df[name]), label)
                  .mask(df[name].notna() & ~predicate(df[name]), notlabel)
                 )
        data[name] = series
    
    # Add a column to count:
    columns_plus = columns + ['Count']
    data['Count'] = 1
    
    # The data-frame with the categorized values:
    df_category = pd.DataFrame(data=data, columns=columns_plus)
    
    # The data-frame with the different cases:
    df_case = df_category.groupby(by=columns).agg({'Count': 'sum'}).reset_index(drop=False)
    
    return df_category, df_case


def mask_for_case(df_category: pd.DataFrame, df_case: pd.DataFrame, case_label: int):
    """\
    Returns a mask for the rows in the original data-frame that correspond to a given case.
    """
    case = df_case.loc[case_label, :]
    masks = [
        df_category[name] == value
        for name, value in case.iteritems() if name != 'Count'
    ]
    mask = functools.reduce(lambda acc, cur: acc & cur, masks)
    return mask
