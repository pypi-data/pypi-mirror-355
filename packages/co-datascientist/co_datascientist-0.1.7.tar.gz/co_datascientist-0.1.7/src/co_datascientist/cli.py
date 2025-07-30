import asyncio
import logging
from pathlib import Path

import click
from yaspin import yaspin

from co_datascientist.workflow_runner import workflow_runner
from . import co_datascientist_api, mcp_local_server
from .settings import settings

logging.basicConfig(level=settings.log_level)
logging.info(f"settings: {settings.model_dump()}")


@click.group()
@click.option('--reset-token', is_flag=True, help='Reset the API token')
@click.option('--reset-openai-key', is_flag=True, help='Reset the OpenAI API key')
@click.option('--dev', is_flag=True, help='Enable development mode (connect to local backend)')
def main(reset_token: bool, reset_openai_key: bool, dev: bool):
    """Welcome to CoDatascientist CLI!"""
    print("Welcome to CoDatascientist CLI!")
    
    if dev:
        settings.enable_dev_mode()
    
    if reset_token:
        settings.delete_api_key()
    
    if reset_openai_key:
        settings.delete_openai_key()
    
    settings.get_api_key()
    
    # Check for existing OpenAI key without prompting (users can add it with 'openai_key' command)
    if not reset_openai_key:
        settings.get_openai_key(prompt_if_missing=False)

    try:
        with yaspin(text=f"Connecting to co-datascientist server at {settings.backend_url}...", color="cyan") as spinner:
            response = asyncio.run(co_datascientist_api.test_connection())
            spinner.ok("✅ ")
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
    
    print(f"🚀 Starting Co-DataScientist workflow for: {script_path}")
    with yaspin(text="Processing your code...", color="magenta") as spinner:
        try:
            asyncio.run(workflow_runner.run_workflow(code, python_path, project_path))
            spinner.ok("✅ ")
        except Exception as e:
            spinner.fail("❌ ")
            raise


@main.command()
@click.option('--detailed', is_flag=True, help='Show detailed cost breakdown including all workflows and model calls')
def costs(detailed):
    """Show your usage costs and token consumption"""
    try:
        # Get usage status with remaining money info
        with yaspin(text="Fetching usage data...", color="blue") as spinner:
            usage_status = asyncio.run(co_datascientist_api.get_user_usage_status())
            spinner.ok("✅ ")
        
        if detailed:
            with yaspin(text="Loading detailed breakdown...", color="green") as spinner:
                response = asyncio.run(co_datascientist_api.get_user_costs())
                spinner.ok("✅ ")
            print(f"\n💰 Co-DataScientist Usage Details:")
            print(f"Total Cost: ${response['total_cost_usd']:.8f}")
            print(f"Usage Limit: ${usage_status['limit_usd']:.2f}")
            print(f"Remaining: ${usage_status['remaining_usd']:.2f}")
            print(f"Usage: {usage_status['usage_percentage']:.1f}% of limit")
            if usage_status['is_blocked']:
                print(f"🚨 Status: BLOCKED (limit exceeded)")
            elif usage_status['usage_percentage'] >= 80:
                print(f"⚠️  Status: Approaching limit ({usage_status['usage_percentage']:.1f}%)")
            else:
                print(f"✅ Status: Active ({usage_status['usage_percentage']:.1f}% used)")
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
            with yaspin(text="Loading usage summary...", color="green") as spinner:
                response = asyncio.run(co_datascientist_api.get_user_costs_summary())
                spinner.ok("✅ ")
            print(f"\n💰 Co-DataScientist Usage Summary:")
            print(f"Total Cost: ${response['total_cost_usd']:.8f}")
            print(f"Usage Limit: ${usage_status['limit_usd']:.2f}")
            print(f"Remaining: ${usage_status['remaining_usd']:.2f} ({usage_status['usage_percentage']:.1f}% used)")
            
            # Status indicator
            if usage_status['is_blocked']:
                print(f"🚨 Status: BLOCKED - Free tokens exhausted!")
                print(f"   You've used ${usage_status['current_usage_usd']:.2f} of your ${usage_status['limit_usd']:.2f} limit.")
            elif usage_status['usage_percentage'] >= 80:
                print(f"⚠️  Status: Approaching limit - {usage_status['usage_percentage']:.1f}% used")
            else:
                print(f"✅ Status: Active - {usage_status['usage_percentage']:.1f}% of limit used")
            
            print(f"Total Tokens: {response['total_tokens']:,}")
            print(f"Workflows Completed: {response['workflows_completed']}")
            if response.get('last_updated'):
                print(f"Last Updated: {response['last_updated']}")
            print(f"\n💡 Use '--detailed' flag for full breakdown")
        print()
    except Exception as e:
        print(f"Error getting costs: {e}")
        # If the new endpoint isn't available, fall back to old behavior
        try:
            if detailed:
                response = asyncio.run(co_datascientist_api.get_user_costs())
                print(f"\n💰 Co-DataScientist Usage Details:")
                print(f"Total Cost: ${response['total_cost_usd']:.8f}")
                print(f"Total Tokens: {response['total_tokens']:,}")
                print(f"Workflows: {response['workflows_count']}")
            else:
                response = asyncio.run(co_datascientist_api.get_user_costs_summary())
                print(f"\n💰 Co-DataScientist Usage Summary:")
                print(f"Total Cost: ${response['total_cost_usd']:.8f}")
                print(f"Total Tokens: {response['total_tokens']:,}")
                print(f"Workflows Completed: {response['workflows_completed']}")
        except Exception as fallback_error:
            print(f"Error getting basic costs: {fallback_error}")


