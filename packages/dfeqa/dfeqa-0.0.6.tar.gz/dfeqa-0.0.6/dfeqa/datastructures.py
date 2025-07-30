import warnings
from collections import Counter
from enum import Enum
from inspect import getfullargspec

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime_64
from pandas.api.types import is_timedelta64_dtype as is_timedelta_64
from pandas.tseries.api import guess_datetime_format


class Constants(Enum):
    USER_SNUM = "numeric"
    USER_SDATE = "date"
    USER_STEXT = "text"
    NUMERIC_TYPE = "numeric"
    TDELTA_TYPE = "timedelta"
    DATE_TYPE = "date"
    SDATE_TYPE = "string(date)"
    SNUM_TYPE = "string(number)"
    STR_TYPE = "string"
    CAT_TYPE = "category"
    UNKNOWN_TYPE = '?'
    NUMERIC_KIND = "iufc"
    IS_NUMBER_REX = r"^-?(0|([1-9]\d*))(\.\d+)*$"
    PROP_DATES_THRESH = 0.5
    PROP_NUMBERS_THRESH = 0.5
    FACTOR_THRESH = 25
    UNIQUE_RANGE = 500 # size of range at start of data to summarise unique values


class DataFrame(pd.DataFrame):
    """Pandas dataframe with some extras"""
    @property
    def _constructor(self):
        return DataFrame

    @property
    def _constructor_sliced(self):
        return Series

    def set_header(self, colnames:list):
        return self.set_axis(colnames, axis="columns") if colnames else self

    def minmax(self, **kwargs):
        return DataFrame([x.minmax(**kwargs[n]) if n in kwargs else x.minmax() for n,x in self.items()])


