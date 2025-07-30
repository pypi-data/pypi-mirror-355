import subprocess

async def run_aws_cli(command: str) -> str:
    """
    Run an AWS CLI command in an isolated environment.
    
    Args:
        command: AWS CLI command to execute

    Returns:
        Command output as string
    """
    try:
        # Execute AWS CLI command - include 'aws' prefix if not already there
        process = subprocess.run(
            ["bash", "-c", command],
            text=True,
            capture_output=True,
            timeout=300,  # 5 minute timeout
        )

        output = process.stdout
        if process.returncode != 0:
            output += f"\nError: {process.stderr}"

        return output

    except subprocess.TimeoutExpired:
        return "AWS CLI execution timed out after 5 minutes"
    except Exception as e:
        return f"Error executing AWS CLI: {str(e)}"


async def aws_tool(command: str) -> str:
    """
    MCP tool implementation for AWS CLI commands.

    Tips:
    - Consolidate multiple scripts to single bash script as possible
    - Region is always important when you run any script

    Args:
        command: AWS CLI command to execute

    Returns:
        Command output as string
    """
    result = await run_aws_cli(command)
    return result
