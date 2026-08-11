import datetime

import pytest

from PyTM.core import invoice_handler

TEST_TIME_NOW = datetime.datetime(
    2023,
    11,
    9,
)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return TEST_TIME_NOW

    monkeypatch.setattr(invoice_handler.datetime, "datetime", mydatetime)


def test_generate(test_data, patch_datetime_now):
    invoice_texts = {
        "title": "Invoice",
        "logo": "",
        "foot_note": "Thanks for your business.",
    }
    user = {
        "name": "Test User",
        "address": "Earth",
        "email": "test@email.com",
        "phone": "+123456789",
        "website": "test.com",
        "hourly_rate": "125",
    }
    html = invoice_handler.generate(
        "13", invoice_texts, user, test_data.get("HelloWorld!"), 10
    )
    assert (
        html
        == '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Invoice</title>\n    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.15/dist/tailwind.min.css" rel="stylesheet">\n</head>\n<body class="font-sans bg-gray-100">\n    <div class="container mx-auto py-8">\n        <div class="bg-white rounded-lg shadow-lg p-8">\n            <div class="flex justify-between">\n                <div class="flex items-center">\n                    <img src="" width=150 alt="Test User" class="h-12 mr-4" style="height:auto;">\n                    <div>\n                        <h1 class="text-2xl font-semibold">Test User</h1>\n                        <p>Earth</p>\n                        <p>test@email.com</p>\n                        <p>+123456789</p>\n                        <p>test.com</p>\n                        </div>\n                </div>\n                <div class="text-right">\n                    <p class="text-sm">Invoice 13</p>\n                    <p class="text-sm">Date: 2023-11-09</p>\n                    <h2 class="font-semibold">Bill to</h2>\n                    <p>Anon</p>\n                    <p>Planet, Earth</p>\n                    <p>anon@exmaple.com</p>\n                    <p>+987654321</p>\n                    <p>example.com</p>\n                </div>\n            </div>\n            <div class="text-left mb-4">\n                <h1 class="text-2xl font-semibold">Project: Hello World!</h1>\n                <p>Date: 2023-11-05</p>\n                <p>Duration: 30 seconds</p>\n            </div>\n            <div class="mt-4">\n                <table class="w-full border-collapse border border-gray-300">\n                    <thead>\n                        <tr>\n                            <th class="p-2 border border-gray-300">Task</th>\n                            <th class="p-2 border border-gray-300">Description</th>\n                            <th class="p-2 border border-gray-300">Hours</th>\n                            <th class="p-2 border border-gray-300">Hourly Rate</th>\n                            <th class="p-2 border border-gray-300">Fee</th>\n                        </tr>\n                    </thead>\n                    <tbody>\n\n                        <tr>\n                            <td class="p-2 border border-gray-300">Task 1</td>\n                            <td class="p-2 border border-gray-300">-</td>\n                            <td class="p-2 border border-gray-300">0.01</td>\n                            <td class="p-2 border border-gray-300">125.00$</td>\n                            <td class="p-2 border border-gray-300">0.79</td>\n                        </tr>\n<tr>\n                            <td class="p-2 border border-gray-300">Task 2</td>\n                            <td class="p-2 border border-gray-300">-</td>\n                            <td class="p-2 border border-gray-300">0.00</td>\n                            <td class="p-2 border border-gray-300">125.00$</td>\n                            <td class="p-2 border border-gray-300">0.23</td>\n                        </tr>\n                        \n                    </tbody>\n                </table>\n            </div>\n            <div class="mt-4">\n                <div class="flex justify-end">\n                    <div class="w-1/2">\n                        <table class="w-full">\n                            <tr>\n                                <td class="py-1">Subtotal:</td>\n                                <td class="text-right py-1">1.02$</td>\n                            </tr>\n                            <tr>\n                                <td class="py-1">Discount:</td>\n                                <td class="text-right py-1">10.00$</td>\n                            </tr>\n                            <tr>\n                                <td class="py-1"><strong>Total:</strong></td>\n                                <td class="text-right py-1">-8.98$</td>\n                            </tr>\n                        </table>\n                    </div>\n                </div>\n            </div>\n            <div class="mt-4">\n                <p class="text-left text-sm">Thanks for your business.</p>\n            </div>\n        </div>\n    </div>\n</body>\n</html>\n'
    )


def test_generate_bills_one_hour_task_as_one_hour(patch_datetime_now):
    """
    Regression test for the 10x billing bug: duration is stored in
    seconds, so a task that ran for exactly one hour (3600s) must be
    billed as 1.00 hour, not 10.00 (the old `/360` bug) or 0.10.
    """
    invoice_texts = {"title": "Invoice", "logo": "", "foot_note": ""}
    user = {
        "name": "Test User",
        "address": "",
        "email": "",
        "phone": "",
        "website": "",
        "hourly_rate": "100",
    }
    project = {
        "created_at": f"{TEST_TIME_NOW}",
        "meta": {
            "title": "Solo Project",
            "client_name": "Client",
            "client_address": "",
            "client_email": "",
            "client_phone": "",
            "client_website": "",
        },
        "tasks": {
            "One Hour Task": {
                "duration": 3600,
                "status": "finished",
                "description": "-",
            }
        },
    }
    html = invoice_handler.generate("1", invoice_texts, user, project, discount=0)
    assert "1.00" in html  # billed hours
    assert "100.00$" in html  # fee = 1 hour * $100/hr
    assert "10.00" not in html
    assert "1000.00" not in html
