import json

from PyTM.core import data_handler


def test_init_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data_handler.init_data(tmp_path)
    assert tmp_path.read() == "{}"


def test_load_data_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    tmp_path.write(json.dumps(data))
    assert data_handler.load_data(tmp_path) == data


def test_load_data_doesnot_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    assert data_handler.load_data(tmp_path) == {}


def test_save_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    data_handler.save_data(data, tmp_path)
    assert tmp_path.read() == json.dumps(data)


def test_update(tmpdir):
    f = lambda d: {"user": "test"}
    tmp_path = tmpdir.join("pytm-test.json")
    tmp_path.write("[]")
    data_handler.update(f, tmp_path)
    assert tmp_path.read() == '{"user": "test"}'