class Series(pd.Series):
    @property
    def _constructor(self):
        return Series

    @property
    def _constructor_expanddim(self):
        return DataFrame

    def _get_strings_as_dates(self, **kwargs):
        d = None
        try:
            warnings.filterwarnings("error")
            d = pd.to_datetime(self.fillna('').astype(str), errors='coerce', **kwargs)
            warnings.resetwarnings()
        except Exception:
            print("Unable to parse strings as dates - fallback to strings") # should be logged when logging implemented
        return d

    def _guess_date_format(self, **kwargs):
        """guesses what the date format is if the series is made up of strings
        accepts:
            dayfirst=False
        returns dict:
            format: date format that occurs most frequently
            errors: number of cases not meeting this format
            None:  if less than PROP_DATES_THRESH is a consistent date format"""
        passargs = [x for x in kwargs.keys() if x in getfullargspec(guess_datetime_format).args]
        dateformats = self.astype(str).apply(guess_datetime_format, args=passargs).value_counts(dropna=False)
        n_matched_format = dateformats.max().item()
        returnvalue = None
        if dateformats.idxmax() is not None and n_matched_format > \
                (self.shape[0] * Constants.PROP_DATES_THRESH.value):
            dateformat = dateformats.idxmax()
            returnvalue = {'format': dateformat,
                'errors': self.shape[0] - n_matched_format}
        return returnvalue

    def _flag_numbers_as_str(self):
        """returns a series of boolean indicating whether values are numbers"""
        return self.astype(str).replace(['','None'],None).str\
            .fullmatch(Constants.IS_NUMBER_REX.value, na=False)

    def _process_text_as_date(self, **kwargs):
        """analyse the text series as dates"""
        dates = self._get_strings_as_dates(**kwargs)
        if dates is not None:
            not_dates = self[dates.isna()]
            format = kwargs.get('format')
            dateformat={'errors': None}
            if format is None:
                dateformat = self._guess_date_format(**kwargs)
                format = dateformat['format'] if dateformat is not None else None
            min = dates.min().strftime(format)
            max = dates.max().strftime(format)
            n_unique_not_dates = not_dates.unique().shape[0]
            unique_values = ["%s to %s" % (str(min), str(max))]
            if n_unique_not_dates <= Constants.FACTOR_THRESH.value:
                unique_values += not_dates.unique().tolist()
            else:
                char_count = Counter()
                self_as_str = self.fillna('').astype(str)
                for x in self_as_str.to_numpy():
                    char_count.update(x)
                unique_values.append("".join(char_count.keys()))
            return {
                'min': min,
                'max': max,
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'errors': dateformat['errors'],
                'type': Constants.SDATE_TYPE.value,
                'elements': unique_values
            }
        else:
            return None

    def _process_text_as_number(self, number_filter=None):
        if number_filter is None:
            number_filter = self._flag_numbers_as_str()
        only_numbers = self[number_filter]
        try:
            s_numbers=pd.to_numeric(only_numbers)
        except Exception as e:
            raise RuntimeError("Error in converting to number in column: %s" % self.name) from e
        min = s_numbers.min().item()
        max = s_numbers.max().item()
        if (~number_filter).sum() > 0:
            not_numbers = self[~number_filter]
        else:
            not_numbers = pd.Series()
        n_unique_not_numbers = not_numbers.unique().shape[0]
        unique_values = ["%s to %s" % (str(min), str(max))]
        if n_unique_not_numbers <= Constants.FACTOR_THRESH.value:
            unique_values += not_numbers.unique().tolist()
        else:
            char_count = Counter()
            for x in not_numbers.fillna('').astype(str).to_numpy():
                char_count.update(x)
            unique_values.append("".join(char_count.keys()))
        return {
            'min': min,
            'max': max,
            'type': Constants.SNUM_TYPE.value,
            'n_null': self.isna().sum().item(),
            'n_not_null': self.notna().sum().item(),
            'elements': unique_values
        }

    def _process_as_text(self):
            char_count = Counter()
            self_as_str = self.fillna('').astype(str)
            unique_values = None
            n_unique = self_as_str.nunique()
            if n_unique <= Constants.FACTOR_THRESH.value:
                unique_values = self_as_str.unique().tolist()
            else:
                char_count = Counter()
                for x in self_as_str.fillna('').astype(str).to_numpy():
                    char_count.update(x)
                unique_values = "".join(char_count.keys())
            return {
                'min': int(self.fillna('').astype(str).str.len().min()),
                'max': int(self.fillna('').astype(str).str.len().max()),
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'elements': unique_values,
                'type': Constants.STR_TYPE.value
            }

    def _minmax_string(self, stype, **kwargs):
        #coordinate all string processing
        if stype == Constants.USER_STEXT.value:
            r = self._process_as_text()
        elif stype == Constants.USER_SDATE.value:
            r = self._process_text_as_date(**kwargs)
            if r is None:
                r = self._process_as_text()
            return r
        else:
            filter = self._flag_numbers_as_str()
            isnumbers = filter is not None and \
                self[~self.isna()].shape[0] > 0 and\
                (0.00 + filter.sum() / self[~self.isna()].shape[0]) > Constants.PROP_NUMBERS_THRESH.value
            if stype == Constants.USER_SNUM.value or isnumbers:
                r = self._process_text_as_number(filter)
            else:
                r = self._process_as_text()
        return r

    def _element_summary(self):
        """summary of elements of a continuous or semi-continuous variable such as number or time"""
        head = self[~self.isna()][:Constants.UNIQUE_RANGE.value]
        uniq_vals = head.unique()
        return ["({0:d} unique values)".format(self[~self.isna()].unique().size)] \
            + (uniq_vals[:Constants.FACTOR_THRESH.value].tolist() \
            if uniq_vals.size <= Constants.FACTOR_THRESH.value else \
            uniq_vals[:Constants.FACTOR_THRESH.value].tolist() + ['...'])

    def minmax(self, stype = None, *args, **kwargs):
        """use:
            s.minmax() # if it is a series of dates, numbers or categories stored in non-text format
            s.minmax(stype="number") # if it is a series of numbers stored as strings
            s.minmax(stype="text") # if it is a series of free text values (speeds processing)
            s.minmax(format="%d%m%Y") # if it is a series of dates stored as strings(speeds processing)
            s.minmax(dayfirst=True, yearlast=True) # a series of dates stored as strings withoug explicitly
                    specifying format"""
        report = {'name': self.name, 'type': Constants.UNKNOWN_TYPE.value, 'n_unique': self.nunique(),
                    'min': None, 'max': None, 'errors': None, 'elements': None,
                    }
        if self.dtype.kind in Constants.NUMERIC_KIND.value:
            report.update({
                'type': Constants.NUMERIC_TYPE.value,
                'min': self.min().item(),
                'max': self.max().item(),
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'elements': self._element_summary()
                })
        elif is_datetime_64(self):
            report.update({
                'type': Constants.DATE_TYPE.value,
                'min': self.min().date(),
                'max': self.max().date(),
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'elements': self._element_summary()
            })
        elif is_timedelta_64(self):
            report.update({
                'type': Constants.TDELTA_TYPE.value,
                'min': self.min(),
                'max': self.max(),
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'elements': self._element_summary()
            })
        elif self.dtype == 'category':
            report.update({
                'min': self.min(),
                'max': self.max(),
                'n_null': self.isna().sum().item(),
                'n_not_null': self.notna().sum().item(),
                'type': Constants.CAT_TYPE.value,
                'elements': self.dtype.categories.to_list()
            })
        elif self.dtype == 'O':
            report.update(self._minmax_string(stype, **kwargs))
        else:
            try:
                report.update({
                    'min': self.min(),
                    'max': self.max(),
                    'n_null': self.isna().sum().item(),
                    'n_not_null': self.notna().sum().item(),
                })
            finally:
                report.update({'type': self.dtype})
        return report
