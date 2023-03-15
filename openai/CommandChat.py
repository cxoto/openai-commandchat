import logging

import utils.logger as logger
from commons.config import get_env
import openai

openai.api_key = "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"



class CommandChat:

    def __init__(self, profile=None):
        profile = profile if profile != None else "default"
        self.api_key = get_env(profile, "api_key")
        self.content= ''


    def run(self, content):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=content,
            temperature=0,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stream=True,
            stop=[" Human:", " AI:"]
        )

        collected_events = []
        completion_text = ''
        # iterate through the stream of events
        for event in response:
            collected_events.append(event)  # save the event response
            event_text = event['choices'][0]['text']  # extract the text
            completion_text += event_text  # append the text
            print(event_text, end="")


if __name__ == '__main__':
    RecordSetClient()
