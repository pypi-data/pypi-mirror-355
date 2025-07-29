import asyncio
import logging
from pathlib import Path

import click

from co_datascientist.workflow_runner import workflow_runner
from . import co_datascientist_api, mcp_local_server
from .settings import settings

logging.basicConfig(level=settings.log_level)
logging.info(f"settings: {settings.model_dump()}")


@click.group()
@click.option('--reset-token', is_flag=True, help='Reset the API token')
@click.option('--dev', is_flag=True, help='Enable development mode (connect to local backend)')
def main(reset_token: bool, dev: bool):
    """Welcome to CoDatascientist CLI!"""
    print("Welcome to CoDatascientist CLI!")
    
    if dev:
        settings.enable_dev_mode()
    
    if reset_token:
        settings.delete_api_key()
    settings.get_api_key()

    try:
        print(f"connecting to co-datascientist server at {settings.backend_url}...")
        response = asyncio.run(co_datascientist_api.test_connection())
        print(f"server: {response}")
    except Exception as e:
        print(f"error from server: {e}")
        print("make sure that your token is correct, your can remove and reset the token using --reset-token flag.")
        if dev:
            print("Note: You're in development mode. Make sure your local backend is running.")
        exit(1)


@main.command()
def mcp_server():
    """Start the MCP server which allows agents to use CoDatascientist"""
    print("starting MCP server... Press Ctrl+C to exit.")
    asyncio.run(mcp_local_server.run_mcp_server())


@main.command()
@click.option('--script-path', required=True, type=click.Path(), help='Path to the python code to process, must be absolute path')
@click.option('--python-path', required=True, type=click.Path(), default="python", show_default=True,
              help='Path to the python interpreter to use')
def run(script_path, python_path):
    """Process a file"""
    print(f"Processing file: {script_path} with python interpreter executable: {python_path}")
    if not Path(script_path).exists():
        print("Python code file path doesn't exist.")
        return

    if not Path(script_path).is_absolute():
        print("Python code file path must be absolute.")
        return

    if python_path != "python":
        if not Path(python_path).exists():
            print("Python interpreter executable path doesn't exist.")
            return

        if not Path(python_path).is_absolute():
            print("Python interpreter executable path has to be either absolute or 'python'.")
            return

    code = Path(script_path).read_text()
    project_path = Path(script_path).parent
    asyncio.run(workflow_runner.run_workflow(code, python_path, project_path))


@main.command()
@click.option('--detailed', is_flag=True, help='Show detailed cost breakdown including all workflows and model calls')
def costs(detailed):
    """Show your usage costs and token consumption"""
    try:
        if detailed:
            response = asyncio.run(co_datascientist_api.get_user_costs())
            print(f"\n💰 Co-DataScientist Usage Details:")
            print(f"Total Cost: ${response['total_cost_usd']:.8f}")
            print(f"Total Tokens: {response['total_tokens']:,} ({response['total_input_tokens']:,} input + {response['total_output_tokens']:,} output)")
            print(f"Workflows: {response['workflows_count']}")
            if response.get('last_updated'):
                print(f"Last Updated: {response['last_updated']}")
            
            if response['workflows']:
                print(f"\n📊 Workflow Breakdown:")
                for workflow_id, workflow_data in response['workflows'].items():
                    print(f"  {workflow_id[:8]}... | ${workflow_data['cost']:.8f} | {workflow_data['input_tokens'] + workflow_data['output_tokens']:,} tokens")
                    if len(workflow_data['model_calls']) > 0:
                        print(f"    Model calls: {len(workflow_data['model_calls'])}")
                        for call in workflow_data['model_calls'][-3:]:  # Show last 3 calls
                            print(f"      • {call['model']}: ${call['cost']:.8f} ({call['input_tokens']}+{call['output_tokens']} tokens)")
                        if len(workflow_data['model_calls']) > 3:
                            print(f"      ... and {len(workflow_data['model_calls']) - 3} more calls")
        else:
            response = asyncio.run(co_datascientist_api.get_user_costs_summary())
            print(f"\n💰 Co-DataScientist Usage Summary:")
            print(f"Total Cost: ${response['total_cost_usd']:.8f}")
            print(f"Total Tokens: {response['total_tokens']:,}")
            print(f"Workflows Completed: {response['workflows_completed']}")
            if response.get('last_updated'):
                print(f"Last Updated: {response['last_updated']}")
            print(f"\n💡 Use '--detailed' flag for full breakdown")
        print()
    except Exception as e:
        print(f"Error getting costs: {e}")


if __name__ == "__main__":
    main()
