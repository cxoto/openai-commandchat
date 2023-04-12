from __future__ import absolute_import

import click
import pkg_resources

import utils.logger as logger
from configuration.profile_config import add_profile, add_default_profile
from occ.CommandChat import CommandChat
from utils.CommonUtil import waiting_stop


VERSION = pkg_resources.require("commandchat")[0].version


@click.group()
@click.version_option(version=VERSION, prog_name='openai-commandchat')
def commandchat_operator():
    pass


@click.command()
@click.option('-profile', help='Enable profile name')
def configure(profile):
    if profile is not None:
        add_profile(profile)
    else:
        add_default_profile()


@click.command()
@click.argument('message')
@click.option('-id', help=' enter chat id, something like context')
@click.option('-profile', help='Enable profile name')
def chat(message, id, profile):
    try:
        CommandChat(profile=profile, chat_log_id=id).chat(message)
    except Exception as e:
        logger.log_g(str(e))
        waiting_stop()

size_map = {
    "s": "256x256",
    "S": "256x256",
    "m": "512x512",
    "M": "512x512",
    "l": "1024x1024",
    "L": "1024x1024"
}

@click.command()
@click.option('-desc', help=' Enter the description of the images you want')
@click.option('-size', help=' Enter the size(S/s,M/m,L/l): \n   small - 256x256 \n   middle  - 512x512 \n   large - 1024x1024')
@click.option('-num', count=True, help=' Enter the number to generate the specified number of images')
@click.option('-profile', help='Enable profile name')
def image(desc, size, num, profile):
    number = num if num > 0 else 1
    size = size_map.get(size)
    size_value = size if size != None else "512x512" 
    CommandChat(profile=profile).image_create(desc, size_value, number if number < 5 else 4)


commandchat_operator.add_command(configure)
commandchat_operator.add_command(chat)
commandchat_operator.add_command(image)


def main():
    commandchat_operator()
