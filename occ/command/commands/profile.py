"""Profile configuration commands"""

import click
import occ.utils.logger as logger


@click.group(invoke_without_command=True)
@click.pass_context
def configure(ctx):
    """Configure OpenAI or Azure OpenAI profiles"""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, show interactive menu
        from occ.command.interactive.profile_menu import interactive_profile_menu
        interactive_profile_menu()


@click.command(name='profile')
@click.option('--profile', '-p', help='Specify profile name to configure')
def profile_cmd(profile):
    """Configure a profile"""
    if profile is not None:
        # If profile is specified, configure it directly
        from occ.configuration.profile_config import configure_profile
        configure_profile(profile)
    else:
        # No profile specified, show interactive selection
        from occ.configuration.profile_config import select_profile_interactively
        select_profile_interactively()


@click.command(name='delete')
@click.argument('profile', required=False)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def delete_cmd(profile, yes):
    """Delete a profile"""
    import questionary
    from occ.commons import config as cfg
    
    # If profile not provided, show interactive selection
    if not profile:
        profiles = [p for p in cfg.get_profiles() if p != 'default']
        
        if not profiles:
            logger.log_r("No profiles to delete (cannot delete 'default' profile)")
            return
        
        profile = questionary.select(
            "Select a profile to delete:",
            choices=profiles
        ).ask()
        
        if not profile:
            logger.log_g("Cancelled")
            return
    
    if not cfg.profile_exists(profile):
        logger.log_r(f"Profile '{profile}' does not exist")
        return
    
    if profile == 'default':
        logger.log_r("Cannot delete the 'default' profile")
        return
    
    # Confirm deletion
    if not yes:
        confirm = questionary.confirm(
            f"Are you sure you want to delete profile '{profile}'? This will also remove all associated models.",
            default=False
        ).ask()
        
        if not confirm:
            logger.log_g("Deletion cancelled")
            return
    
    cfg.remove_profile(profile)
    logger.log_g(f"Profile '{profile}' deleted successfully")


@click.command(name='list')
def list_cmd():
    """List all configured profiles"""
    from occ.commons import config as cfg
    from rich.table import Table
    from rich.console import Console
    
    profiles = cfg.get_profiles()
    if not profiles:
        logger.log_r("No profiles found. Run 'occ configure profile' to create one.")
        return
    
    console = Console()
    table = Table(title="Configured Profiles", show_header=True, header_style="bold magenta")
    table.add_column("Profile", style="cyan", width=20)
    table.add_column("API Type", style="green", width=15)
    table.add_column("Default Prompt", style="yellow", width=20)
    table.add_column("Models", style="blue")
    
    for profile in profiles:
        api_type = cfg.get_env(profile, 'api_server_type') or 'N/A'
        default_prompt = cfg.get_profile_default_prompt(profile) or 'None'
        models = cfg.get_profile_models(profile)
        models_str = ', '.join(models) if models else 'N/A'
        table.add_row(profile, api_type, default_prompt, models_str)
    
    console.print(table)


# Add subcommands to configure group
configure.add_command(profile_cmd)
configure.add_command(delete_cmd)
configure.add_command(list_cmd)

