import gradio as gr

from modules import script_callbacks, shared
from scripts.bot import DiscordBot

discord_bot = DiscordBot()

def on_ui_settings():
    shared.opts.add_option("edb_discord_bot_token", shared.OptionInfo('', "Discord Bot Token", section=("easy_discord_bot", "EasyDiscordBot")))
    shared.opts.add_option("edb_deepl_api_key", shared.OptionInfo('', "DeepL Api Key", section=("easy_discord_bot", "EasyDiscordBot")))

def on_ui_tabs():
    with gr.Blocks() as discord_bot_tab:
        start_button = gr.Button("Start")
        stop_button = gr.Button("Stop")

        def start():
            discord_bot.start(token=shared.opts.edb_discord_bot_token)

        start_button.click(
            fn=start
        )

        stop_button.click(
            fn=discord_bot.stop
        )

    return (discord_bot_tab, "DiscordBot", "discord_bot_tab"),

script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_before_reload(discord_bot.stop)
