from __future__ import absolute_import

import click
import pkg_resources

import utils.logger as logger
from configuration.profile_config import add_profile, add_default_profile
from openai.CommandChat import CommandChat

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
    CommandChat(profile=profile, chat_log_id=id).chat(message)

@click.command()
@click.option('-desc', help=' Enter the description of the images you want')
@click.option('-num', count=True, help=' Enter the number to generate the specified number of images')
@click.option('-profile', help='Enable profile name')
def image(desc, num, profile):
    if num == 0:
        num = 1
    CommandChat(profile=profile).image_create(desc, num)


commandchat_operator.add_command(configure)
commandchat_operator.add_command(chat)
commandchat_operator.add_command(image)


def main():
    commandchat_operator()

if __name__ == '__main__':
    main()