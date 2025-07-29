import argparse
import gdown
import shutil
import os
import subprocess
from .json_utils import write_json,read_json

write_json("ollama_installed",True if shutil.which("ollama") else False)

def add_subparser(subparsers):
    download_parser = subparsers.add_parser(
        "download-model",
        help = "Download the commit message generator model."
    )

    setup_parser = subparsers.add_parser(
        "setup-model",
        help = "Setup the model."
    )

    download_parser.set_defaults(func=download)

    setup_parser.set_defaults(func=setup)

def download(args):
    model_downloaded = read_json("model_downloaded")

    if model_downloaded:
        print("The model is already downloaded.")
    else:
        model_folder = "cli_tool/ezcmt-model"
        try:
            os.mkdir(model_folder)
        except Exception:
            pass

        try:
            gdown.download("https://drive.google.com/uc?id=1yteR3xbPi12ATNAO9Ys1nX-iAd_7qpnB",
                        model_folder + "/Modelfile")
        except Exception:
            print("Modelfile already exists. It could be because you didnt delete the model files before uninstalling ezcmt. Run 'ezcmt delete-model' before uninstalling ezcmt to remove the model files.")

        try:
            gdown.download("https://drive.google.com/uc?id=1N3Jdi1Xctn4DRLhD6-jvu4Qe_m1yWD-E",
                        model_folder + "/ezcmt.gguf")
        except Exception:
            print("LoRA's file already exists. It could be because you didnt delete the model files before uninstalling ezcmt. Run 'ezcmt delete-model' before uninstalling ezcmt to remove the model files.")

        try:
            gdown.download("https://drive.google.com/uc?id=1uWTnCZJ2mR7fbJfrUWFSLjxOgT3YdxSg",
                        model_folder + "/qwen2.5-coder.gguf")
        except Exception:
            print("Base model's file already exists. It could be because you didnt delete the model files before uninstalling ezcmt. Run 'ezcmt delete-model' before uninstalling ezcmt to remove the model files.")

        print("Download done.")

        write_json("model_downloaded",True)

def setup(args):
    if read_json("setup_done"):
        print("Setup is already done.")
    else:
        if read_json("ollama_installed"):
            result = subprocess.Popen(["ollama","create","-f","cli_tool/ezcmt-model/Modelfile","_ezcmt"])
            if result.returncode == 0:
                print("An error occured. Perhaps Ollama isnt installed?")
            write_json("setup_done",True)
        else:
            print("Cannot setup when Ollama isnt installed. Install it at https://ollama.com/")