from PyTM.core.data_handler import init_data
from PyTM.core.data_handler import load_data
from PyTM.core.data_handler import save_data
from PyTM.core.data_handler import update
import json


def test_init_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    init_data(tmp_path)
    assert tmp_path.read() == "{}"


def test_load_data_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    tmp_path.write(json.dumps(data))
    assert load_data(tmp_path) == data


def test_load_data_doesnot_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    assert load_data(tmp_path) == {}


def test_save_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    save_data(data, tmp_path)
    assert tmp_path.read() == json.dumps(data)


def test_update(tmpdir):
    f = lambda d: {"user": "test"}
    tmp_path = tmpdir.join("pytm-test.json")
    tmp_path.write("[]")
    update(f, tmp_path)
    assert tmp_path.read() == '{"user": "test"}'
