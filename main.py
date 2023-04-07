import datetime
import os
import random
import shutil
import sys

import colorama
import inquirer
import yaml

from models import YAMLSettings

OUTPUT_DIR = "./output/"
INPUT_DIR = "./input/"

PHAML_VERSION = "0.6.1"


def main():
    # Import Archipelago (this will also prompt to install any requirements).
    sys.path.append(os.path.abspath("./archipelago"))
    shutil.copyfile("./archipelago/host.yaml", "./host.yaml")
    from archipelago import Generate, Utils

    # Header
    header = f"PHAML GEN v{PHAML_VERSION} on Archipelago v{Utils.__version__}".ljust(114, " ")
    print("=" * (len(header) + 6))
    print("== " + header + " ==")
    print("=" * (len(header) + 6))

    # Preliminary validation.
    if not os.path.exists(INPUT_DIR):
        raise FileNotFoundError(f"Directory '{INPUT_DIR}' was not found to read files from.")
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    # Get all folders in input
    folders = []
    for name in os.listdir(INPUT_DIR):
        if os.path.isdir(os.path.join(INPUT_DIR, name)):
            folders.append(name)

    questions = [
        inquirer.List("folder", "Which folder do you wish to generate a seed from?", choices=folders),
        inquirer.List("separate", "Do you want each file to be its own world, or randomly pick one?",
                      choices=["Every World", "Randomly Pick One"]),
    ]
    answers = inquirer.prompt(questions)
    new_input_dir = INPUT_DIR + str(answers["folder"]) + "/"

    # Get all valid files in our input directory.
    files = []
    for name in os.listdir(new_input_dir):
        if os.path.isfile(os.path.join(new_input_dir, name)) and name.endswith((".yaml", ".yml", ".json")):
            files.append(name)

    if len(files) == 0:
        raise FileNotFoundError(f"No input files found in '{new_input_dir}'.")

    # Load and validate all yaml files.
    print(f"Found {len(files)} {'file' if len(files) == 1 else 'files'} in '{new_input_dir}'.\n")
    longest_name = len(max(files, key=len))
    potential_worlds = []
    for file in files:
        print(colorama.Fore.RESET + f"Validating '{file}'".ljust(longest_name + 20, "."), end="")
        with open(f"{new_input_dir}{file}") as raw:
            settings: dict = yaml.safe_load(raw)

            # Validate in AP's generator.
            plando = settings["requires"]["plando"] if "plando" in settings["requires"] else ""
            Generate.roll_settings(settings, Generate.PlandoSettings.from_option_string(plando))

            if settings["requires"]["version"] != Utils.__version__:
                print(colorama.Fore.YELLOW + f"Valid? Potential Version Issue - Requires AP v{settings['requires']['version']}")
            else:
                print(colorama.Fore.GREEN + "Valid!")

            potential_worlds.append(settings)

    print(colorama.Fore.RESET)

    file_name = datetime.datetime.now().strftime("Phaml__%m-%d-%Y__%H.%M.%S.yaml")
    if answers["separate"] == "Every World":
        for world in potential_worlds:
            rolled = Generate.roll_settings(world)
            final = YAMLSettings(rolled, Utils.__version__, "")
            final.output_append(PHAML_VERSION, file_name, OUTPUT_DIR)
    else:
        rolled = Generate.roll_settings(random.choice(potential_worlds))
        final = YAMLSettings(rolled, Utils.__version__, "")
        final.output(PHAML_VERSION, file_name, OUTPUT_DIR)

    print(
        colorama.Back.GREEN + colorama.Fore.BLACK + " SUCCESS " +
        colorama.Back.RESET + colorama.Fore.GREEN + f" Outputted to {OUTPUT_DIR}{file_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        if ex.__context__ is not None:
            print(colorama.Fore.RED + f"{ex}\n{ex.__context__}")
        else:
            print(colorama.Fore.RED + str(ex))

        print(
            "\n" +
            colorama.Back.RED + colorama.Fore.BLACK + " FAILURE " +
            colorama.Back.RESET + colorama.Fore.RED + " Please check your settings and try again!")
