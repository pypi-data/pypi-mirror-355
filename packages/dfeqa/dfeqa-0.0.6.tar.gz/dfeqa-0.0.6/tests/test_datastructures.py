from datetime import date, datetime

import pandas as pd

from dfeqa.datastructures import Constants, Series


def test_minmax_strings(List_Of_Series):
    assert Series(List_Of_Series[0]).minmax() == \
        {
            'name': "forename",
            'type': "string",
            'n_unique': 10,
            'min': 4,
            'max': 9,
            'n_null': 0,
            'n_not_null': 10,
            'errors': None,
            'elements': List_Of_Series[0].tolist(),
        }

def test_minmax_strings_with_more_values_than_factor_threshold(List_Of_Series):
    assert Series(pd.concat([List_Of_Series[0] + '_' + suffix for suffix in 'abc'])).minmax() == \
        {
            'name': "forename",
            'type': "string",
            'n_unique': 30,
            'min': 6,
            'max': 11,
            'n_null': 0,
            'n_not_null': 30,
            'errors': None,
            'elements': 'John_aSimLeRydAlfrGgsctEZWb',
        }

def test_minmax_dates(List_of_Dates_as_Strings):
    s = Series(pd.to_datetime(List_of_Dates_as_Strings, format="%d%m%Y"), name="testdates")
    assert s.minmax() == {
            'name': "testdates",
            'type': "date",
            'n_unique': 672,
            'min': date.fromisoformat('2000-01-01'),
            'max': date.fromisoformat('2001-12-28'),
            'n_null': 0,
            'n_not_null': 672,
            'errors': None,
            'elements': ['(672 unique values)'] \
                + [datetime.strptime(x, '%d%m%Y') for x in List_of_Dates_as_Strings]\
                [:Constants.FACTOR_THRESH.value] + ['...']
    }

def test_minmax_integers():
    assert Series(range(1,101), name="testintegers").minmax() == {
            'name': "testintegers",
            'type': "numeric",
            'n_unique': 100,
            'min': 1,
            'max': 100,
            'n_null': 0,
            'n_not_null': 100,
            'errors': None,
            'elements': ['(100 unique values)'] + [x for x in range(1,101)][:Constants.FACTOR_THRESH.value] + ['...'],
    }

def test_minmax_floats():
    assert Series([x/100 for x in range(-200, 201, 33)], name="testfloats").minmax() == {
            'name': "testfloats",
            'type': "numeric",
            'n_unique': 13,
            'min': -2.0,
            'max': 1.96,
            'n_null': 0,
            'n_not_null': 13,
            'errors': None,
            'elements': ['(13 unique values)'] + [x/100 for x in range(-200, 201, 33)],
    }

def test_minmax_dates_as_strings(List_of_Dates_as_Strings):
    assert Series(List_of_Dates_as_Strings, name="datestrings").minmax(stype="date", format="%d%m%Y") == {
            'name': "datestrings",
            'type': "string(date)",
            'n_unique': 672,
            'min': "01012000",
            'max': "28122001",
            'n_null': 0,
            'n_not_null': 672,
            'errors': None,
            'elements': ["01012000 to 28122001"],
        }

def test_minmax_dates_as_strings_with_dayfirst(List_of_Dates_as_Strings):
    assert Series([datetime.strptime(x, '%d%m%Y').strftime('%d/%m/%Y') for x in List_of_Dates_as_Strings]
        , name="datestrings").minmax(stype="date", dayfirst=True) == {
            'name': "datestrings",
            'type': "string(date)",
            'n_unique': 672,
            'min': "01/01/2000",
            'max': "28/12/2001",
            'n_null': 0,
            'n_not_null': 672,
            'errors': 0,
            'elements': ["01/01/2000 to 28/12/2001"],
        }

