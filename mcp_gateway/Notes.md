MCP Gateway

This is the tool layer.

It is not an agent.

It provides deterministic tools and its definitions like light destination , price etc

The important part is:

mcp.run(
    transport="http",
    host="127.0.0.1",
    port=9000,
)

Current FastMCP documentation describes this HTTP transport as Streamable HTTP and the server is available at /mcp.

MCP endpoint : http://127.0.0.1:9000/mcp
