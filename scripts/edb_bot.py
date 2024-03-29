import asyncio
import traceback
from io import BytesIO
import discord
import logging
import datetime
from PIL import Image

from modules import shared
from scripts.edb_action import txt2img, img2img
from scripts.edb_settings import read_bot_settings, read_t2i_settings, read_i2i_settings
from scripts.edb_utils import translate, normalize_text, pil_to_discord_file, logging, is_dm, is_active_channels, is_mentioned, is_triggered

intents = discord.Intents.default()
intents.message_content = True

class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reload_settings()
        self.last_request = {}

    def reload_settings(self):
        self.bot_settings = read_bot_settings()
        self.t2i_settings = read_t2i_settings()
        self.i2i_settings = read_i2i_settings()

    def is_cooltime(self, user):
        current_time = datetime.datetime.now()
        return self.cooldown_at(user, current_time=current_time) > current_time

    def set_cooltime(self, user):
        current_time = datetime.datetime.now()
        self.last_request[user.id] = current_time

    def cooldown_at(self, user, current_time=datetime.datetime.now()):
        previous_request = self.last_request.get(user.id)

        if previous_request:
            return previous_request + datetime.timedelta(seconds=self.bot_settings['cooltime_second'])

        return current_time

    def generate(self, prompt, image = None):
        if not image:
            processed = txt2img(**{
                **self.t2i_settings,
                **{'prompt': prompt},
            })
        else:
            processed = img2img(**{
                **self.i2i_settings,
                **{
                    'init_images': [image],
                    'prompt': prompt,
                },
            })

        return processed

    async def reply(self, message, prompt):
        user = message.author

        sem = asyncio.Semaphore(1)
        async with sem:
            if not self.is_cooltime(user):
                self.set_cooltime(user)

                await message.add_reaction("\N{Squared OK}")
                activity = discord.Game(f"{user.display_name}のために生成中……")
                await self.change_presence(activity=activity)

                try:
                    translated = normalize_text(
                        translate(
                            prompt,
                            deepl_api_key=shared.opts.edb_deepl_api_key,
                            chatgpt_api_key=shared.opts.edb_chatgpt_api_key,
                        )
                    )
                    logging(f'Generating {prompt} `{translated}` (request from {user})')

                    generate_message = self.bot_settings['messages']['generate'].replace("<prompt>", prompt).replace("<translated>", translated).replace("<author>", user.mention)

                    reply_message = await message.reply(generate_message, silent=True)
                    if message.attachments and message.attachments[0].content_type.startswith('image'):
                        data = await message.attachments[0].read()
                        image = Image.open(BytesIO(data))
                    else:
                        image = None

                    await asyncio.sleep(1)
                    p = self.generate(translated, image=image)

                    complete_message = self.bot_settings['messages']['complete'].replace("<prompt>", prompt).replace("<translated>", translated).replace("<author>", user.mention)

                    await reply_message.edit(
                        content=complete_message,
                        attachments=[pil_to_discord_file(image, p, p.all_seeds[i], p.all_prompts[i]) for i, image in enumerate(p.images)],
                    )

                    try:
                        await message.remove_reaction("\N{Squared OK}", self.user)
                    except:
                        pass
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                finally:
                    await self.change_presence(activity=None)
            else:
                cooltime_message = self.bot_settings['messages']['cooltime'].replace("<cooltime>", self.cooldown_at(user).strftime('%H:%M:%S'))

                await message.reply(cooltime_message, silent=True)

    # Event
    async def on_direct_message(self, message):
        if not self.bot_settings['enable_on_dm']: return

        prompt = message.content
        if prompt: await self.reply(message, prompt)

    async def on_mention(self, message):
        if not self.bot_settings['enable_on_guild']: return

        prompt = message.content.replace(f'<@{self.user.id}>', '').strip()
        if prompt: await self.reply(message, prompt)

    async def on_trigger_word(self, message, trigger_word):
        if not self.bot_settings['enable_on_guild']: return

        prompt = message.content.replace(trigger_word, '').strip()
        if prompt: await self.reply(message, prompt)

    # Override
    async def on_connect(self):
        logging('connected to discord')

    async def on_disconnect(self):
        logging('disconnected from discord')

    async def on_ready(self):
        logging(f'logged in as {self.user}')

    async def on_message(self, message):
        if not message.content: return

        self.reload_settings()
        if message.author.bot:
            if message.author.id not in self.bot_settings['acceptable_bots']: return

        try:
            if is_dm(message):
                return await self.on_direct_message(message)

            if is_active_channels(message, self.bot_settings['active_channels']):
                if is_mentioned(self.user, message):
                    return await self.on_mention(message)

                [triggered, trigger_word] = is_triggered(message, self.bot_settings['trigger_words'])
                if triggered:
                    return await self.on_trigger_word(message, trigger_word)
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            return await message.reply(self.bot_settings['messages']["failed"])

class DiscordBot:
    def __init__(self):
        self.client = None

    def start(self, token):
        if self.client: return

        self.client = Client(
            intents=intents,
            shard_count=1
        )
        async def runner():
            async with self.client:
                await self.client.start(token, reconnect=True)
        try:
            try:
                asyncio.run(runner())
            except KeyboardInterrupt:
                return
        except RuntimeError as e:
            print(e)

    def stop(self):
        try:
            if self.client and self.client.loop and self.client.is_ready():
                self.client.loop.create_task(self.client.close())
                self.client = None
        except RuntimeError:
            pass
