from pathlib import Path
import yaml

from modules.scripts import basedir

script_dir = Path(basedir())
settings_bot_filepath = script_dir.joinpath('settings_bot.yml')
settings_t2i_filepath = script_dir.joinpath('settings_t2i.yml')
settings_i2i_filepath = script_dir.joinpath('settings_i2i.yml')

DEFAULT_BOT_SETTINGS = {
    'enable_on_dm': True,
    'enable_on_guild': True,
    'cooltime_second': 60,
    'active_channels': [],
    'trigger_words': [
        '!gen',
    ]
}

DEFAULT_T2I_SETTINGS = {
    'negative_prompt': "(worst quality, bad quality:1.5)",
    'sampler_name': "UniPC",
    'steps': 50,
    'cfg_scale': 7.5,
    'width': 512,
    'height': 512,
    'batch_size': 1,
    'denoising_strength': None,
}

DEFAULT_I2I_SETTINGS = {
    'negative_prompt': "(worst quality, bad quality:1.5)",
    'sampler_name': "UniPC",
    'steps': 50,
    'cfg_scale': 7.5,
    'width': 512,
    'height': 512,
    'batch_size': 1,
    'denoising_strength': 0.7,
}

def read_bot_settings_file():
    with open(settings_bot_filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def read_t2i_settings_file():
    with open(settings_t2i_filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def read_i2i_settings_file():
    with open(settings_i2i_filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def init_setting_files():
    try:
        read_bot_settings_file()
    except FileNotFoundError:
        with open(settings_bot_filepath, 'w') as f:
            yaml.dump(DEFAULT_BOT_SETTINGS, f, sort_keys=False)

    try:
        read_t2i_settings_file()
    except FileNotFoundError:
        with open(settings_t2i_filepath, 'w') as f:
            yaml.dump({
                'negative_prompt': '',
                'sampler_name': 'UniPC',
                'steps': 30,
                'batch_size': 1,
            }, f, sort_keys=False)

    try:
        read_i2i_settings_file()
    except FileNotFoundError:
        with open(settings_i2i_filepath, 'w') as f:
            yaml.dump({
                'negative_prompt': '',
                'sampler_name': 'UniPC',
                'steps': 30,
                'batch_size': 1,
                'denoising_strength': 0.7,
            }, f, sort_keys=False)

    return [read_bot_settings(), read_t2i_settings(), read_i2i_settings_file()]

def read_bot_settings():
    return {
        **DEFAULT_BOT_SETTINGS,
        **read_bot_settings_file()
    }

def read_t2i_settings():
    return {
        **DEFAULT_T2I_SETTINGS,
        **read_t2i_settings_file()
    }

def read_i2i_settings():
    return {
        **DEFAULT_I2I_SETTINGS,
        **read_t2i_settings_file()
    }

init_setting_files()
