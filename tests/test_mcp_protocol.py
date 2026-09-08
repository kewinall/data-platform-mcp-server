from mcp import Client

from data_platform_mcp.server import mcp


async def test_mcp_lists_tools_resources_and_prompts() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools.tools}
        assert {
            "describe_table",
            "get_table_metadata",
            "get_table_lineage",
            "analyze_sql_lineage",
            "search_etl_logs",
            "whoami",
        } <= tool_names

        resources = await client.list_resources()
        resource_uris = {str(resource.uri) for resource in resources.resources}
        assert "platform://capabilities" in resource_uris

        templates = await client.list_resource_templates()
        assert any("catalog://" in str(item.uri_template) for item in templates.resource_templates)

        prompts = await client.list_prompts()
        prompt_names = {prompt.name for prompt in prompts.prompts}
        assert {"incident_triage", "data_discovery"} <= prompt_names


async def test_mcp_reads_resource_renders_prompt_and_reports_local_identity() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        resource = await client.read_resource("platform://capabilities")
        assert resource.contents

        prompt = await client.get_prompt(
            "incident_triage",
            arguments={"dag_id": "quality_checks", "symptom": "validation failed"},
        )
        assert prompt.messages
        assert "quality_checks" in prompt.messages[0].content.text

        identity = await client.call_tool("whoami", {})
        assert identity.structured_content["client_id"] == "local-process"
