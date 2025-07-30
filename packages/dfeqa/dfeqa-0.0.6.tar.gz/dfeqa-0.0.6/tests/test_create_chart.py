from matplotlib import axes

from dfeqa import barchart


def test_freq_dist_chart_generates(Long_Frame_Length_Summary):
    assert isinstance(barchart(chartdata = Long_Frame_Length_Summary,
        cats = 'value',
        values = 'count',
        groups = 'group',
        vlines = [(3,4),(9,8)]),
    axes._axes.Axes)


def test_freq_dist_chart_generates_with_ints(Long_Frame_Length_Summary):
    assert isinstance(barchart(chartdata = Long_Frame_Length_Summary,
        cats = 'value',
        values = 'count',
        groups = 'group',
        vlines= (3,9)), axes._axes.Axes)


def test_freq_chart_reformats_string_xaxis(Long_Frame_Length_Summary):
    assert isinstance(barchart(chartdata = Long_Frame_Length_Summary,
        cats = 'value',
        values = 'count',
        groups = 'group',
        vlines = (3,9),
        x_rescale = 2), axes._axes.Axes)


def test_freq_chart_reformats_list_xaxis(Long_Frame_Length_Summary):
    assert isinstance(barchart(Long_Frame_Length_Summary,
        cats = 'value',
        values = 'count',
        groups = 'group',
        x_rescale = [0, 2, 4]), axes._axes.Axes)

def test_chart_cats_from_index(Wide_Frame_Length_Summary):
    testdata = Wide_Frame_Length_Summary.copy()
    assert isinstance(
        barchart(testdata.set_index('value'), values='forename'),
        axes._axes.Axes)

def test_chart_no_values(People_As_Frame):
    assert isinstance(
        barchart(
            People_As_Frame, cats='fname_len'),
        axes._axes.Axes)

def test_chart_from_series(List_Of_Series):
    assert isinstance(
        barchart(
            List_Of_Series[0]),
        axes._axes.Axes)

def test_chart_from_list_of_series(List_Of_Series):
    assert isinstance(
        barchart([x.str.len().value_counts().rename(x.name) for x in List_Of_Series]),
        axes._axes.Axes)
