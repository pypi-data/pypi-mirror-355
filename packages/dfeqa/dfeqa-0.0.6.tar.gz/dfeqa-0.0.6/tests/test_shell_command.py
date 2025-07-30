import hashlib
import os
from pathlib import Path

import pytest

import dfeqa
from dfeqa.cmdline import execute


def test_generate_from_template(tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        execute(['dfeqa', 'create', 'data_quality', 'testfile.txt'])
    assert md5(str(Path(dfeqa.__path__[0], "templates", "data_quality.qmd"))) == \
        md5(Path(tmpdir, "testfile.txt"))

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