def test_minmax_dates_as_strings_without_format(List_of_Dates_as_Strings):
    assert Series([datetime.strptime(x, '%d%m%Y').strftime('%m/%d/%Y') for x in List_of_Dates_as_Strings]
        , name="datestrings").minmax(stype="date") == {
            'name': "datestrings",
            'type': "string(date)",
            'n_unique': 672,
            'min': "01/01/2000",
            'max': "12/28/2001",
            'n_null': 0,
            'n_not_null': 672,
            'errors': 0,
            'elements': ["01/01/2000 to 12/28/2001"],
        }

def test_minmax_dates_as_strings_using_dayfirst(List_of_Dates_as_Strings):
    assert Series([datetime.strptime(x, '%d%m%Y').strftime('%d/%m/%Y') for x in List_of_Dates_as_Strings]
        , name="datestrings").minmax(stype="date", dayfirst=True) == {
            'name': "datestrings",
            'type': "string(date)",
            'n_unique': 672,
            'min': "01/01/2000",
            'max': "28/12/2001",
            'n_null': 0,
            'n_not_null': 672,
            'errors': 0,
            'elements': ["01/01/2000 to 28/12/2001"],
        }

def test_minmax_numbers_as_strings():
    assert Series([str(x/100) for x in range(-200, 201, 33)], name="testfloats").minmax() == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 13,
            'min': -2.0,
            'max': 1.96,
            'n_null': 0,
            'n_not_null': 13,
            'errors': None,
            'elements': ['-2.0 to 1.96'],
    }

def test_minmax_numbers_as_strings_with_stype_and_null_and_Empty():
    assert pd.concat([Series([str(x/100) for x in range(-200, 201, 33)]),
        Series([None,''])]).rename("testfloats").minmax(stype="numeric") == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 14,
            'min': -2.0,
            'max': 1.96,
            'n_null': 1,
            'n_not_null': 14,
            'errors': None,
            'elements': ["-2.0 to 1.96", None, ''],
    }

def test_minmax_strings_with_stype(List_Of_Series):
    assert Series(List_Of_Series[0]).minmax(stype="text") == \
        {
            'name': "forename",
            'type': "string",
            'n_unique': 10,
            'min': 4,
            'max': 9,
            'n_null': 0,
            'n_not_null': 10,
            'errors': None,
            'elements': List_Of_Series[0].tolist(),
        }

def test_minmax_strings_with_null(List_Of_Series):
    assert pd.concat([Series(List_Of_Series[0]),Series([None])]).rename("forename").minmax(stype="text") == \
        {
            'name': 'forename',
            'type': 'string',
            'n_unique': 10,
            'min': 0,
            'max': 9,
            'errors': None,
            'elements': List_Of_Series[0].tolist() + [''],
            'n_null': 1,
            'n_not_null': 10,
        }


# + more numbers than non-numbers
# + less numbers than non-numbers
# + less non-numbers than threshold
# + more non-numbers than threshold
# user-override where more non-numbers than numbers
# more numbers than non-numbers, but not more than nulls+non-numbers

def test_minmax_numbers_as_strings_and_less_non_numbers():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)])[:20],
        Series(["ABC%s" % x for x in range(10)])])\
                .rename("testfloats").minmax() == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 30,
            'min': -20.0,
            'max': -13.73,
            'n_null': 0,
            'n_not_null': 30,
            'errors': None,
            'elements': ['-20.0 to -13.73',
                'ABC0', 'ABC1', 'ABC2', 'ABC3',
                'ABC4', 'ABC5', 'ABC6', 'ABC7',
                'ABC8', 'ABC9'],
    }

def test_minmax_numbers_as_strings_and_more_non_numbers():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)])[:20],
        Series(["ABC%s" % x for x in range(21)])])\
                .rename("testfloats").minmax() == {
            'name': "testfloats",
            'type': "string",
            'n_unique': 41,
            'min': 4,
            'max': 6,
            'n_null': 0,
            'n_not_null': 41,
            'errors': None,
            'elements': '-20.19673485ABC',
    }

