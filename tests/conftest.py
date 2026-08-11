import pytest

from PyTM import settings


@pytest.fixture()
def pytm_home(tmp_path, monkeypatch):
    """
    Isolates a CLI-level test from the developer's real `~/.pytm` store.

    `data_handler`'s public functions resolve `settings.data_filepath` /
    `settings.state_filepath` fresh on every call (not as bound function
    defaults), so patching these attributes here is enough to redirect
    every command under test to a throwaway directory.
    """
    data_folder = tmp_path / "pytm-home"
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "data_filepath", str(data_folder / "data.json"))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    return data_folder


@pytest.fixture()
def test_data():
    return {
        "HelloWorld!": {
            "tasks": {
                "Task_1": {
                    "created_at": "2023-11-05 14:51:15.498257",
                    "status": "finished",
                    "duration": 22.641091,
                    "since": "",
                    "finished_at": "2023-11-05 14:51:55.117368",
                },
                "Task_2": {
                    "created_at": "2023-11-05 14:52:03.955644",
                    "status": "finished",
                    "duration": 6.620551,
                    "since": "",
                    "finished_at": "2023-11-05 14:52:10.578448",
                },
            },
            "created_at": "2023-11-05 14:50:25.139631",
            "status": "finished",
            "meta": {
                "title": "Hello World!",
                "billable": True,
                "client_name": "Anon",
                "client_email": "anon@exmaple.com",
                "client_phone": "+987654321",
                "client_address": "Planet, Earth",
                "client_website": "example.com",
            },
        },
        "Test": {
            "tasks": {},
            "created_at": "2023-11-05 14:55:30.250893",
            "status": "paused",
        },
        "Sample": {
            "tasks": {},
            "created_at": "2023-11-07 14:39:41.816441",
            "status": "finished",
        },
        "Demo": {
            "tasks": {
                "Task_1": {
                    "created_at": "2023-11-07 15:28:30.788607",
                    "status": "finished",
                    "duration": 21.069416,
                    "since": "",
                    "finished_at": "2023-11-07 15:28:51.860428",
                },
                "Task_2": {
                    "created_at": "2023-11-07 15:28:56.988527",
                    "status": "finished",
                    "duration": 17.375999,
                    "since": "",
                    "finished_at": "2023-11-07 15:29:24.284147",
                },
                "Task_3": {
                    "created_at": "2023-11-07 15:28:30.788607",
                    "status": "finished",
                    "duration": 21.069416,
                    "since": "",
                    "finished_at": "2023-11-07 15:28:51.860428",
                },
            },
            "created_at": "2023-11-07 15:28:22.518193",
            "status": "finished",
            "meta": {
                "title": "Demo Project",
                "billable": True,
                "client_name": "Anonymous",
                "client_email": "anon@example.com",
                "client_phone": "+987654321",
                "client_address": "Somewhere, In, Earth",
                "client_website": "example.com",
            },
        },
        "BEST": {
            "tasks": {
                "UNTITLED_1": {
                    "created_at": "2023-11-08 18:30:01.391926",
                    "status": "running",
                    "duration": 0,
                    "since": "2023-11-08 18:30:01.391938",
                },
                "TODO": {
                    "created_at": "2023-11-08 18:30:03.517269",
                    "status": "finished",
                    "duration": 61.664511,
                    "since": "",
                    "finished_at": "2023-11-08 18:31:05.186215",
                },
            },
            "created_at": "2023-11-08 18:24:07.726515",
            "status": "finished",
        },
    }
