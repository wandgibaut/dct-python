import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import dct
from dct.codelets import PythonCodelet
from dct.mind import Mind


class WriterCodelet(PythonCodelet):
    def calculate_activation(self) -> float:
        return 3.5

    def proc(self, activation: float) -> None:
        dct.set_memory_objects_by_name(
            str(self.root_codelet_dir),
            "workspace",
            "value",
            activation,
            "outputs",
        )


class CountingCodelet(PythonCodelet):
    def proc(self, activation: float) -> None:
        self.fields["count"] = int(self.fields.get("count", 0)) + 1
        self.write_all_field()


class ExistingCodelet(PythonCodelet):
    def proc(self, activation: float) -> None:
        pass


class FakeRedisProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False
        self.wait_calls = 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.wait_calls += 1

    def kill(self):
        self.killed = True


class MindTests(unittest.TestCase):
    def test_add_json_memory_and_run_codelet_once(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mind = Mind(base_dir=tmp_dir)
            mind.add_memory("workspace", "json", initial_value={"value": 0})
            codelet = mind.add_codelet(WriterCodelet, outputs=["workspace"])

            mind.run_once()

            self.assertEqual(codelet.name, "WriterCodelet")
            self.assertEqual(
                json.loads((Path(tmp_dir) / "memories" / "workspace.json").read_text(encoding="utf-8"))["value"],
                3.5,
            )

    def test_run_steps_executes_deterministic_number_of_cycles(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mind = Mind(base_dir=tmp_dir)
            mind.add_codelet(CountingCodelet, name="counter", timestep=0)

            mind.run(steps=3)

            fields = json.loads(
                (Path(tmp_dir) / "codelets" / "counter" / "fields.json").read_text(encoding="utf-8")
            )
            self.assertEqual(fields["count"], 3)

    def test_codelet_fields_bind_redis_mongo_and_local_memories(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mind = Mind(base_dir=tmp_dir, redis_port=7001)
            mind.add_memory("r", "redis")
            mind.add_memory("m", "mongo", location="mongodb://db:27017")
            mind.add_memory("j", "json", group=["sensory"])

            mind.add_codelet(CountingCodelet, name="collector", inputs=["r", "m"], outputs=["j"])

            fields = json.loads(
                (Path(tmp_dir) / "codelets" / "collector" / "fields.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                fields["inputs"],
                [
                    {"name": "r", "type": "redis", "ip/port": "127.0.0.1:7001", "group": []},
                    {"name": "m", "type": "mongo", "ip/port": "mongodb://db:27017", "group": []},
                ],
            )
            self.assertEqual(
                fields["outputs"],
                [{"name": "j", "type": "local", "ip/port": str(Path(tmp_dir) / "memories"), "group": ["sensory"]}],
            )

    def test_add_codelet_accepts_existing_instance(self):
        with tempfile.TemporaryDirectory() as original_dir, tempfile.TemporaryDirectory() as mind_dir:
            original_root = Path(original_dir)
            (original_root / "fields.json").write_text(
                json.dumps({"enable": False, "lock": False, "timestep": 0, "inputs": [], "outputs": []}),
                encoding="utf-8",
            )
            instance = ExistingCodelet(name="existing", root_codelet_dir=original_root)

            mind = Mind(base_dir=mind_dir)
            returned = mind.add_codelet(instance, outputs=[])

            self.assertIs(returned, instance)
            self.assertEqual(instance.root_codelet_dir, Path(mind_dir) / "codelets" / "existing")

    def test_redis_process_lifecycle(self):
        fake_process = FakeRedisProcess()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch("subprocess.Popen", return_value=fake_process) as popen:
                mind = Mind(base_dir=tmp_dir, start_redis=True, redis_port=6380)

                mind.start()
                mind.stop()

        popen.assert_called_once()
        command = popen.call_args.args[0]
        self.assertEqual(command[:3], ["redis-server", "--port", "6380"])
        self.assertIn("--dir", command)
        self.assertTrue(fake_process.terminated)
        self.assertEqual(fake_process.wait_calls, 1)

    def test_redis_initial_memory_is_deferred_until_start(self):
        fake_process = FakeRedisProcess()

        with tempfile.TemporaryDirectory() as tmp_dir:
            mind = Mind(base_dir=tmp_dir, start_redis=True, redis_port=6380)
            with mock.patch("dct.set_redis_memory") as set_redis_memory:
                mind.add_memory("workspace", "redis", initial_value={"value": "ready"})
                set_redis_memory.assert_not_called()

                with mock.patch("subprocess.Popen", return_value=fake_process):
                    mind.start()
                    mind.stop()

        set_redis_memory.assert_called_once_with(
            "127.0.0.1:6380",
            "workspace",
            None,
            None,
            full_memory={
                "name": "workspace",
                "type": "redis",
                "ip/port": "127.0.0.1:6380",
                "group": [],
                "value": "ready",
            },
        )

    def test_context_manager_cleans_temporary_directory(self):
        with Mind() as mind:
            base_dir = mind.base_dir
            self.assertTrue(base_dir.exists())

        self.assertFalse(base_dir.exists())

    def test_unknown_memory_reference_raises_key_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mind = Mind(base_dir=tmp_dir)

            with self.assertRaises(KeyError):
                mind.add_codelet(CountingCodelet, inputs=["missing"])


if __name__ == "__main__":
    unittest.main()
