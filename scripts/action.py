import gradio as gr

import modules.shared as shared
from modules import scripts
from modules.shared import opts, cmd_opts
from modules.processing import StableDiffusionProcessingTxt2Img, process_images

def init_default_script_args(script_runner):
    #find max idx from the scripts in runner and generate a none array to init script_args
    last_arg_index = 1
    for script in script_runner.scripts:
        if last_arg_index < script.args_to:
            last_arg_index = script.args_to
    # None everywhere except position 0 to initialize script args
    script_args = [None]*last_arg_index
    script_args[0] = 0

    # get default values
    with gr.Blocks(): # will throw errors calling ui function without this
        for script in script_runner.scripts:
            if script.ui(script.is_img2img):
                ui_default_values = []
                for elem in script.ui(script.is_img2img):
                    ui_default_values.append(elem.value)
                script_args[script.args_from:script.args_to] = ui_default_values
    return script_args

def txt2img(**kwargs):
    p = StableDiffusionProcessingTxt2Img(
        sd_model=shared.sd_model,
        outpath_samples=opts.outdir_samples or opts.outdir_txt2img_samples,
        outpath_grids=opts.outdir_grids or opts.outdir_txt2img_grids,
        seed_enable_extras=False,
        **kwargs
    )

    script_runner = scripts.scripts_txt2img
    p.scripts = script_runner
    p.script_args = init_default_script_args(script_runner)

    shared.state.begin()

    processed = script_runner.run(p, *p.script_args)
    if processed is None:
        processed = process_images(p)

    p.close()

    shared.state.end()
    shared.total_tqdm.clear()

    return processed
