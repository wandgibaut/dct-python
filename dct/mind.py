# ****************************************************************************#
# Copyright (c) 2022  Wandemberg Gibaut                                       #
# All rights reserved. This program and the accompanying materials            #
# are made available under the terms of the MIT License                       #
# which accompanies this distribution, and is available at                    #
# https://opensource.org/licenses/MIT                                         #
#                                                                             #
# Contributors:                                                               #
#      W. Gibaut                                                              #
#                                                                             #
# ****************************************************************************#

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Type, Union
import json
import subprocess
import tempfile
import threading
import time

from dct.codelets import PythonCodelet


MemoryKind = str
CodeletFactory = Type[PythonCodelet]
CodeletInput = Union[PythonCodelet, CodeletFactory]


@dataclass
class MemoryConfig:
    name: str
    type: MemoryKind
    location: str
    group: list[str] = field(default_factory=list)

    def to_field_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "ip/port": self.location,
            "group": list(self.group),
        }


@dataclass
class CodeletRuntime:
    name: str
    codelet: PythonCodelet
    thread: Optional[threading.Thread] = None


class Mind:
    """Standalone in-process coordinator for DCT codelets and memories."""

    def __init__(
        self,
        name: str = "mind",
        base_dir: Optional[Union[str, Path]] = None,
        redis_host: str = "127.0.0.1",
        redis_port: int = 6379,
        start_redis: bool = False,
        redis_server_command: str = "redis-server",
        redis_save_seconds: int = 3600,
        redis_save_changes: int = 1,
    ) -> None:
        self.name = name
        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
        if base_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="dct-mind-")
            base_dir = self._temp_dir.name

        self.base_dir = Path(base_dir)
        self.codelets_dir = self.base_dir / "codelets"
        self.memories_dir = self.base_dir / "memories"
        self.codelets_dir.mkdir(parents=True, exist_ok=True)
        self.memories_dir.mkdir(parents=True, exist_ok=True)

        self.redis_host = redis_host
        self.redis_port = redis_port
        self.start_redis_process = start_redis
        self.redis_server_command = redis_server_command
        self.redis_save_seconds = redis_save_seconds
        self.redis_save_changes = redis_save_changes

        self.memories: dict[str, MemoryConfig] = {}
        self.codelets: dict[str, CodeletRuntime] = {}
        self._pending_initial_memories: dict[str, dict[str, Any]] = {}
        self._redis_process: Optional[subprocess.Popen[Any]] = None
        self._running = False

    @property
    def redis_location(self) -> str:
        return f"{self.redis_host}:{self.redis_port}"

    def add_memory(
        self,
        name: str,
        memory_type: MemoryKind = "local",
        location: Optional[Union[str, Path]] = None,
        initial_value: Optional[dict[str, Any]] = None,
        group: Optional[list[str]] = None,
    ) -> MemoryConfig:
        normalized_type = self._normalize_memory_type(memory_type)
        memory_location = self._resolve_memory_location(normalized_type, location)
        memory = MemoryConfig(
            name=name,
            type=normalized_type,
            location=memory_location,
            group=group or [],
        )
        self.memories[name] = memory

        if initial_value is not None and self._should_defer_initial_memory(memory):
            self._pending_initial_memories[name] = initial_value
        elif initial_value is not None:
            self._write_initial_memory(memory, initial_value)

        return memory

    def add_codelet(
        self,
        codelet: CodeletInput,
        name: Optional[str] = None,
        inputs: Optional[list[str]] = None,
        outputs: Optional[list[str]] = None,
        timestep: float = 0.1,
        enable: bool = True,
        lock: bool = False,
    ) -> PythonCodelet:
        codelet_name = name or self._infer_codelet_name(codelet)
        root_codelet_dir = self.codelets_dir / codelet_name
        root_codelet_dir.mkdir(parents=True, exist_ok=True)

        fields = {
            "name": codelet_name,
            "enable": enable,
            "lock": lock,
            "timestep": timestep,
            "inputs": self._memory_entries(inputs or []),
            "outputs": self._memory_entries(outputs or []),
        }
        self._write_fields(root_codelet_dir, fields)

        if isinstance(codelet, PythonCodelet):
            codelet.root_codelet_dir = root_codelet_dir
            codelet.fields = codelet.read_all_field()
            codelet_instance = codelet
        else:
            codelet_instance = codelet(name=codelet_name, root_codelet_dir=root_codelet_dir)

        self.codelets[codelet_name] = CodeletRuntime(name=codelet_name, codelet=codelet_instance)
        return codelet_instance

    def run_once(self) -> None:
        for runtime in self.codelets.values():
            codelet = runtime.codelet
            codelet.fields = codelet.read_all_field()
            if bool(codelet.fields.get("enable")) and not bool(codelet.fields.get("lock")):
                activation = codelet.calculate_activation()
                codelet.proc(activation)

    def run(self, steps: Optional[int] = None, duration: Optional[float] = None) -> None:
        if steps is not None:
            for _ in range(steps):
                self.run_once()
            return

        self.start()
        if duration is None:
            return

        try:
            time.sleep(duration)
        finally:
            self.stop()

    def start(self) -> None:
        if self._running:
            return

        if self.start_redis_process:
            self._start_redis()
            self._flush_pending_initial_memories()

        self._running = True
        for runtime in self.codelets.values():
            runtime.codelet.change_field("enable", True)
            runtime.thread = threading.Thread(
                target=runtime.codelet.run,
                name=f"dct-codelet-{runtime.name}",
                daemon=True,
            )
            runtime.thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        if not self._running and self._redis_process is None:
            return

        for runtime in self.codelets.values():
            runtime.codelet.change_field("enable", False)

        for runtime in self.codelets.values():
            if runtime.thread is not None:
                runtime.thread.join(timeout=timeout)
                runtime.thread = None

        self._stop_redis()
        self._running = False

    def close(self) -> None:
        self.stop()
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def __enter__(self) -> "Mind":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _memory_entries(self, memory_names: list[str]) -> list[dict[str, Any]]:
        entries = []
        for memory_name in memory_names:
            if memory_name not in self.memories:
                raise KeyError(f"Memory {memory_name!r} was not added to this mind")
            entries.append(self.memories[memory_name].to_field_entry())
        return entries

    def _write_fields(self, root_codelet_dir: Path, fields: dict[str, Any]) -> None:
        with (root_codelet_dir / "fields.json").open("w", encoding="utf-8") as fields_file:
            json.dump(fields, fields_file)

    def _write_initial_memory(self, memory: MemoryConfig, initial_value: dict[str, Any]) -> None:
        memory_value = {
            "name": memory.name,
            "type": memory.type,
            "ip/port": memory.location,
            "group": list(memory.group),
            **initial_value,
        }

        if memory.type == "local":
            memory_path = Path(memory.location) / f"{memory.name}.json"
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            with memory_path.open("w", encoding="utf-8") as memory_file:
                json.dump(memory_value, memory_file)
            return

        import dct

        if memory.type == "redis":
            dct.set_redis_memory(memory.location, memory.name, None, None, full_memory=memory_value)
        elif memory.type == "mongo":
            for field_name, value in memory_value.items():
                dct.set_mongo_memory(memory.location, memory.name, field_name, value)
        else:
            raise ValueError(f"Unsupported memory type: {memory.type}")

    def _should_defer_initial_memory(self, memory: MemoryConfig) -> bool:
        return memory.type == "redis" and self.start_redis_process and self._redis_process is None

    def _flush_pending_initial_memories(self) -> None:
        for memory_name, initial_value in list(self._pending_initial_memories.items()):
            self._write_initial_memory(self.memories[memory_name], initial_value)
            del self._pending_initial_memories[memory_name]

    def _resolve_memory_location(self, memory_type: MemoryKind, location: Optional[Union[str, Path]]) -> str:
        if location is not None:
            return str(location)
        if memory_type == "local":
            return str(self.memories_dir)
        if memory_type == "redis":
            return self.redis_location
        if memory_type == "mongo":
            return "mongodb://localhost:27017"
        raise ValueError(f"Unsupported memory type: {memory_type}")

    def _normalize_memory_type(self, memory_type: MemoryKind) -> MemoryKind:
        normalized = memory_type.lower()
        if normalized == "json":
            return "local"
        if normalized in {"local", "redis", "mongo"}:
            return normalized
        raise ValueError(f"Unsupported memory type: {memory_type}")

    def _infer_codelet_name(self, codelet: CodeletInput) -> str:
        if isinstance(codelet, PythonCodelet):
            return codelet.name or codelet.__class__.__name__
        return codelet.__name__

    def _start_redis(self) -> None:
        if self._redis_process is not None:
            return

        self.memories_dir.mkdir(parents=True, exist_ok=True)
        self._redis_process = subprocess.Popen(
            [
                self.redis_server_command,
                "--port",
                str(self.redis_port),
                "--save",
                str(self.redis_save_seconds),
                str(self.redis_save_changes),
                "--dir",
                str(self.memories_dir),
                "--dbfilename",
                "memory.rdb",
            ]
        )

    def _stop_redis(self) -> None:
        if self._redis_process is None:
            return

        self._redis_process.terminate()
        try:
            self._redis_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._redis_process.kill()
            self._redis_process.wait(timeout=2)
        finally:
            self._redis_process = None
