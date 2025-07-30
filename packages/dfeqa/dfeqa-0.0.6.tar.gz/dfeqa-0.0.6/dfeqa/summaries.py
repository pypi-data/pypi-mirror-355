import warnings
from enum import Enum
from typing import Union

import matplotlib.pyplot as plt
import pandas as pd
import regex
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from .datastructures import DataFrame

_pat1 = regex.compile(r'\{\{([^\{\}\|]*)\}\}')
_pat3 = regex.compile(r'{{((?:[^<>={}!]|{{(?1)}})+)'
                        r'(\<\=|\>\=|\!\=|\<|\=|\>)'
                        r'((?:[^|{}]|{{(?3)}})+)\|'
                        r'((?:[^{}|]++|{(?!{)|}(?!})|(?<=\\)\||{{(?4)}}|(?0))*)\|'
                        r'((?:[^{}]++|{(?!{)|}(?=})|{{(?5)}}|(?0))*)}}')

class Constants(Enum):
    SERIES_LABEL = "series"


class summary():
    """General purpose class to provide convenience functions to summarise dataframes,
    series, lists of series or dicts of series"""
    def __init__(self, data: pd.DataFrame|pd.Series|list|tuple|dict, names = None, *args, **kwargs):
        self._data = data
        self._summaries = self._calc_freqs(*args, **kwargs)
        self._names = names

    def _calc_freqs(self, *args, **kwargs):
        _summaries = []
        if isinstance(self._data, pd.Series):
            k = self._data.name or Constants.SERIES_LABEL.value
            s = self._data.rename(None).value_counts(*args, **kwargs).rename(k).fillna(0).astype(int)
            _summaries = [(k, s)]
        elif isinstance(self._data, (list,tuple,dict)):
            if isinstance(self._data, (list,tuple)):
                _summaries = [(x.name or Constants.SERIES_LABEL.value + "_" + str(i),
                    x.rename(None).value_counts(*args, **kwargs).fillna(0).astype(int)
                    .rename(x.name or Constants.SERIES_LABEL.value + "_" + str(i)))
                    for i,x in enumerate(self._data)]
            else:
                _summaries = [(k, v.rename(None)
                    .value_counts(*args, **kwargs).rename(k).astype(int))
                    for k,v in self._data.items()]
        else:
            _summaries = [(lbl, x.rename(None).value_counts(*args, **kwargs).rename(lbl))
                for lbl,x in self._data.items()]
        return _summaries

    def set_names(self, names):
        self._names = names
        return self

    def wide_fd(self, select=None, sort_counts=False):
        columns = self._names or [n for (n,x) in self._summaries]
        sumgroups = select or [k for (k,x) in self._summaries]
        d = pd.DataFrame(self._summaries[0][1]) if len(self._summaries)==1 else \
            pd.concat([x for (k,x) in self._summaries if k in sumgroups], axis=1)
        d = d.fillna(0).astype(int).reset_index(drop=False)
        d = DataFrame(_wide_sort(d, offset=1)) if sort_counts else\
            DataFrame(d.sort_values('index')).reset_index(drop=True)
        return d.set_axis(['value'] + columns, axis="columns")

    def long_fd(self, select=None, sort_counts=False):
        return_df = DataFrame(
            self.wide_fd(select=select).melt(id_vars=['value'],
                var_name="group", value_name="count"))
        return return_df.sort_values(['group','count','value'], ascending=[True, False, True])\
            .reset_index(drop=True) if sort_counts else\
            return_df.sort_values(['group','value','count'], ascending=[True, True, False])\
            .reset_index(drop=True)

    def groups_that_contain(self, value = True):
        """List names and sizes of groups containing any records with a value (default=True)"""
        return [{'groupname':lbl, 'value': value, 'count':int(x[value]), 'total': int(x.sum())}
            for (lbl,x) in self._summaries if value in x.index]

def _wide_sort(df: pd.DataFrame, offset:int):
    dummynumber = 0
    dummyname = "__%d" % dummynumber
    columns = df.columns.to_list()
    while dummyname in columns:
        dummynumber += 1
        dummyname = "__%d" % dummynumber
    df = df.assign(**{dummyname: df[columns[1:]].max(axis=1)})
    df = df.sort_values(columns[0],ascending=True).sort_values([dummyname] + columns[1:], ascending=False)
    return df[columns].reset_index(drop=True)


