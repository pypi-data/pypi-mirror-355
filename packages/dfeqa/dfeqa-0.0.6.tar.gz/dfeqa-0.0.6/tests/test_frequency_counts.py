import pandas as pd

from dfeqa import fd, summary
from dfeqa.datastructures import DataFrame


def test_freq_dist_from_series(List_Of_Series):
    pd.testing.assert_frame_equal(
        fd(List_Of_Series[0].str.len()),
        DataFrame(List_Of_Series[0].str.len().value_counts().sort_index()\
            .reset_index(drop=False).rename(columns={List_Of_Series[0].name: 'value'}))
    )


def test_freq_dist_from_dataframe_with_columns(List_Of_Series, Wide_Frame_Length_Summary):
    dummy_col = List_Of_Series[0].apply(lambda x: 'dummy value').rename('dummy')
    pd.testing.assert_frame_equal(
        fd(pd.concat([x.str.len() for x in List_Of_Series + [dummy_col]] , axis=1), cols = ['forename', 'surname']),
        DataFrame(Wide_Frame_Length_Summary)
    )


def test_freq_dist_from_series_without_ids():
    s = pd.Series(['x' for a in range(10)], name="testdata")
    pd.testing.assert_frame_equal(fd(s), DataFrame([{'value':'x','count':10}]))


def test_freq_dist_from_dataframe_without_columns(List_Of_Series):
    test_fd = pd.concat([
        s.value_counts(dropna=False).rename(s.name) for s in List_Of_Series
        ], axis = 1).fillna(0).astype(int)\
            .sort_index().reset_index(drop=False).rename(columns={'index':'value'})
    pd.testing.assert_frame_equal(fd(pd.concat(List_Of_Series, axis=1)), DataFrame(test_fd))


def test_freq_dist_from_list_of_series(List_Of_Series, Wide_Frame_Name_Freqs):
    pd.testing.assert_frame_equal(fd(List_Of_Series), DataFrame(Wide_Frame_Name_Freqs))


def test_freq_dist_from_list_of_series_same_name(List_Of_Series):
    d = fd([List_Of_Series[0],List_Of_Series[0]], ids=['a','b'])
    assert d.columns.tolist() == ['value','a','b']


def test_wide_freq_dist_from_dataframe_with_custom_id(List_Of_Series, Wide_Frame_Name_Freqs):
    benchmark = Wide_Frame_Name_Freqs.rename(columns={'forename':'f','surname':'s'})
    pd.testing.assert_frame_equal(fd(pd.concat(List_Of_Series , axis=1), ids=['f','s']),
        DataFrame(benchmark))


def test_wide_freq_dist_from_list_with_custom_id(List_Of_Series, Wide_Frame_Name_Freqs):
    benchmark = Wide_Frame_Name_Freqs.rename(columns={'forename':'f','surname':'s'})
    pd.testing.assert_frame_equal(fd(List_Of_Series, ids=['f','s']),
        DataFrame(benchmark))


def test_long_freq_dist_from_list_with_custom_id(List_Of_Series):
    df = fd(List_Of_Series, ids=['f','s'], long=True)
    g = df['group'].unique()
    assert g[0] == 'f' and g[1] == 's'


def test_freq_dist_from_series_using_object(List_Of_Series):
    pd.testing.assert_frame_equal(
        summary(List_Of_Series[0].str.len()).wide_fd(),
        DataFrame(
        List_Of_Series[0].str.len().value_counts().sort_index(ascending=True).reset_index(drop=False)\
            .rename(columns={
                List_Of_Series[0].name: 'value',
                'count': List_Of_Series[0].name
                }))
    )


def test_freq_dist_from_dataframe_using_object(List_Of_Series):
    test_fd = pd.concat([
        s.value_counts(dropna=False).rename(s.name) for s in List_Of_Series
        ], axis = 1).fillna(0).astype(int)\
            .sort_index(ascending=True).reset_index(drop=False).rename(columns={'index':'value'})
    pd.testing.assert_frame_equal(summary(pd.concat(List_Of_Series, axis=1)).wide_fd(),
        DataFrame(test_fd))


def test_freq_dist_from_list_using_object(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary(List_Of_Series).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort))


def test_freq_dist_from_dict_using_object(List_Of_Series):
    test_dict = {x.name: x.rename(None) for x in List_Of_Series}
    test_fd = pd.concat([
        s.value_counts(dropna=False).rename(s.name) for s in List_Of_Series
        ], axis = 1).fillna(0).astype(int)\
        .reset_index(drop=False).rename(columns={'index':'value'})\
        .sort_values(['forename','surname','value'], ascending=[False,False,True])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary(test_dict).wide_fd(sort_counts=True),\
        DataFrame(test_fd))


def test_freq_dist_from_dict_of_series_using_object(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary({x.name:x for x in List_Of_Series}).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort))


