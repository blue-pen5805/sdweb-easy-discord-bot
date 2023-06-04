import launch

if not launch.is_installed("discord"):
    launch.run_pip(f"install discord", "discord")

if not launch.is_installed("deepl"):
    launch.run_pip(f"install deepl", "deepl")

if not launch.is_installed("openai"):
    launch.run_pip(f"install openai", "openai")