def test_minmax_numbers_as_strings_and_more_non_numbers_with_override():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)])[:5],
        Series(["ABC%s" % x for x in range(6)])])\
                .rename("testfloats").minmax(stype='numeric') == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 11,
            'min': -20.0,
            'max': -18.68,
            'n_null': 0,
            'n_not_null': 11,
            'errors': None,
            'elements': ['-20.0 to -18.68',
                'ABC0',
                'ABC1',
                'ABC2',
                'ABC3',
                'ABC4',
                'ABC5']
    }

def test_minmax_numbers_as_strings_and_less_than_threshold_non_numbers():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)]),
        Series(["ABC%s" % x for x in range(Constants.FACTOR_THRESH.value)])])\
                .rename("testfloats").minmax() == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 147,
            'min': -20.0,
            'max': 19.93,
            'n_null': 0,
            'n_not_null': 147,
            'errors': None,
            'elements': ['-20.0 to 19.93'
                , 'ABC0', 'ABC1', 'ABC2', 'ABC3', 'ABC4'
                , 'ABC5', 'ABC6', 'ABC7', 'ABC8', 'ABC9'
                , 'ABC10', 'ABC11', 'ABC12', 'ABC13', 'ABC14'
                , 'ABC15', 'ABC16', 'ABC17', 'ABC18', 'ABC19'
                , 'ABC20', 'ABC21', 'ABC22', 'ABC23', 'ABC24']
    }

def test_minmax_numbers_as_strings_and_more_than_threshold_non_numbers():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)]),
        Series(["ABC%s" % x for x in range(Constants.FACTOR_THRESH.value+1)])])\
                .rename("testfloats").minmax() == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 148,
            'min': -20.0,
            'max': 19.93,
            'n_null': 0,
            'n_not_null': 148,
            'errors': None,
            'elements': ['-20.0 to 19.93', 'ABC0123456789']
    }

def test_minmax_numbers_as_strings_and_more_nulls_than_numbers_more_than_notnumbers():
    assert pd.concat([Series([str(x/100) for x in range(-2000, 2001, 33)])[:6],
        Series(["ABC%s" % x for x in range(5)]),
        Series([None for x in range(7)])])\
                .rename("testfloats").minmax() == {
            'name': "testfloats",
            'type': "string(number)",
            'n_unique': 11,
            'min': -20.0,
            'max': -18.35,
            'n_null': 7,
            'n_not_null': 11,
            'errors': None,
            'elements': ['-20.0 to -18.35', 'ABC0', 'ABC1', 'ABC2', 'ABC3', 'ABC4', None]
    }

def test_minmax_dates_as_strings_and_less_non_dates(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:20],
        Series(["ABC%s" % x for x in range(10)])
    ]).rename("testdates")

    assert combined_series.minmax(stype="date", format="%d%m%Y") == {
        'name': "testdates",
        'type': "string(date)",
        'n_unique': 30,
        'min': '01012000',
        'max': '20012000',
        'n_null': 0,
        'n_not_null': 30,
        'errors': None,
        'elements': ['01012000 to 20012000'] + ["ABC%s" % x for x in range(10)],
    }

def test_minmax_dates_as_strings_and_more_non_dates(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:20],
        Series(["ABC%s" % x for x in range(21)])
    ]).rename("testdates")

    assert combined_series.minmax() == {
            'name': "testdates",
            'type': "string",
            'n_unique': 41,
            'min': 4,
            'max': 8,
            'n_null': 0,
            'n_not_null': 41,
            'errors': None,
            'elements': '0123456789ABC',
    }

def test_minmax_dates_as_strings_and_more_non_dates_with_override(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:20],
        Series(["ABC%s" % x for x in range(21)])
    ]).rename("testdates")

    assert combined_series.minmax(stype='date', format="%d%m%Y") == {
            'name': "testdates",
            'type': "string(date)",
            'n_unique': 41,
            'min': '01012000',
            'max': '20012000',
            'n_null': 0,
            'n_not_null': 41,
            'errors': None,
            'elements': ['01012000 to 20012000'] + ["ABC%s" % x for x in range(21)]
    }

