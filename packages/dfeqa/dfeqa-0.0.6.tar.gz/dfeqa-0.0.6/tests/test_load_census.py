import pytest

from dfeqa import load_census


def test_load_census_without_conn():
    df = load_census(202324, NCYear = "R", term = "Autumn", columns = "PupilMatchingRefAnonymous")
    assert df.shape[0] > 100

def test_load_census_with_conn_multiple_columns(PDR_Conn):
    df = load_census(202324, NCYear = "R", term = "Autumn",
        columns = ["forename","surname"],
        conn = PDR_Conn)
    assert df.shape[0] > 100

def test_load_census_multiyeargroup(PDR_Conn):
    df = load_census(202324, NCYear = ["R","1"], term = "Autumn",
        columns = "PupilMatchingRefAnonymous",
        conn = PDR_Conn)
    assert df.shape[0] > 100

@pytest.mark.slow
def test_load_allcols():
    df = load_census(202324, NCYear = "R", term = "Autumn")
    assert df.shape[0] > 100
