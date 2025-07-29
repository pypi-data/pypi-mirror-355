import mcp.types as types

syia_data_tools = [
    types.Tool(
        name="cdi_data_main",
        description="""Return CDI inspection rows and local PDF paths for a Synergy doc‑name.
        Get the doc_name from get_vessel_info tool and pass it to this tool doc_name=shippalmDoc""",
        inputSchema={
            "type": "object",
            "properties": {
                "doc_name": {"type": "string"},
            },
            "required": ["doc_name"],
        },
        # returns="list[dict]",
    )
]

tool_definitions = syia_data_tools