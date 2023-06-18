import openai
import yaml
import json
from pathlib import Path

from modules.scripts import basedir

script_dir = Path(basedir())
functions_filepath = script_dir.joinpath('scripts', 'chatgpt', 'functions.yml')

def functions():
    with open(functions_filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def translate(prompt):
    system_prompt = '''
    You are a professional translator.
    Below are the rules you should always follow.

    Rules:
    1. Response should always only one line.
    2. Return the English and symbols in request as is.
    3. If non-English words are included in request, translate them into English.
    4. When translating, if translation is not possible, convert to Roman characters.
    '''

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": prompt }
            ],
            request_timeout=10,
            functions=[functions()[0]],
            function_call="auto",
            temperature=1.25,
            max_tokens=1000,
        )
        function_call = response.choices[0]['message']['function_call']
        if function_call:
            arguments = json.loads(function_call['arguments'])
            return arguments['translated'], arguments['need_to_create_text']
        else:
            return None, False
    except Exception as e:
        print(e)
        return None, False

def writing(prompt) -> str|None:
    system_prompt = '''
    You are a professional writer.
    Below are the rules you should always follow.

    Rules:
    1. Response should always only one line.
    2. Create sentences freely using your imagination.
    '''

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": prompt }
            ],
            request_timeout=10,
            functions=[functions()[1]],
            function_call="auto",
            temperature=1.5,
            max_tokens=1000,
        )
        function_call = response.choices[0]['message']['function_call']
        if function_call:
            arguments = json.loads(function_call['arguments'])
            return arguments['text']
        else:
            return None
    except Exception as e:
        print(e)
        return None

def request(text, api_key=None) -> str|None:
    if not api_key: return None
    openai.api_key = api_key

    translated, need_to_create_text = translate(text)
    if translated and need_to_create_text:
        return writing(translated)
    else:
        return translated
