"""Stdio transport tests: run the server as a subprocess and talk JSON-RPC to it.

Run with: python3 -m unittest discover tests
No Google credentials are needed; tool calls that need auth are expected to fail cleanly.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent / "scripts" / "server.py"


def run_server(stdin: bytes) -> tuple[bytes, bytes, int]:
    with tempfile.TemporaryDirectory() as tmp:
        env = {
            **os.environ,
            # Point auth at an empty directory so no real token is ever used.
            "YOUTUBE_TOKEN_FILE": str(Path(tmp) / "token.json"),
            "YOUTUBE_CLIENT_SECRETS": str(Path(tmp) / "client_secret.json"),
        }
        proc = subprocess.run(
            [sys.executable, str(SERVER)],
            input=stdin,
            capture_output=True,
            timeout=20,
            env=env,
        )
    return proc.stdout, proc.stderr, proc.returncode


def ndjson(*messages: object) -> bytes:
    return b"".join(
        (m if isinstance(m, bytes) else json.dumps(m).encode()) + b"\n" for m in messages
    )


def responses(stdout: bytes) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
}


class StdioTransportTest(unittest.TestCase):
    def test_handshake_and_tools_list(self) -> None:
        out, err, code = run_server(
            ndjson(
                INIT,
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            )
        )
        self.assertEqual(code, 0, err.decode())
        replies = responses(out)
        # The notification must not get a reply.
        self.assertEqual([r["id"] for r in replies], [1, 2])
        self.assertEqual(replies[0]["result"]["protocolVersion"], "2025-06-18")
        names = {tool["name"] for tool in replies[1]["result"]["tools"]}
        self.assertIn("youtube_update_video", names)

    def test_malformed_line_does_not_kill_server(self) -> None:
        out, err, code = run_server(
            ndjson(INIT, b"not json", b"\xff\xfe", {"jsonrpc": "2.0", "id": 3, "method": "ping"})
        )
        self.assertEqual(code, 0, err.decode())
        replies = responses(out)
        self.assertEqual(len(replies), 4)
        for bad in replies[1:3]:
            self.assertIsNone(bad["id"])
            self.assertEqual(bad["error"]["code"], -32700)
        self.assertEqual(replies[3], {"jsonrpc": "2.0", "id": 3, "result": {}})

    def test_batch_and_bare_values_are_rejected_not_fatal(self) -> None:
        out, err, code = run_server(
            ndjson(
                [{"jsonrpc": "2.0", "id": 4, "method": "ping"}],
                42,
                {"jsonrpc": "2.0", "id": 5, "method": "ping"},
            )
        )
        self.assertEqual(code, 0, err.decode())
        replies = responses(out)
        self.assertEqual([r["error"]["code"] for r in replies[:2]], [-32600, -32600])
        self.assertEqual(replies[2]["id"], 5)

    def test_null_params_are_tolerated(self) -> None:
        out, err, code = run_server(
            ndjson({"jsonrpc": "2.0", "id": 6, "method": "initialize", "params": None})
        )
        self.assertEqual(code, 0, err.decode())
        self.assertIn("result", responses(out)[0])

    def test_tool_failure_is_reported_as_tool_error(self) -> None:
        out, err, code = run_server(
            ndjson(
                INIT,
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {"name": "youtube_update_video", "arguments": {"video_id": "x"}},
                },
            )
        )
        self.assertEqual(code, 0, err.decode())
        reply = responses(out)[1]
        self.assertTrue(reply["result"]["isError"])

    def test_content_length_framing_still_supported(self) -> None:
        body = json.dumps(INIT).encode()
        out, err, code = run_server(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.assertEqual(code, 0, err.decode())
        header, _, payload = out.partition(b"\r\n\r\n")
        self.assertTrue(header.startswith(b"Content-Length:"))
        self.assertEqual(json.loads(payload)["id"], 1)


if __name__ == "__main__":
    unittest.main()