def test_freq_dist_from_dict_of_series_same_name_using_object(List_Of_Series):
    d = summary({'a': List_Of_Series[0].rename('z'),'b': List_Of_Series[0].rename('z')}).wide_fd()
    assert d.columns.tolist() == ['value','a','b']


def test_freq_dist_from_tuple_of_series_using_object(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary(tuple(List_Of_Series)).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort))


def test_long_freq_dist_from_list_using_object(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    df = summary(List_Of_Series, names=['f','s']).long_fd()
    ref_df = Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})\
        .melt(id_vars=['value'], var_name="group", value_name="count").sort_values(['group','value','count'])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(df,DataFrame(ref_df))


def test_object_wide_custom_ids_from_tuple(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary(tuple(List_Of_Series), dropna=False).set_names(['f','s']).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})))


def test_object_wide_custom_ids_from_list(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary(List_Of_Series, dropna=False)\
        .set_names(['f','s']).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})))


def test_object_wide_custom_ids_from_df(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    pd.testing.assert_frame_equal(
        summary(pd.concat(List_Of_Series , axis=1), dropna=False)\
        .set_names(['f','s']).wide_fd(sort_counts=True),
        DataFrame(Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'}))
    )


def test_object_wide_custom_ids_from_series(List_Of_Series):
    benchmark = List_Of_Series[0].value_counts(dropna=False).reset_index(drop=False)\
        .rename(columns={'forename':'value', 'count':'forename'})\
        .sort_values(['forename','value'],ascending=[False,True])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary(List_Of_Series[0], dropna=False)\
        .wide_fd(sort_counts=True), DataFrame(benchmark))


def test_object_long_custom_ids_from_tuple(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    benchmark = Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})\
        .melt(id_vars=['value'], var_name="group", value_name="count").sort_values(['group','value','count'])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(
        summary(tuple(List_Of_Series), dropna=False).set_names(['f','s']).long_fd(),
        DataFrame(benchmark))


def test_object_long_custom_ids_from_list(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    benchmark = Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})\
        .melt(id_vars=['value'], var_name="group", value_name="count").sort_values(['group','value','count'])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary(List_Of_Series, dropna=False).set_names(['f','s']).long_fd(),
        DataFrame(benchmark))


def test_object_long_custom_ids_from_df(List_Of_Series, Wide_Frame_Name_Freqs_Max_Sort):
    benchmark = Wide_Frame_Name_Freqs_Max_Sort.rename(columns={'forename':'f','surname':'s'})\
        .melt(id_vars=['value'], var_name="group", value_name="count").sort_values(['group','value','count'])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary(pd.concat(List_Of_Series , axis=1), dropna=False)\
        .set_names(['f','s']).long_fd(),
        DataFrame(benchmark))


def test_object_long_custom_ids_from_series(List_Of_Series):
    benchmark = List_Of_Series[0].value_counts(dropna=False)\
        .reset_index(drop=False).rename(columns={'forename':'value', 'count':'f'})\
        .melt(id_vars=['value'], var_name="group", value_name="count").sort_values(['group','value','count'])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary(List_Of_Series[0], dropna=False)\
        .set_names(['f']).long_fd(),
        DataFrame(benchmark))

def test_object_long_value_sort(List_Of_Series, Long_Frame_Length_Summary):
    benchmark = Long_Frame_Length_Summary.sort_values(['group','value'],ascending=[True,True])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .long_fd(sort_counts=False),
        DataFrame(benchmark))

def test_object_long_count_sort(List_Of_Series, Long_Frame_Length_Summary):
    benchmark = Long_Frame_Length_Summary.sort_values(['group','count','value'],ascending=[True,False,True])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .long_fd(sort_counts=True),
        DataFrame(benchmark))

def test_object_long_value_default_sort(List_Of_Series, Long_Frame_Length_Summary):
    benchmark = Long_Frame_Length_Summary.sort_values(['group','value'],ascending=[True,True])\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .long_fd(),
        DataFrame(benchmark))

def test_object_wide_count_sort(List_Of_Series, Wide_Frame_Length_Summary):
    benchmark = Wide_Frame_Length_Summary\
        .assign(val_sort= Wide_Frame_Length_Summary[['forename','surname']].max(axis=1))\
        .sort_values(['val_sort','forename','surname'],ascending=False)\
        .reset_index(drop=True).drop(columns=['val_sort'])
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .wide_fd(sort_counts=True),
        DataFrame(benchmark))

def test_object_wide_value_sort(List_Of_Series, Wide_Frame_Length_Summary):
    benchmark = Wide_Frame_Length_Summary\
        .sort_values('value',ascending=True)\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .wide_fd(sort_counts=False),
        DataFrame(benchmark))

def test_object_wide_default_sort(List_Of_Series, Wide_Frame_Length_Summary):
    benchmark = Wide_Frame_Length_Summary\
        .sort_values('value',ascending=True)\
        .reset_index(drop=True)
    pd.testing.assert_frame_equal(summary([x.str.len() for x in List_Of_Series], dropna=False)\
        .wide_fd(),
        DataFrame(benchmark))
