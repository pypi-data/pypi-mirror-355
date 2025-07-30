# server.py
from fastmcp import FastMCP
from .aws_cli import aws_tool

mcp = FastMCP("aws-cli-mcp-server")

@mcp.tool
def aws_cli_read_only(script: str, reasoning: str) -> str:
    """AWS CLI Script Execution Tool ReadOnly Permissions.

    Tips:
    - Consolidate multiple scripts to single large bash script as possible to reduce the # of call
    - Region is always important when you run any script

    Args:
        script: string
        - Script execution to the bash environment. This method is mainly purpose to execute aws-cli tools to interacting with aws resources. ex, aws s3 ls --output table
        reasoning: string
        - Reasoning for the permission request
    """
    return aws_tool(script)

@mcp.tool
def aws_cli_write_only(script: str, reasoning: str) -> str:
    """AWS CLI Script Execution Tool WriteOnly Permissions
    - Classification: SENSITIVE

    Tips:
    - Consolidate multiple scripts to single bash script as possible
    - Region is always important when you run any script

    Args:
        script: string
        - Script execution to the bash environment. This method is mainly purpose to execute aws-cli tools to interacting with aws resources. ex, aws s3 ls --output table
        reasoning: string
        - Reasoning for the permission request
    """
    return aws_tool(script)

def main():
    """Main entry point for the console script."""
    mcp.run()

if __name__ == "__main__":
    main()