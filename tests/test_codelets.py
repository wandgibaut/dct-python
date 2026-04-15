import json
import tempfile
import unittest
from pathlib import Path

from dct.codelets import PythonCodelet


class ConcreteCodelet(PythonCodelet):
    def __init__(self, *args, **kwargs):
        self.activations = []
        super().__init__(*args, **kwargs)

    def proc(self, activation: float) -> None:
        self.activations.append(activation)


class PythonCodeletTests(unittest.TestCase):
    def test_base_class_requires_proc_implementation(self):
        with self.assertRaises(TypeError):
            PythonCodelet()

    def test_field_helpers_read_and_update_fields_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            fields_path = root / "fields.json"
            fields_path.write_text(
                json.dumps(
                    {
                        "enable": False,
                        "lock": False,
                        "timestep": 0,
                        "items": [{"name": "old"}],
                    }
                ),
                encoding="utf-8",
            )

            codelet = ConcreteCodelet(name="test", root_codelet_dir=root)

            self.assertEqual(codelet.name, "test")
            self.assertEqual(codelet.read_field("enable"), False)
            self.assertEqual(codelet.fields_path, fields_path)

            codelet.change_field("enable", True)
            self.assertEqual(json.loads(fields_path.read_text(encoding="utf-8"))["enable"], True)

            codelet.add_entry("items", '{"name": "new"}')
            self.assertEqual(codelet.remove_entry("items", "old"), {"name": "old"})

            codelet.set_field_list("items", ['{"name": "first"}', '{"name": "second"}'])
            self.assertEqual(
                json.loads(fields_path.read_text(encoding="utf-8"))["items"],
                [{"name": "first"}, {"name": "second"}],
            )

    def test_default_activation_and_convert(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "fields.json").write_text(
                json.dumps({"enable": False, "lock": False, "timestep": 0}),
                encoding="utf-8",
            )

            codelet = ConcreteCodelet(root_codelet_dir=root)

            self.assertEqual(codelet.calculate_activation(), 0)
            self.assertEqual(codelet.convert("a;b;c"), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
