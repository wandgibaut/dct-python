import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


class FakeResponse:
    def __init__(self, *args, status=None, headers=None, **kwargs):
        self.status_code = status
        self.headers = headers or {}


class FakeFlask:
    def __init__(self, name):
        self.name = name

    def route(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


class FakeRequest:
    host = "127.0.0.1:5000"

    def __init__(self, payload=None):
        self.payload = payload

    def get_json(self):
        return self.payload


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_flask = types.ModuleType("flask")
        fake_flask.Flask = FakeFlask
        fake_flask.Response = FakeResponse
        fake_flask.request = FakeRequest()

        cls.flask_patcher = mock.patch.dict(sys.modules, {"flask": fake_flask})
        cls.flask_patcher.start()
        cls.server = importlib.import_module("dct.server")

    @classmethod
    def tearDownClass(cls):
        cls.flask_patcher.stop()

    def test_validate_idea_requires_expected_fields(self):
        valid = {"id": 1, "name": "idea", "l": 0, "category": "c", "scope": "s", "value": 42}

        self.assertEqual(self.server.validate_idea(valid), valid)
        self.assertIsNone(self.server.validate_idea({"name": "idea"}))

    def test_request_json_accepts_dict_and_encoded_dict(self):
        self.server.request = FakeRequest({"name": "idea"})
        self.assertEqual(self.server._request_json(), {"name": "idea"})

        self.server.request = FakeRequest(json.dumps({"name": "idea"}))
        self.assertEqual(self.server._request_json(), {"name": "idea"})

        self.server.request = FakeRequest(["not", "a", "dict"])
        with self.assertRaises(ValueError):
            self.server._request_json()

    def test_redis_url_uses_request_port_plus_one(self):
        self.server.request = FakeRequest()
        self.server.request.host = "localhost:7000"

        self.assertEqual(self.server._redis_url_from_request(), "localhost:7001")

    def test_get_node_info_reads_fields_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            codelet = root / "codelets" / "a"
            codelet.mkdir(parents=True)
            (codelet / "fields.json").write_text(
                json.dumps(
                    {
                        "inputs": [{"ip/port": "127.0.0.1:1"}, {"ip/port": "127.0.0.1:1"}],
                        "outputs": [{"ip/port": "127.0.0.1:2"}],
                    }
                ),
                encoding="utf-8",
            )

            old_root = self.server.root_node_dir
            self.server.root_node_dir = str(root)
            try:
                self.assertEqual(
                    json.loads(self.server.get_node_info()),
                    {
                        "number_of_codelets": 1,
                        "input_ips": ["127.0.0.1:1"],
                        "output_ips": ["127.0.0.1:2"],
                    },
                )
            finally:
                self.server.root_node_dir = old_root


if __name__ == "__main__":
    unittest.main()
