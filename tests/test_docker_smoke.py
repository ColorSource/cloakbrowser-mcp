from __future__ import annotations

import os
import subprocess

import pytest


@pytest.mark.docker
def test_docker_compose_config():
    if os.environ.get("CLOAKBROWSER_MCP_RUN_DOCKER_TESTS") != "1":
        pytest.skip("Set CLOAKBROWSER_MCP_RUN_DOCKER_TESTS=1 to run Docker smoke test.")

    result = subprocess.run(
        ["docker", "compose", "config"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "cloakbrowser-mcp" in result.stdout
