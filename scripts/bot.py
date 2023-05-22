import asyncio
import discord
import logging
import datetime

from modules import shared
from scripts.action import txt2img
from scripts.settings import read_bot_settings, read_t2i_settings
from scripts.utils import translate, pil_to_discord_file, logging, is_dm, is_active_channels, is_mentioned, is_triggered

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

    async def generate(self, prompt):
        processed = txt2img(
            **{'prompt': prompt},
            **self.t2i_settings
        )

        return [processed.images, processed.infotexts]

    async def reply(self, message, prompt):
        user = message.author

        if not self.is_cooltime(user):
            translated = translate(prompt, api_key=shared.opts.edb_deepl_api_key).replace('\n', ' ')
            logging(f'Generating {prompt} `{translated}` (request from {user})')

            reply_message = await message.reply(f"Generating **{prompt}** `{translated}`", silent=True)
            [images, infotexts] = await self.generate(translated)

            await reply_message.edit(
                content=f"Generated **{prompt}** `{translated}`",
                attachments=[pil_to_discord_file(image) for image in images],
            )

            self.set_cooltime(user)
        else:
            await message.reply(f"cooldown at {self.cooldown_at(user).strftime('%H:%M:%S')}", silent=True)

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
        if message.author == self.user or not message.content: return

        self.reload_settings()
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

            return await message.reply('Failed to generate images!')

class DiscordBot:
    def __init__(self):
        self.client = None

    def start(self, token):
        if self.client: return

        self.client = Client(intents=intents)
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
