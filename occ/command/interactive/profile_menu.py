"""Interactive menu for profile configuration"""

import questionary
from questionary import Style
import occ.utils.logger as logger


# Custom style for questionary
CUSTOM_STYLE = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
])


def interactive_profile_menu():
    """Interactive menu for managing profiles"""
    while True:
        action = questionary.select(
            "Profile Configuration - What would you like to do?",
            choices=[
                'List all profiles',
                'Configure profile',
                'Delete profile',
                'Exit'
            ],
            style=CUSTOM_STYLE
        ).ask()
        
        if action is None or action == 'Exit':
            break
        elif action == 'List all profiles':
            from occ.command.commands.profile import list_cmd
            list_cmd.callback()
        elif action == 'Configure profile':
            interactive_configure_profile()
        elif action == 'Delete profile':
            interactive_delete_profile()


def interactive_configure_profile():
    """Interactive profile configuration"""
    from occ.commons import config as cfg
    from occ.configuration.profile_config import configure_profile
    
    profiles = cfg.get_profiles()
    
    if profiles:
        choices = profiles + ['[Create New Profile]']
        selection = questionary.select(
            "Select a profile to configure:",
            choices=choices,
            style=CUSTOM_STYLE
        ).ask()
        
        if not selection:
            return
        
        if selection == '[Create New Profile]':
            profile_name = questionary.text("Enter new profile name:", style=CUSTOM_STYLE).ask()
            if profile_name:
                configure_profile(profile_name)
        else:
            configure_profile(selection)
    else:
        logger.log_g("No profiles found. Creating default profile...")
        configure_profile('default')


def interactive_delete_profile():
    """Interactive profile deletion"""
    from occ.commons import config as cfg
    from occ.command.commands.profile import delete_cmd
    
    profiles = [p for p in cfg.get_profiles() if p != 'default']
    
    if not profiles:
        logger.log_r("No profiles to delete (cannot delete 'default' profile)")
        return
    
    profile = questionary.select(
        "Select a profile to delete:",
        choices=profiles,
        style=CUSTOM_STYLE
    ).ask()
    
    if profile:
        delete_cmd.callback(profile, False)