def fd(
    data: pd.DataFrame|pd.Series|list,
    cols: list = None,
    ids: list = None,
    long=False,
    value_columnname=None
    ):
    """frequency distributions - provide a dataframe with cols to create frequencies from or
    a list of Pandas Series
    return long-form summary of freqency distribution of specified columns
    optional ids provides labels for groups in returned data"""

    if cols:
        data = data[cols]
    if isinstance(data, pd.Series) and ids is None:
        ids = ['count'] # to maintain consistent behaviour from pre-v0.0.6
    if long:
        returndata = summary(data).set_names(ids).long_fd()
    else:
        returndata = summary(data).set_names(ids).wide_fd()
    if value_columnname:
        returndata = returndata.rename(columns = {'value': value_columnname})
    return returndata

def freqchart(chartdata:pd.DataFrame, value_col: str, freq_col: str = None, groups:str = None,
        min_range: int|tuple|list = None, max_range: int|tuple|list = None,
        x_rescale: int|list=None):
    """return barchart comparing frequency dists of a number of defined columns
    optionally pass min_range and max_range (integer, list or tuple) for vlines indicating range"""
    warnings.warn("freqchart() is deprecated and will be removed in a future release. Use barchart() instead.",
        DeprecationWarning, stacklevel=2)
    return barchart(chartdata, cats=value_col, values=freq_col, groups=groups,\
        vlines=[(x for x in min_range),(x for x in max_range)],
        x_rescale=x_rescale)

def _drawvlines(p, lines):
    if lines is None:
        return p
    elif not isinstance(lines,(list,tuple)):
        p.axvline(x=lines, color=sns.color_palette()[0])
    elif isinstance(lines,(tuple,list)) and all(isinstance(x,(list,tuple)) for x in lines):
        for line in lines:
            _drawvlines(p, line)
    else:
        x_map = {a.get_text(): i for i,a in enumerate(p.get_xaxis().get_ticklabels())}
        for i,x in enumerate(lines):
            try:
                p.axvline(x=x_map[str(x)], color=sns.color_palette()[i])
            except KeyError:
                print("value for vline is not on x axis")
    return p

def _barchart_from_list_of_series(chartdata, groups):
    names=None
    if groups is not None:
        names = groups
    elif all(x.name for x in chartdata):
        names = [x.name for x in chartdata]
    else:
        names = ["group" + str(x+1) for x in range(len(chartdata))]
    cd = []
    for i,x in enumerate(chartdata):
        y = x.copy()
        y.index = y.index.rename(None)
        y = y.reset_index(drop=False, name="value").assign(group=names[i])
        cd.append(y)
    p = sns.barplot(pd.concat(cd), x='index', y='value', hue='group')
    if all(x['value'].apply(isinstance,args = [int]).all() for x in cd):
        p.yaxis.set_major_locator(MaxNLocator(integer=True))
    return p

def _barchart_from_dataframe_with_values_defined(chartdata, values, groups):
    i='i' if values != 'i' else '_i'
    cols = [groups] if groups else []
    v = values if isinstance(values,list) else [values]
    cols = cols + v
    d = chartdata.copy()[cols].reset_index(drop=False, names=i)
    p = sns.barplot(data = d, x=i, y=values, hue=groups)
    p.yaxis.set_major_locator(MaxNLocator(integer=True))
    return p

def barchart(chartdata:pd.DataFrame | pd.Series ,
        cats: str=None,
        values: str = None,
        groups: str = None,
        xlabel: str=None,
        ylabel: str=None,
        vlines: int|tuple|list = None,
        x_rescale: int|list=None):
    """return barchart comparing frequency dists of a number of defined columns
    optionally pass vlines (integer, list or tuple) for vlines indicating range"""

    p = None
    plt.close("all")
# dataframe with cats and values defined
    if isinstance(chartdata, pd.DataFrame) and cats is not None and values is not None:
        p = sns.barplot(x=cats, y=values, hue = groups,
            data = chartdata
            )
        if chartdata[values].apply(isinstance,args = [int]).all():
            p.yaxis.set_major_locator(MaxNLocator(integer=True))
# dataframe with only values defined
    elif isinstance(chartdata, pd.DataFrame) and values is not None and cats is None and isinstance(values,str):
        p = _barchart_from_dataframe_with_values_defined(chartdata, values, groups)
