[English](README.md) | [中文](README-zh.md)

# openai-commandchat 

## Quick start

Use this command line to install the python packages:

```bash
pip3 install commandchat
```
Or use the following command line to guide you to a specific python version, if you have multiple versions of python locally
```bash
python3.x -m pip3 install commandchat
```



## Features
- You can set the api_key for openai with a simple command, and you can distinguish the key for your multiple accounts with a profile (default `default` if you don't specify it): `occ configure -profile`
- You can use the command `occ chat` to chat with the chat-GPT model `gpt-3.5-turbo`.
### To be implemented
- You can use the `occ image -desc` command with chat-GPT's model to describe the image you want to generate, giving you back a link to the image.
- You can use the `occ xxx -yyy` command to chat with a specified model of chat-GPT to complete a task you specify or give you advice.
- Others not yet thought of


## Requirements

A terminal with Python and pip installed:

- Installed python environment and python version >= 3.9
- Install the openai package

## Installing

```bash
pip3 install commandchat
```

## Uninstall

```bash
pip3 uninstall commandchat
```

## Feedback or questions
- You can send an email to: ``xxx.tao.c@gmail.com`` or ``xoto@outlook.be``

## License
MIT

