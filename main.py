import datetime
import os
import random
import shutil
import sys

import colorama
import inquirer
import yaml
from inquirer import errors

from models import YAMLSettings

OUTPUT_DIR = "./output/"
INPUT_DIR = "./input/"

PHAML_VERSION = "0.6.2"


def get_files_in_dir(folder):
    files = []
    for name in os.listdir(INPUT_DIR + folder + "/"):
        if os.path.isfile(os.path.join(INPUT_DIR + folder + "/", name)) and name.endswith(
                (".yaml", ".yml", ".json", ".txt")):
            files.append(name)

    return files


def validate_unique_worlds(answers, current):
    worlds = len(get_files_in_dir(answers["folder"]))
    try:
        if 0 < int(current) <= worlds:
            return True
    except Exception as error:
        raise errors.ValidationError(
            "", reason=f"You must enter an integer between 1-{worlds}.")

    raise errors.ValidationError(
        "", reason=f"Your world folder contains {worlds} worlds. Please pick a number between 1-{worlds}.")


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
                      choices=["Every World", "Randomly Pick One", "Pick # Unique Worlds"]),
        inquirer.Text("unique", f"How many worlds to generate?", validate=validate_unique_worlds,
                      ignore=lambda x: x["separate"] != "Pick # Unique Worlds")
    ]
    answers = inquirer.prompt(questions)
    files = get_files_in_dir(answers["folder"])
    new_input_dir = INPUT_DIR + answers["folder"] + "/"

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
            Generate.roll_settings(settings)

            # Validate name is safe as well.
            safe_name = False
            for s in ["{number}", "{NUMBER}", "{player}", "{PLAYER}"]:
                if s in settings["name"]:
                    safe_name = True
                    break

            if settings["requires"]["version"] != Utils.__version__:
                print(colorama.Fore.YELLOW + f"Valid! Potential Version Conflict - YAML 'Requires' AP "
                                             f"v{settings['requires']['version']}")
            elif not safe_name:
                print(colorama.Fore.YELLOW + "Valid! Name in file does not contain a '{number}', '{NUMBER}', '{player}'"
                                             ", '{PLAYER}' object. Could cause a name conflict!")
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
    elif answers["separate"] == "Pick # Unique Worlds":
        worlds_to_roll = int(answers["unique"])
        random.shuffle(potential_worlds)
        for i, world in enumerate(potential_worlds):
            if i >= worlds_to_roll:
                break

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
    finally:
        # Clear colors
        print(colorama.Back.RESET + colorama.Fore.RESET)
