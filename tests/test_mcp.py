"""
Tests for Phase 3: MCP Tool Server and Antigravity Agent Integration
"""
import json
import pytest
from daemonx.mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_mcp_tool_listing():
    """TEST 6: Expose device, gallery, instagram, knowledge, task, cleanup tools through MCP."""
    server = create_mcp_server(mock_mode=True)
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]

    # Verify device tools
    assert "device_list" in tool_names
    assert "device_status" in tool_names
    assert "device_capture_screen" in tool_names
    assert "device_inspect_screen" in tool_names
    assert "device_launch_app" in tool_names
    assert "device_tap" in tool_names
    assert "device_swipe" in tool_names
    assert "device_scroll" in tool_names
    assert "device_press_back" in tool_names
    assert "device_input_text" in tool_names

    # Verify gallery tools
    assert "gallery_inventory" in tool_names
    assert "gallery_analyze_image" in tool_names
    assert "gallery_find_duplicates" in tool_names
    assert "gallery_search" in tool_names

    # Verify instagram tools
    assert "instagram_open_saved" in tool_names
    assert "instagram_inspect_current_reel" in tool_names
    assert "instagram_extract_visible_content" in tool_names
    assert "instagram_verify_reel" in tool_names
    assert "instagram_unsave_verified" in tool_names

    # Verify knowledge tools
    assert "knowledge_search" in tool_names
    assert "knowledge_create_record" in tool_names
    assert "knowledge_get_record" in tool_names
    assert "knowledge_export" in tool_names

    # Verify task tools
    assert "task_create" in tool_names
    assert "task_start" in tool_names
    assert "task_pause" in tool_names
    assert "task_resume" in tool_names
    assert "task_status" in tool_names

    # Verify cleanup tools
    assert "cleanup_preview" in tool_names
    assert "cleanup_quarantine" in tool_names
    assert "cleanup_restore" in tool_names


@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """TEST 7 & 8: Antigravity Agent tool execution and reasoning flow."""
    server = create_mcp_server(mock_mode=True)

    # 1. Test device_list
    res_list = await server.call_tool("device_list", {})
    text_content = res_list.content[0].text
    devices = json.loads(text_content)
    assert len(devices) >= 1
    assert devices[0]["model"] == "Android Device"

    # 2. Test device_inspect_screen
    res_inspect = await server.call_tool("device_inspect_screen", {"run_ocr": False})
    obs_data = json.loads(res_inspect.content[0].text)
    assert "elements" in obs_data
    assert "screen_type" in obs_data

    # 3. Test knowledge_create_record & knowledge_search
    res_create = await server.call_tool("knowledge_create_record", {
        "title": "Agent MCP Guide",
        "text": "How to connect Antigravity to local MCP servers for Android automation",
        "creator": "antigravity_engineer"
    })
    create_data = json.loads(res_create.content[0].text)
    assert "media_id" in create_data

    res_search = await server.call_tool("knowledge_search", {"query": "automation"})
    search_data = json.loads(res_search.content[0].text)
    assert len(search_data) >= 1

    # 4. Test cleanup_preview
    res_cleanup = await server.call_tool("cleanup_preview", {})
    cleanup_data = json.loads(res_cleanup.content[0].text)
    assert "total_candidates" in cleanup_data
