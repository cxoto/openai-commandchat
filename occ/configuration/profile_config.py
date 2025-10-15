import click

import occ.commons.config as config
import occ.utils.logger as logger


def add_default_profile():
    api_key = click.prompt(logger.style('\n[default] Your default api_key '),
                           default=config.get_default_env("api_key"), type=str)
    config.set_env('default', 'api_key', api_key)

    api_base_url = click.prompt(logger.style('\n[default] Your api_base_url(Optional) '),
                           default=config.get_default_env("api_base_url"), type=str)
    config.set_env('default', 'api_base_url', api_base_url)

    limit_history = click.prompt(logger.style('\n[default] Your default limit_history '),
                                 default=config.get_default_env("limit_history"), type=str)
    config.set_env('default', 'limit_history', limit_history)

    api_server_type = click.prompt(logger.style('\n[default] Your default api_server_type '),
                                 default=config.get_default_env("api_server_type"), type=str)
    config.set_env('default', 'api_server_type', api_server_type)

    api_version = click.prompt(logger.style('\n[default] Your default api_version '),
                                 default=config.get_default_env("api_version"), type=str)
    config.set_env('default', 'api_version', api_version)


def input_config_vars(profile_name, key_name, is_default_exist):
    if is_default_exist:
        default_value = config.get_env('default', key_name)
        user_input = click.prompt(logger.style('\ndefault value  ' + key_name), default=default_value, type=str)
    else:
        user_input = click.prompt(logger.style('\nYour ' + key_name), type=str)

    config.set_env(profile_name, key_name, user_input)


def add_profile(profile_name):
    config.add_profile(profile_name)
    config.set_env(profile_name, 'profile_name', profile_name)
    input_config_vars(profile_name, 'api_key', False)
    input_config_vars(profile_name, 'api_base_url', False)
    input_config_vars(profile_name, 'limit_history', False)
    input_config_vars(profile_name, 'api_server_type', False)
    input_config_vars(profile_name, 'api_version', False)
