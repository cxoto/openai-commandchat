"""Prompt management commands"""

import click
import occ.utils.logger as logger


@click.group(invoke_without_command=True)
@click.pass_context
def prompt(ctx):
    """Manage prompt templates"""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, show interactive menu
        from occ.command.interactive.prompt_menu import interactive_prompt_menu
        interactive_prompt_menu()


@click.command(name='list')
def list_cmd():
    """List all available prompt templates"""
    from occ.commons.prompts import list_prompts
    from rich.table import Table
    from rich.console import Console
    
    console = Console()
    table = Table(title="Available Prompt Templates", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan", width=15)
    table.add_column("Name", style="green", width=25)
    table.add_column("Description", style="yellow", width=35)
    table.add_column("Type", style="blue", width=10)
    
    for key, value in list_prompts().items():
        prompt_type = "Built-in" if value.get("builtin", False) else "Custom"
        table.add_row(key, value["name"], value["description"], prompt_type)
    
    console.print(table)
    console.print("\n[bold green]Usage:[/bold green] occ chat -pt <key> \"your message\"")
    console.print("[bold green]Example:[/bold green] occ chat -pt translate \"你好世界\"")


@click.command(name='add')
@click.argument('key')
@click.option('--name', '-n', required=True, help='Display name for the prompt')
@click.option('--description', '-d', required=True, help='Brief description of the prompt')
@click.option('--system-prompt', '-s', required=True, help='The system prompt content')
def add_cmd(key, name, description, system_prompt):
    """Add a new custom prompt template"""
    from occ.commons.prompts import add_prompt
    
    success, message = add_prompt(key, name, description, system_prompt)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='modify')
@click.argument('key', required=False)
@click.option('--name', '-n', help='New display name')
@click.option('--description', '-d', help='New description')
@click.option('--system-prompt', '-s', help='New system prompt content')
def modify_cmd(key, name, description, system_prompt):
    """Modify an existing custom prompt template"""
    from occ.commons.prompts import modify_prompt, list_prompts, get_prompt
    import questionary
    
    # If key not provided, show interactive selection
    if not key:
        user_prompts = {k: v for k, v in list_prompts().items() if not v.get('builtin', False)}
        
        if not user_prompts:
            logger.log_r("No custom prompts to modify. Built-in prompts cannot be modified.")
            return
        
        key = questionary.select(
            "Select a prompt to modify:",
            choices=list(user_prompts.keys())
        ).ask()
        
        if not key:
            logger.log_g("Cancelled")
            return
        
        # If no options provided, ask interactively
        if not any([name, description, system_prompt]):
            current_prompt = get_prompt(key)
            
            fields = questionary.checkbox(
                "What would you like to modify?",
                choices=['Name', 'Description', 'System Prompt']
            ).ask()
            
            if not fields:
                logger.log_g("Cancelled")
                return
            
            if 'Name' in fields:
                name = questionary.text(
                    "Enter new name:",
                    default=current_prompt['name']
                ).ask()
            
            if 'Description' in fields:
                description = questionary.text(
                    "Enter new description:",
                    default=current_prompt['description']
                ).ask()
            
            if 'System Prompt' in fields:
                system_prompt = questionary.text(
                    "Enter new system prompt:",
                    default=current_prompt['system_prompt'],
                    multiline=True
                ).ask()
    
    if not any([name, description, system_prompt]):
        logger.log_r("At least one of --name, --description, or --system-prompt must be provided")
        return
    
    success, message = modify_prompt(key, name, description, system_prompt)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='remove')
@click.argument('key', required=False)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def remove_cmd(key, yes):
    """Remove a custom prompt template"""
    from occ.commons.prompts import remove_prompt, get_prompt, list_prompts
    import questionary
    
    # If key not provided, show interactive selection
    if not key:
        user_prompts = {k: v for k, v in list_prompts().items() if not v.get('builtin', False)}
        
        if not user_prompts:
            logger.log_r("No custom prompts to remove. Built-in prompts cannot be removed.")
            return
        
        key = questionary.select(
            "Select a prompt to remove:",
            choices=list(user_prompts.keys())
        ).ask()
        
        if not key:
            logger.log_g("Cancelled")
            return
    
    # Check if prompt exists
    prompt = get_prompt(key)
    if not prompt:
        logger.log_r(f"Prompt '{key}' not found")
        return
    
    if prompt.get("builtin", False):
        logger.log_r(f"Cannot remove built-in prompt '{key}'")
        return
    
    # Confirm removal
    if not yes:
        confirm = questionary.confirm(
            f"Are you sure you want to remove prompt '{key}'?",
            default=False
        ).ask()
        
        if not confirm:
            logger.log_g("Removal cancelled")
            return
    
    success, message = remove_prompt(key)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='show')
@click.argument('key', required=False)
def show_cmd(key):
    """Show detailed information about a prompt template"""
    from occ.commons.prompts import get_prompt, list_prompts
    from rich.console import Console
    from rich.panel import Panel
    import questionary
    
    # If key not provided, show interactive selection
    if not key:
        prompts_dict = list_prompts()
        if not prompts_dict:
            logger.log_r("No prompts available")
            return
        
        key = questionary.select(
            "Select a prompt to view:",
            choices=list(prompts_dict.keys())
        ).ask()
        
        if not key:
            logger.log_g("Cancelled")
            return
    
    prompt = get_prompt(key)
    if not prompt:
        logger.log_r(f"Prompt '{key}' not found")
        return
    
    console = Console()
    prompt_type = "Built-in" if prompt.get("builtin", False) else "Custom"
    
    console.print(f"\n[bold cyan]Key:[/bold cyan] {key}")
    console.print(f"[bold cyan]Name:[/bold cyan] {prompt['name']}")
    console.print(f"[bold cyan]Type:[/bold cyan] {prompt_type}")
    console.print(f"[bold cyan]Description:[/bold cyan] {prompt['description']}")
    console.print(f"\n[bold cyan]System Prompt:[/bold cyan]")
    console.print(Panel(prompt['system_prompt'], border_style="green"))


# Add subcommands to prompt group
prompt.add_command(list_cmd)
prompt.add_command(add_cmd)
prompt.add_command(modify_cmd)
prompt.add_command(remove_cmd)
prompt.add_command(show_cmd)

