from io import BytesIO
import discord
import deepl

from modules.images import FilenameGenerator
from modules.shared import opts
import scripts.edb_chatgpt as ChatGPT

def translate(text, deepl_api_key=None, chatgpt_api_key=None):
    translated = None
    if text.isascii(): return text

    if chatgpt_api_key:
        translated = ChatGPT.request(text, api_key=chatgpt_api_key)
    if deepl_api_key and not translated:
        translated = translate_with_deepl(text, api_key=deepl_api_key)

    if translated: return translated

    return text

def translate_with_deepl(text, api_key=None):
    if not api_key: return None

    translator = deepl.Translator(api_key)
    try:
        result = translator.translate_text(
            text,
            target_lang=deepl.Language.ENGLISH_BRITISH,
            preserve_formatting=True,
        )
    except Exception as e:
        print(e)
        return None

    return result.text

def normalize_text(text):
    return text.replace('\n', ' ').replace(': ', ':')

def pil_to_discord_file(image, p, seed, prompt):
    image_binary = BytesIO()
    image.save(image_binary, 'webp', quality=85)
    image_binary.seek(0)

    namegen = FilenameGenerator(p, seed, prompt, image)
    file_decoration = opts.samples_filename_pattern or "[seed]-[prompt_spaces]"
    filename = f"{namegen.apply(file_decoration)}.webp"

    return discord.File(fp=image_binary, filename=filename)

def logging(text):
    print(f'[DiscordBot] {text}')

def is_dm(message):
    return not message.guild

def is_active_channels(message, active_channels):
    if not active_channels: return True

    return message.channel.id in active_channels

def is_mentioned(user, message):
    if not user: return False

    mentioned_ids = list(map(lambda x: x.id, message.mentions))
    return user and (user.id in mentioned_ids)

def is_triggered(message, trigger_words):
    for trigger_word in trigger_words:
        if message.content.startswith(trigger_word):
            return [True, trigger_word]

    return [False, None]
