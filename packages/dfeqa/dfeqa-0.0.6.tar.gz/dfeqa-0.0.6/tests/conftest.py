import os

import pandas as pd
import pytest


def pytest_addoption(parser):
    parser.addoption('--slow', action='store_true', default=False,
                      help='Also run slow tests')

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--slow"):
        skipper = pytest.mark.skip(reason="Only run when --slow is given")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skipper)

@pytest.fixture
def List_Of_Series():
    return [
        pd.Series([
            'John', 'Simon', 'Lenina', 'Raymond', 'Alfredo',
            'George', 'Associate', 'Edgar', 'Zachary', 'William'
            ], name='forename'),
        pd.Series([
            'Spartan', 'Phoenix', 'Huxley', 'Cocteau', 'Garcia',
            'Earle', 'Bob', 'Friendly', 'Lamb', 'Smithers'
            ], name='surname')
    ]

@pytest.fixture
def People_As_Frame(List_Of_Series):
    d = pd.concat(List_Of_Series, axis=1)
    d['fname_len']=d['forename'].str.len()
    return d

@pytest.fixture
def Wide_Frame_Length_Summary(List_Of_Series):
    return pd.concat(
        [x.str.len().value_counts(dropna=False).rename(x.name)\
            for x in List_Of_Series], axis=1
            ).fillna(0).astype(int).sort_index().reset_index(drop=False).rename(columns={'index':'value'})

@pytest.fixture
def Long_Frame_Length_Summary(Wide_Frame_Length_Summary):
    return Wide_Frame_Length_Summary.melt(id_vars=['value'], value_name='count', var_name='group')

@pytest.fixture
def Long_Frame_Name_Freqs(List_Of_Series):
    return pd.concat(
        [x.value_counts(dropna=False).reset_index(drop=False)\
            .rename(columns={x.name:'value'}).assign(group=x.name)
            for x in List_Of_Series]
    )

@pytest.fixture
def Wide_Frame_Name_Freqs(List_Of_Series):
    return pd.concat(
        [x.value_counts(dropna=False).rename(x.name)\
            for x in List_Of_Series], axis=1
    ).fillna(0).astype(int).sort_index().reset_index(drop=False).rename(columns={'index':'value'})

@pytest.fixture
def Wide_Frame_Name_Freqs_Max_Sort(List_Of_Series):
    d = pd.concat(
        [x.value_counts(dropna=False).sort_index().rename(x.name)\
            for x in List_Of_Series], axis=1
    ).fillna(0).astype(int)
    return d.assign(max=d[['forename','surname']]\
        .max(axis=1))\
        .sort_values(['max','forename','surname'], ascending=False)\
        .reset_index(drop=False).rename(columns={'index':'value'})\
        .drop(columns='max')

@pytest.fixture
def PDR_Conn():
    return os.environ['default_conn']

@pytest.fixture
def Series_of_Dates():
    return pd.Series([pd.to_datetime("/".join([str(d + 1),str(m + 1),str(2000 + y)]),
    dayfirst=True, yearfirst=False) for y in range(2) for m in range(12) for d in range(28)])

@pytest.fixture
def List_of_Dates_as_Strings():
    return ["%02d%02d%04d" % (d, m, y)
        for y in range(2000,2002)
        for m in range(1,13)
        for d in range(1,29)]
