#!/usr/bin/env python3
from __future__ import absolute_import

import click
import pkg_resources

import utils.logger as logger
from configuration.profile_config import add_profile, add_default_profile
from openai.CommandChat import CommandChat

VERSION = pkg_resources.require("recordset")[0].version


def debug_logging(verbose):
    if verbose == 1:
        click.echo(click.style("Debugging Level is set", fg='green'))
        logger.enable_debug()


@click.group()
@click.version_option(version=VERSION, prog_name='openai-commandchat')
def commandchat_operator():
    pass


@click.command()
@click.option('--profile', help='Enable profile name')
@click.option('-d', count=True, help='Enable debugger logging')
def configure(profile, d):
    debug_logging(d)
    if profile is not None:
        add_profile(profile)
    else:
        add_default_profile()


@click.command()
@click.option('--profile', help=' profile name')
@click.option('-d', count=True, help='Enable debugger logging')
def rlist(profile, d):
    debug_logging(d)
    CommandChat(profile).run("list")


@click.command()
@click.option('-c', help=' enter something you want to say ')
@click.option('-d', count=True, help='Enable debugger logging')
def c(c, d):
    debug_logging(d)
    CommandChat(profile).run(c)


commandchat_operator.add_command(configure)
commandchat_operator.add_command(c)


if __name__ == '__main__':  # pragma: no cover
    commandchat_operator()
