# AWS CLI MCP Server

A simple MCP server that provides a bridge to execute AWS CLI commands.

## Tools

- **aws_cli_read**: For read-only AWS operations (listing, describing resources)
- **aws_cli_write**: For write operations (creating, modifying, deleting resources)

## Setup

### 1. Configure AWS CLI

Set up AWS SSO following [this guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html#sso-configure-profile-token-auto-sso).

### 2. Run Server

**Using locally:**
```bash
uvx --env AWS_PROFILE=your-sso-profile aws-cli-mcp-server
```

**Using MCP configuration:**
```json
{
  "mcpServers": {
    "aws-cli-mcp-server": {
      "command": "uvx",
      "args": ["aws-cli-mcp-server"],
      "env": {
        "AWS_PROFILE": "your-sso-profile"
      }
    }
  }
}
```

**Using access keys:**
```json
{
  "mcpServers": {
    "aws-cli-mcp-server": {
      "command": "uvx",
      "args": ["aws-cli-mcp-server"],
      "env": {
        "AWS_ACCESS_KEY_ID": "your-access-key",
        "AWS_SECRET_ACCESS_KEY": "your-secret-key"
      }
    }
  }
}
```