import re

from dfeqa import valid_name_regex, valid_upn


def test_valid_name():
    assert re.findall(valid_name_regex,'Raymond Cocteau') == ['Raymond Cocteau']

def test_valid_name_contains_number():
    assert re.findall(valid_name_regex,'Raym0nd Cocteau') == ['Raym0nd Cocteau']

def test_valid_name_contains_apostrophe():
    assert re.findall(valid_name_regex,"Raymond C'octeau") == ["Raymond C'octeau"]

def test_invalid_name_contains_phone_number():
    assert re.findall(valid_name_regex,'01898 888444') == []

def test_valid_upn():
    assert valid_upn('A123456789012')

def test_invalid_upn():
    assert not valid_upn('B123456789012')
