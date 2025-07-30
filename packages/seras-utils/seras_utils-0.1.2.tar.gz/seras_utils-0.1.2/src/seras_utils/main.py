import json
from openai import OpenAI
import subprocess

client = OpenAI()

def dump_json(obj):
    print(json.dumps(obj, indent=2))

def respond(messages, schema):
    response = client.responses.create(
        input=messages,
        model='gpt-4o',
        text={'format':'json_schema',**schema}
    )
    text = response.output[0].content[0].text
    return text