"""Image generation command"""

import click
from occ.CommandChat import CommandChat


# Size mapping for convenience
SIZE_MAP = {
    "s": "256x256",
    "S": "256x256",
    "m": "512x512",
    "M": "512x512",
    "l": "1024x1024",
    "L": "1024x1024"
}


@click.command()
@click.option('-desc', help='Enter the description of the images you want')
@click.option('-size',
              help='Enter the size(S/s,M/m,L/l): \n   small - 256x256 \n   middle  - 512x512 \n   large - 1024x1024')
@click.option('-num', count=True, help='Enter the number to generate the specified number of images')
@click.option('-profile', help='Enable profile name')
def image(desc, size, num, profile):
    """Generate images using AI"""
    number = num if num > 0 else 1
    size = SIZE_MAP.get(size)
    size_value = size if size is not None else "512x512"
    CommandChat(profile=profile).image_create(desc, size_value, number if number < 5 else 4)

