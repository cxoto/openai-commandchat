import configparser
import logging
import os

import importlib

import occ.utils.logger as logger

config = configparser.ConfigParser()


def get_home_path():
    homedir = os.environ.get('HOME', None)
    if os.name == 'nt':
        homedir = os.path.expanduser('~')
    return homedir


def get_config_path():
    homedir = get_home_path()
    if not homedir:
        logger.log_r("Home Directory Not found!! Set Envirnoment `HOME` ")
        exit()
    logger.debug("Home Directory : " + homedir)
    config_file_temp = os.path.join(homedir + "/.occ/config")
    logger.debug("Config File Location : " + config_file_temp)
    if not os.path.exists(config_file_temp):
        logger.log_r("ERROR: No Config file present")
        try:
            os.makedirs(os.path.dirname(config_file_temp))
        except OSError as exc:  # Guard against race condition
            logger.log_r("Directory found! but not config file")

        logger.debug("Creating config file")
        file = open(config_file_temp, "w")
        file.write("[default]")
        file.close()

    logger.debug(config.read(config_file_temp))
    return config_file_temp


config_file = get_config_path()


def set_env(profile, key, value):
    config.set(profile, key, value)
    write_config()


def add_profile(profile):
    if config.has_section(profile):
        logger.log_r(profile + " Section already exists!!")
        return

    config.add_section(profile)
    write_config()


def write_config():
    with open(config_file, 'w') as configfile:
        config.write(configfile)


def get_env(profile, key):
    logger.debug("Searching in profile : " + profile)
    logger.debug("Searching in key" + key)
    if config.has_option(profile, key):
        return config.get(profile, key)
    logger.debug("Not found in current profile")
    if config.has_option('default', key):
        return config.get('default', key)

    logger.debug("No Value Found in DEFAULT SECTION as well")
    return None


def get_default_env(key):
    if config.has_option('default', key):
        return config.get('default', key)
    return None


def get_profiles():
    """Get all profile names (excluding model-specific sections)"""
    profiles = []
    for section in config.sections():
        # Filter out model-specific sections (e.g., profile_name.model_name)
        if '.' not in section:
            profiles.append(section)
    return profiles


def get_profile_models(profile):
    """Get all models configured for a specific profile"""
    models = []
    prefix = f"{profile}."
    for section in config.sections():
        if section.startswith(prefix):
            model_name = section[len(prefix):]
            models.append(model_name)
    return models


def get_model_config(profile, model):
    """Get configuration for a specific model under a profile"""
    section = f"{profile}.{model}"
    if not config.has_section(section):
        return None
    return {
        'api_key': config.get(section, 'api_key', fallback=None),
        'api_base_url': config.get(section, 'api_base_url', fallback=None),
        'api_version': config.get(section, 'api_version', fallback=None)
    }


def set_model_config(profile, model, api_key, api_base_url, api_version):
    """Set configuration for a specific model under a profile"""
    section = f"{profile}.{model}"
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'api_key', api_key)
    config.set(section, 'api_base_url', api_base_url)
    config.set(section, 'api_version', api_version)
    write_config()


def remove_profile(profile):
    """Remove a profile and all its associated models"""
    if config.has_section(profile):
        config.remove_section(profile)
    # Remove all model sections
    prefix = f"{profile}."
    for section in list(config.sections()):
        if section.startswith(prefix):
            config.remove_section(section)
    write_config()


def profile_exists(profile):
    """Check if a profile exists"""
    return config.has_section(profile)


def get_profile_default_prompt(profile):
    """Get the default prompt for a profile"""
    return get_env(profile, 'default_prompt')


def set_profile_default_prompt(profile, prompt_key):
    """Set the default prompt for a profile"""
    if not profile_exists(profile):
        return False, f"Profile '{profile}' does not exist"
    set_env(profile, 'default_prompt', prompt_key)
    return True, f"Default prompt for profile '{profile}' set to '{prompt_key}'"


def log_config():
    level_input = 'DEBUG'
    if level_input == 'DEBUG':
        print(level_input)
        logging.basicConfig(level=logging.DEBUG)


def find_version():
    version = importlib.metadata.version("commandchat")
    print(version)
