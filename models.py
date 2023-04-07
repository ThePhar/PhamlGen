import datetime
import os
from typing import List, Tuple

import yaml


class YAMLDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YAMLDumper, self).increase_indent(flow, False)


class YAMLSettings:
    name: str = "Player {player}"
    game: str = "Archipelago"
    description: str = f"Auto-generated with PhamlGen on {datetime.datetime.now().strftime('%a, %b %d %Y @ %H:%M')}."
    requires = {"version": "0.3.7", "plando": ""}
    settings: dict = {}

    def __init__(self, rolled_generation, version, plando, name_override=None):
        self.requires["version"] = version
        self.requires["plando"] = plando
        self.settings = {}

        for attr in dir(rolled_generation):
            if attr.startswith("_"):
                continue

            # Convert settings to YAML valid settings.
            setting = getattr(rolled_generation, attr)
            if attr == "name":
                self.name = setting
                continue
            if attr == "game":
                self.game = setting
                continue

            try:
                if isinstance(setting.value, set):
                    self.settings[attr] = list(setting.value)
                else:
                    self.settings[attr] = setting.current_key
            except AttributeError:
                yaml_settings = self.get_alttp_setting(attr, setting)
                for yaml_attr, yaml_setting in yaml_settings:
                    self.settings[yaml_attr] = yaml_setting
            except LookupError:
                self.settings[attr] = setting.value
            except TypeError:
                self.settings[attr] = setting.value

        # If a name override was submitted, override the name.
        if name_override:
            self.settings["name"] = name_override

    @staticmethod
    def get_alttp_setting(attr, setting) -> List[Tuple[str, any]]:
        """
        I only have to do this because not all of alttp's options are moved over and they're different in code! wtf
        """

        # glitches_required
        if attr == "logic":
            if setting == "noglitches":
                return [("glitches_required", "none")]
            if setting == "nologic":
                return [("glitches_required", "nologic")]
            if setting == "owglitches":
                return [("glitches_required", "overworld_glitches")]
            if setting == "minorglitches":
                return [("glitches_required", "minor_glitches")]
            if setting == "hybridglitches":
                return [("glitches_required", "hybrid_major_glitches")]

        # entrance_shuffle
        if attr == "shuffle":
            if setting == "vanilla":
                return [("entrance_shuffle", "none")]

            return [("entrance_shuffle", setting)]

        # goals
        if attr == "goal":
            if setting == "ganonpedestal":
                return [("goals", "ganon_pedestal")]
            if setting == "triforcehunt":
                return [("goals", "triforce_hunt")]
            if setting == "localtriforcehunt":
                return [("goals", "local_triforce_hunt")]
            if setting == "ganontriforcehunt":
                return [("goals", "ganon_triforce_hunt")]
            if setting == "localganontriforcehunt":
                return [("goals", "local_ganon_triforce_hunt")]
            if setting == "icerodhunt":  # Why?
                return [("goals", "ice_rod_hunt")]

            return [("goals", setting)]

        # item_pool
        if attr == "difficulty":
            return [("item_pool", setting)]

        # timer
        if attr == "timer":
            if not setting:
                return [("timer", "none")]
            if setting == "timed-ohko":
                return [("timer", "timed_ohko")]
            if setting == "timed-countdown":
                return [("timer", "timed_countdown")]

            return [("timer", setting)]

        # misery_mire_medallion and turtle_rock_medallion
        if attr == "required_medallions":
            for index, medallion in enumerate(setting):
                if medallion == "ether":
                    setting[index] = "Ether"
                elif medallion == "quake":
                    setting[index] = "Quake"
                elif medallion == "bombos":
                    setting[index] = "Bombos"

            return [("misery_mire_medallion", setting[0]), ("turtle_rock_medallion", setting[1])]

        return [(attr, setting)]

    def output(self, pg_version: str, file_name: str, output_dir: str):
        meta = fr"""{self.yaml_header(pg_version, self.requires["version"], file_name)}

# Your name in-game. Spaces will be replaced with underscores and there is a 16-character limit.
name: {self.name}

# Used to describe your yaml. Useful if you have multiple files.
description: {self.description}

# Requirements the Archipelago generator must fulfil to generate this world successfully.
requires:
    version: {self.requires["version"]}
    plando: {self.requires["plando"] if self.requires["plando"] else "''"}

# The name of the game to be played for this session.
game: {self.game}

# All the rolled settings for this game.
"""

        with open(output_dir + file_name, "w+") as file:
            file.write(meta)
            yaml.dump(
                {self.game: self.settings}, file, indent=4, width=120, default_flow_style=False, Dumper=YAMLDumper
            )

    def output_append(self, pg_version: str, file_name: str, output_dir: str):
        meta = fr"""{self.yaml_header(pg_version, self.requires["version"], file_name)}

# Your name in-game. Spaces will be replaced with underscores and there is a 16-character limit.
name: {self.name}

# Used to describe your yaml. Useful if you have multiple files.
description: {self.description}

# Requirements the Archipelago generator must fulfil to generate this world successfully.
requires:
    version: {self.requires["version"]}
    plando: {self.requires["plando"] if self.requires["plando"] else "''"}

# The name of the game to be played for this session.
game: {self.game}

# All the rolled settings for this game.
"""

        if not os.path.exists(os.path.join(output_dir, file_name)):
            file = open(output_dir + file_name, "w+")
            file.close()

        with open(output_dir + file_name, "a+") as file:
            file.write("---\n")
            file.write(meta)
            yaml.dump(
                {self.game: self.settings}, file, indent=4, width=120, default_flow_style=False, Dumper=YAMLDumper
            )

    @staticmethod
    def yaml_header(pg_version: str, ap_version: str, file_name: str):
        pg_version_text = f"Generated with PhamlGen v{pg_version}"
        ap_version_text = f"Validated with Archipelago v{ap_version}"
        header = [
            "#############################",
            "##                           ",
            "##       7!^!??!^:.          ",
            "##  .!JJY##G#&&###BGP5J!:    ",
            "##   .~J#&#d############B5   ",
            "##    ..5#BB##&###########   ",
            "##       ?&&&B5###########   ",
            "##      .:~!!^~&##########   ",
            "##             Y&#########   ",
            "##              Y########B   ",
            "##    meow.     ~###BB###B   ",
            "##                           ",
            "#############################",
        ]

        # Expand top and bottom parts with #s.
        header[0] = header[0].ljust(118, "#")
        header[-1] = header[-1].ljust(118, "#")

        header[2] += file_name
        header[4] += pg_version_text
        header[5] += ap_version_text
        header[9] += "(c) 2023 PhamlGen - Zach 'Phar' Parks"
        header[10] += "https://github.com/thePhar/PhamlGen"

        for index, _ in enumerate(header):
            header[index] = header[index].ljust(118, " ")
            header[index] += "##"

        return "\n".join(header)