@main.command()
def status():
    """Quick check of your usage status and remaining balance"""
    try:
        with yaspin(text="Checking status...", color="yellow") as spinner:
            usage_status = asyncio.run(co_datascientist_api.get_user_usage_status())
            spinner.ok("✅ ")
        
        print(f"\n🔍 Quick Usage Status:")
        print(f"Used: ${usage_status['current_usage_usd']:.2f} / ${usage_status['limit_usd']:.2f}")
        print(f"Remaining: ${usage_status['remaining_usd']:.2f}")
        
        # Show OpenAI key status
        openai_key = settings.get_openai_key(prompt_if_missing=False)
        if openai_key:
            print(f"🔑 Using your OpenAI account (unlimited usage)")
        else:
            print(f"🆓 Using TropiFlow's free tier")
        
        # Progress bar
        percentage = usage_status['usage_percentage']
        bar_width = 20
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"Progress: [{bar}] {percentage:.1f}%")
        
        # Status with emoji
        if usage_status['is_blocked']:
            print(f"🚨 BLOCKED - Free tokens exhausted! Contact support or wait for reset.")
            if not openai_key:
                print(f"💡 Add your OpenAI key with --reset-openai-key for unlimited usage")
        elif percentage >= 90:
            print(f"🟥 CRITICAL - Only ${usage_status['remaining_usd']:.2f} remaining!")
            if not openai_key:
                print(f"💡 Add your OpenAI key with --reset-openai-key for unlimited usage")
        elif percentage >= 80:
            print(f"🟨 WARNING - Approaching limit ({percentage:.1f}% used)")
        elif percentage >= 50:
            print(f"🟦 MODERATE - {percentage:.1f}% of limit used")
        else:
            print(f"🟩 GOOD - Plenty of free tokens remaining")
        
        print(f"\n💡 Use 'costs' command for detailed breakdown")
        print()
        
    except Exception as e:
        print(f"Error getting status: {e}")


@main.command()
@click.option('--remove', is_flag=True, help='Remove stored OpenAI key')
def openai_key(remove):
    """Manage your OpenAI API key for unlimited usage"""
    if remove:
        settings.delete_openai_key()
    else:
        current_key = settings.get_openai_key(prompt_if_missing=False)
        if current_key:
            print("✅ OpenAI key is currently configured.")
            print("   Your requests use your OpenAI account for unlimited usage.")
            print("   Use '--remove' flag to switch back to TropiFlow's free tier.")
        else:
            print("ℹ️  No OpenAI key configured. Using TropiFlow's free tier.")
            print("   Add your key for unlimited usage:")
            settings.get_openai_key(prompt_if_missing=True)


if __name__ == "__main__":
    main()
