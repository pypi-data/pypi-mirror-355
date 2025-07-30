from dfeqa import parse_text, year_group


def test_older_year_group():
    assert year_group("23092012",2024) == 'y6'

def test_younger_year_group():
    assert year_group("01012013",2024) == 'y6'

def test_really_old_year_group():
    assert year_group("01012010",2024) == 'abovey8'

def test_year_group_custom_upper():
    assert year_group("01012010",2024, upper_year = 6) == 'abovey6'

def test_reception_year_group():
    assert year_group("01012019",2024) == 'r'

def test_really_young_year_group():
    assert year_group("01012020",2024) == 'under_r'

def test_parsed_text():
    my_data = {'my_val': "to catch one"}
    assert parse_text("send a maniac {{my_val}}",my_data) == "send a maniac to catch one"

def test_recursive_conditional_text():
    my_data = {'my_val': "to catch one",'boggle': "good", 'my_val2':"from a brutish bygone era"}
    assert parse_text("send a maniac {{'boggle = good'|{{my_val}}|{{my_val2}}}}",my_data) == "send a maniac from a brutish bygone era"

def test_academic_year_as_string():
    assert year_group("23092012","2024") == 'y6'

def test_upper_year_as_string():
    assert year_group("01012010","2024", upper_year = "6") == 'abovey6'