def test_minmax_dates_as_strings_and_less_than_threshold_non_dates(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:20],
        Series(["ABC%s" % x for x in range(Constants.FACTOR_THRESH.value)])
    ]).rename("testdates")

    assert combined_series.minmax(stype="date", format="%d%m%Y") == {
            'name': "testdates",
            'type': "string(date)",
            'n_unique': 20 + Constants.FACTOR_THRESH.value,
            'min': '01012000',
            'max': '20012000',
            'n_null': 0,
            'n_not_null': 20 + Constants.FACTOR_THRESH.value,
            'errors': None,
            'elements': ['01012000 to 20012000'
                , 'ABC0', 'ABC1', 'ABC2', 'ABC3', 'ABC4'
                , 'ABC5', 'ABC6', 'ABC7', 'ABC8', 'ABC9'
                , 'ABC10', 'ABC11', 'ABC12', 'ABC13', 'ABC14'
                , 'ABC15', 'ABC16', 'ABC17', 'ABC18', 'ABC19'
                , 'ABC20', 'ABC21', 'ABC22', 'ABC23', 'ABC24']
    }

def test_minmax_dates_as_strings_and_more_than_threshold_non_dates(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:20],
        Series(["ABC%s" % x for x in range(Constants.FACTOR_THRESH.value + 1)])
    ]).rename("testdates")

    assert combined_series.minmax(stype="date", format="%d%m%Y") == {
            'name': "testdates",
            'type': "string(date)",
            'n_unique': 20 + Constants.FACTOR_THRESH.value + 1,
            'min': '01012000',
            'max': '20012000',
            'n_null': 0,
            'n_not_null': 20 + Constants.FACTOR_THRESH.value + 1,
            'errors': None,
            'elements': ['01012000 to 20012000', '0123456789ABC']
    }

def test_minmax_dates_as_strings_and_more_nulls_than_numbers_more_than_notdates(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(List_of_Dates_as_Strings)[:6],
        Series(["ABC%s" % x for x in range(5)]),
        Series([None for x in range(7)])
    ]).rename("testdates")

    assert combined_series.minmax(stype="date",format="%d%m%Y") == {
            'name': "testdates",
            'type': "string(date)",
            'n_unique': 11,
            'min': '01012000',
            'max': '06012000',
            'n_null': 7,
            'n_not_null': 11,
            'errors': None,
            'elements': ['01012000 to 06012000'
                , 'ABC0', 'ABC1', 'ABC2', 'ABC3', 'ABC4', None]
    }

def test_minmax_specified_dates_but_none_in_data():
    assert Series(["ABC%s" % x for x in range(5)], name="testdates").minmax(stype="date") == {
            'name': "testdates",
            'type': "string",
            'n_unique': 5,
            'min': 4,
            'max': 4,
            'n_null': 0,
            'n_not_null': 5,
            'errors': None,
            'elements': ['ABC0', 'ABC1', 'ABC2', 'ABC3', 'ABC4']
    }

def test_minmax_mixture_of_types(List_of_Dates_as_Strings):
    combined_series = pd.concat([
        Series(pd.to_datetime(List_of_Dates_as_Strings, format="%d%m%Y")),
        Series([x for x in range(20)]),
        Series([x for x in "abcdefghijklmnopqrstuvwxyz"])
    ]).rename("combined_series")
    assert combined_series.minmax() == {
        'name': 'combined_series',
        'type': 'string',
        'n_unique': 718,
        'min': 1,
        'max': 19,
        'errors': None,
        'elements': '20-1 :3456789abcdefghijklmnopqrstuvwxyz',
        'n_null': 0,
        'n_not_null': 718
    }



