"""Integration tests for the Patchbay Python worker bootstrap."""

import asyncio
import os
import sys
from pathlib import Path

from patchbay_protocol import DEFAULT_MAX_MESSAGE_BYTES, JsonRpcPeer

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "examples" / "hello-world"
PLUGIN_ID = "org.patchbay.examples.hello-world"


def test_worker_initializes_executes_and_shuts_down(tmp_path: Path) -> None:
    async def scenario() -> None:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "patchbay_core.worker",
            "--plugin-dir",
            str(PLUGIN_DIR),
            "--data-dir",
            str(tmp_path / "worker-data"),
            "--max-message-bytes",
            str(DEFAULT_MAX_MESSAGE_BYTES),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT,
            env=os.environ.copy(),
            limit=DEFAULT_MAX_MESSAGE_BYTES + 2,
        )

        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        peer = JsonRpcPeer(
            process.stdout,
            process.stdin,
            sender="host",
        )
        peer.start()

        try:
            initialized = await peer.request(
                "plugin.initialize",
                {
                    "protocol_version": "1.0",
                    "host_api_version": "1.0",
                    "plugin_id": PLUGIN_ID,
                    "configuration": {},
                    "granted_capabilities": [],
                },
                timeout=5,
            )

            assert initialized["status"] == "success"

            result = await peer.request(
                "plugin.execute",
                {
                    "execution_id": "worker-test-001",
                    "input": {"name": "Patchbay"},
                    "timeout_ms": 3000,
                },
                timeout=5,
            )

            assert result["status"] == "success"
            assert result["data"]["message"] == "Hello, Patchbay!"

            shutdown = await peer.request(
                "plugin.shutdown",
                {},
                timeout=5,
            )

            assert shutdown["status"] == "success"

        finally:
            await peer.close()

        return_code = await asyncio.wait_for(
            process.wait(),
            timeout=5,
        )
        stderr = await process.stderr.read()

        assert return_code == 0, stderr.decode(
            "utf-8",
            errors="replace",
        )

    asyncio.run(scenario())
