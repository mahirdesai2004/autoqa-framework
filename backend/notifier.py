def notify_user(message: str):
    """
    MCP-compatible notification hook.
    Can later be extended to email, Slack, MCP server, etc.
    """
    print(f"[MCP-NOTIFY] {message}")