import openai

CHAT_GPT_SYSTEM_PROMPT = '''
You are a professional EN.

Below are the rules you should always follow.
Rules are listed in order of priority.

Definitions:
- REQUEST: user messages
- RESPONSE: Texts translated from user messages or created based on user messages.

Rules:
1. RESPONSE should always be returned in English
2. RESPONSE should always only one line.
3. If REQUEST contains instructions, follow them.
4. Return the English and symbols in REQUEST as is.
5. If non-English words are included in REQUEST, translate them into English.
6. When translating, if translation is not possible, convert to Roman characters.
7. If you are unable to respond to a REQUEST due to policy violations or other reasons, please return a creative piece of writing about animals.
'''

def translate_with_chatgpt(text, api_key=None):
    if not api_key: return None

    try:
        openai.api_key = api_key
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.75,
            max_tokens=256,
            request_timeout=5,
            messages=[
                { "role": "system", "content": CHAT_GPT_SYSTEM_PROMPT },
                { "role": "user", "content": "REQUEST: ゴリラとジジイ。slow motion" },
                { "role": "assistant", "content": "RESPONSE: gorilla and old man. slow motion" },
                { "role": "user", "content": "REQUEST: pig, dog, fusion, [犬:running:10]" },
                { "role": "assistant", "content": "RESPONSE: pig, dog, fusion, [dog:running:10]" },
                { "role": "user", "content": "REQUEST: あっかり～ん" },
                { "role": "assistant", "content": "RESPONSE: Akkari~n" },
                { "role": "user", "content": "REQUEST: 少女が自らの残虐性に気づく物語を創作してください。" },
                { "role": "assistant", "content": "RESPONSE: Sophie was always a sweet, innocent girl - until one day, she stumbled upon a gruesome sight. In her backyard, she saw her dog laying on the ground, dead with its stomach cut open. At first, she was horrified, but as she kept staring at it, she began to feel a rush of excitement. The thought of taking control over life and death seemed to thrill her in ways she never experienced before." },
                { "role": "user", "content": f"REQUEST: {text} (Please answer in English.)" }
            ]
        )

        return completion.choices[0]['message']['content'].replace('RESPONSE: ', '')
    except Exception as e:
        print(e)
        return None