# dataframe with only cats defined
    elif isinstance(chartdata, pd.DataFrame) and values is None and cats is not None and isinstance(cats,str):
        p = sns.barplot(data=chartdata[cats].value_counts(dropna=False))
        p.yaxis.set_major_locator(MaxNLocator(integer=True))
# pd.Series
    elif isinstance(chartdata, pd.Series):
        p = sns.barplot(chartdata)
        p.yaxis.set_major_locator(MaxNLocator(integer=True))
# list of series
    elif isinstance(chartdata, list) and all(isinstance(x, pd.Series) for x in chartdata):
        p = _barchart_from_list_of_series(chartdata, groups)
    else:
        raise RuntimeError('unable to generate chart from given parameters')

    p = _drawvlines(p,vlines)

    if x_rescale:
        assert isinstance(x_rescale, (int, list))
        ticks = p.get_xticks()
        if isinstance(x_rescale, int):
            p.set_xticks([x for i,x in enumerate(ticks) if i % x_rescale == 0])
        elif isinstance(x_rescale, list):
            p.set_xticks([ticks[x] for x in x_rescale])

    p.set_xlabel(xlabel)
    p.set_ylabel(ylabel)

    return p


def parse_text (in_text, data: Union[tuple, dict]) -> str:
    """pattern 1 returns the value stored in data store.
    pattern 3 is split into 3 parts. Part 2 (a string) is returned if
    part 1 is true, else part 3.
    Part 1 in pattern 3 can be made up of a string, data store key and
    one of </<=/=/>=/>."""

    def _extract_from(key, data: Union[tuple, dict]) -> str:
        """returns first find of key from dictionary or tuple of dictionaries"""
        if not isinstance(data, tuple):
            data = (data,)
        found=None
        for dataset in data:
            assert isinstance(dataset, dict)
            if key in dataset:
                found = str(dataset[key])
                break
        else:
            found = str(key)
        return found

    def _f1(match_obj):
        _s = match_obj.group(1)
        return _extract_from(_s, data)

    def _f3(match_obj):
        """return a string from a 'f3' format string"""
        _s = match_obj.group(0)
        _op1 = match_obj.group(1).strip()
        _operator = match_obj.group(2).strip()
        assert _operator in ["<","<=","=",">=",">", "!="], \
            "operator in text template not supported"
        _op2 = match_obj.group(3).strip()
        operand1 = _extract_from(_op1,data)
        operand2 = _extract_from(_op2,data)
        operations = {
            "=" : lambda _x, _y: _x == _y,
            "<=" : lambda _x, _y: _x <= _y,
            ">=" : lambda _x, _y: _x >= _y,
            "<" : lambda _x, _y: _x < _y,
            ">" : lambda _x, _y: _x > _y,
            "!=" : lambda _x, _y: _x != _y
        }
        return regex.sub(_pat3, _f3, str(match_obj.group(4))) \
            if operations[_operator](operand1, operand2) \
            else regex.sub(_pat3, _f3, match_obj.group(5))

    returntext = regex.sub(_pat3, _f3, in_text)
    return regex.sub(_pat1, _f1, returntext)


def status_summary(objectives: list[str], rags: list[str], down=False):
    """return a formatted list of statements with RAG statuses;
    specify down=true to list verically, or leave the default to list across the page
    rags (statuses) can be None, red, amber, green or grey"""
    assert len(objectives) == len(rags)
    df = pd.DataFrame(objectives)
    if not down:
        df = df.T
    s = df.style.hide().hide(axis=1)

    s.set_table_styles([
        {'selector': 'td', 'props': 'text-align: center; border-radius: 10px; width: {}%;'\
            .format(str(int(100 / len(objectives))))},
        {'selector': '.grey', 'props': 'background-color:rgb(205, 205, 205);'},
        {'selector': '.green', 'props': 'background-color: #e6ffe6;'},
        {'selector': '.amber', 'props': 'background-color:#ffdfb3;'},
        {'selector': '.red', 'props': 'background-color: #ffe6e6;'},
    ], overwrite=False)
    cell_colour = pd.DataFrame(rags)
    if not down:
        cell_colour = cell_colour.T
    return s.set_td_classes(cell_colour)
