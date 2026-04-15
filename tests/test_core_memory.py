import json
import tempfile
import unittest
from pathlib import Path

import dct


class CoreMemoryTests(unittest.TestCase):
    def test_local_memory_get_and_set(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_dir = Path(tmp_dir)
            memory_path = memory_dir / "working.json"
            memory_path.write_text(json.dumps({"name": "working", "value": 1}), encoding="utf-8")

            self.assertEqual(dct.get_local_memory(str(memory_dir), "working")["value"], 1)

            self.assertEqual(dct.set_local_memory(str(memory_dir), "working", "value", 2), 0)
            self.assertEqual(json.loads(memory_path.read_text(encoding="utf-8"))["value"], 2)

    def test_add_memory_to_group_updates_existing_memory_once(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            memories = root / "memories"
            memories.mkdir()

            (root / "fields.json").write_text(
                json.dumps(
                    {
                        "inputs": [
                            {
                                "name": "working",
                                "type": "local",
                                "ip/port": str(memories),
                                "group": [],
                            }
                        ],
                        "outputs": [],
                    }
                ),
                encoding="utf-8",
            )
            memory_path = memories / "working.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "name": "working",
                        "type": "local",
                        "ip/port": str(memories),
                        "group": ["existing"],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(dct.add_memory_to_group(str(root), "working", "new", "inputs"), 0)
            self.assertEqual(dct.add_memory_to_group(str(root), "working", "new", "inputs"), 0)
            self.assertEqual(
                json.loads(memory_path.read_text(encoding="utf-8"))["group"],
                ["existing", "new"],
            )

    def test_add_memory_to_group_returns_error_for_missing_memory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "fields.json").write_text(
                json.dumps({"inputs": [], "outputs": []}),
                encoding="utf-8",
            )

            self.assertEqual(dct.add_memory_to_group(str(root), "missing", "new", "inputs"), -1)


if __name__ == "__main__":
    unittest.main()
