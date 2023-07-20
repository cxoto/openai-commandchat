import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='commandchat',
    version='0.0.4',
    entry_points={
        'console_scripts': [
            'occ = occ.command.__main__:main'
        ]
    },
    author="xoto",
    author_email="xxx.tao.c@gmail.com",
    description="use command to chat with openai models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/",
    packages=setuptools.find_packages(),
    install_requires=[
        'click',
        'Image',
        'openai'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
