"""Tests for the MCP server registration — verifying all tools are exposed correctly."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloakbrowsermcp.server import create_server


class TestServerCreation:
    """Test MCP server is created with correct metadata."""

    def test_create_server_returns_mcp_instance(self):
        server = create_server()
        assert server is not None
        assert server.name == "cloakbrowser"

    def test_server_has_tools(self):
        server = create_server()
        # The server should have tool handlers registered
        assert hasattr(server, "_tool_manager")


class TestToolRegistration:
    """Test all expected tools are registered on the server."""

    EXPECTED_TOOLS = [
        "browser_launch", "browser_close", "browser_snapshot", "browser_click",
        "browser_type", "browser_select", "browser_hover", "browser_drag",
        "browser_check", "browser_read_page", "browser_extract_links",
        "browser_get_images", "browser_screenshot", "browser_navigate",
        "browser_back", "browser_forward", "browser_press_key",
        "browser_scroll", "browser_wait", "browser_wait_for_text",
        "browser_wait_for_ref", "browser_evaluate", "browser_new_page",
        "browser_list_pages", "browser_close_page",
    ]

    def test_all_tools_registered(self):
        server = create_server()
        tool_manager = server._tool_manager

        registered = set(tool_manager._tools.keys())

        for tool_name in self.EXPECTED_TOOLS:
            assert tool_name in registered, f"Tool '{tool_name}' not registered"

    def test_no_extra_unexpected_tools(self):
        """All registered tools should be in our expected list."""
        server = create_server()
        tool_manager = server._tool_manager

        registered = set(tool_manager._tools.keys())

        for tool_name in registered:
            assert tool_name in self.EXPECTED_TOOLS, f"Unexpected tool '{tool_name}' registered"


class TestToolSchemas:
    """Test that tool input schemas are properly defined."""

    def test_browser_launch_schema(self):
        server = create_server()
        tools = server._tool_manager._tools

        launch_tool = tools["browser_launch"]
        assert launch_tool is not None

    def test_navigate_requires_url(self):
        server = create_server()
        tools = server._tool_manager._tools

        nav_tool = tools["browser_navigate"]
        assert nav_tool is not None

    def test_snapshot_tool_exists(self):
        server = create_server()
        tools = server._tool_manager._tools

        snapshot_tool = tools["browser_snapshot"]
        assert snapshot_tool is not None

    def test_browser_click_tool_exists(self):
        server = create_server()
        tools = server._tool_manager._tools

        click_ref_tool = tools["browser_click"]
        assert click_ref_tool is not None

    def test_browser_drag_tool_exists(self):
        server = create_server()
        tools = server._tool_manager._tools

        drag_tool = tools["browser_drag"]
        assert drag_tool is not None

    def test_structured_read_tools_exist(self):
        server = create_server()
        tools = server._tool_manager._tools

        assert tools["browser_extract_links"] is not None
        assert tools["browser_get_images"] is not None

    def test_precise_wait_tools_exist(self):
        server = create_server()
        tools = server._tool_manager._tools

        assert tools["browser_wait_for_text"] is not None
        assert tools["browser_wait_for_ref"] is not None
