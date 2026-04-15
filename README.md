# dct-python

Python package for the Distributed Cognitive Toolkit (DCT), a toolkit for building distributed cognitive architectures from codelets and shared memory objects.

The package provides:

- `PythonCodelet`, an abstract base class for Python codelets.
- Helpers for reading and writing memory objects through local JSON files, Redis, MongoDB, or HTTP/TCP endpoints.
- A small Flask API server for node/codelet metadata and memory access.
- Utilities for creating Docker-backed nodes and drawing network connectivity.

## Installation

From the repository root:

```bash
python -m pip install .
```

For editable development:

```bash
python -m pip install -e .
```

The package metadata currently supports Python 3.9 and 3.10. The core package can be imported without Redis, MongoDB, or Flask installed, but those dependencies are required when using the corresponding runtime features.

## Codelets

Create a codelet by subclassing `PythonCodelet` and implementing `proc`.

```python
from dct.codelets import PythonCodelet


class MyCodelet(PythonCodelet):
    def calculate_activation(self) -> float:
        return 1.0

    def proc(self, activation: float) -> None:
        print(f"activation={activation}")
```

Each codelet directory is expected to contain a `fields.json` file. A minimal example:

```json
{
  "enable": true,
  "lock": false,
  "timestep": 0.1,
  "inputs": [],
  "outputs": []
}
```

Instantiate a codelet with the directory that contains `fields.json`:

```python
codelet = MyCodelet(name="my-codelet", root_codelet_dir="/path/to/codelet")
codelet.run()
```

## Memory Helpers

Local JSON memory:

```python
import dct

memory = dct.get_local_memory("/path/to/memories", "working_memory")
dct.set_local_memory("/path/to/memories", "working_memory", "value", {"state": "updated"})
```

Generic memory access:

```python
memory = dct.get_memory_object("working_memory", "/path/to/memories", "local")
dct.set_memory_object("working_memory", "/path/to/memories", "local", "value", 42)
```

Supported connection types are:

- `local`
- `redis`
- `mongo`
- `tcp`

## Server

The server exposes HTTP endpoints for node metadata, codelet metadata, memory reads/writes, and idea reads/writes.

Run it with:

```bash
ROOT_NODE_DIR=/path/to/node python -m dct.server 127.0.0.1:5000
```

Common endpoints:

- `GET /get_node_info`
- `GET /get_codelet_info/<codelet_name>`
- `GET /get_memory/<memory_name>`
- `POST /set_memory/`
- `GET /get_idea/<idea_name>`
- `POST /set_idea/`

## Utilities

`dct/utils.py` includes helper commands for Docker-backed nodes and network drawings.

Show the available options:

```bash
python dct/utils.py --help
```

Example network drawing:

```bash
python dct/utils.py --option draw-network --list-of-nodes 127.0.0.1:9998,127.0.0.1:9997
```

## Tests

The test suite uses Python's standard `unittest` runner, so it does not require pytest.

Run all tests:

```bash
python -m unittest discover -v
```

Run a syntax check:

```bash
python -m compileall dct tests
```

## Development Notes

This package is still alpha software. Some runtime integrations depend on external services:

- Redis-backed memories require a running Redis server.
- Mongo-backed memories require a running MongoDB server.
- HTTP/TCP memory access requires a running DCT node server.
- Docker node utilities require Docker and the expected DCT node scripts/images.

Keep changes covered by tests where possible, especially for codelet field handling, memory helpers, and server request parsing.
