import logging
import os
from pathlib import Path

import yaml

from glow.colors import cprint
from glow.constants import ASCII_ART, GLOW_CONFIGS_FILE, GLOW_CONFIG_OPTIONS
from glow.utils.yaml import open_yaml_conf


class GlowConfig:
    """
    Manage the configs for glow
    """

    def __init__(self, glow_configs_file: str = GLOW_CONFIGS_FILE):
        self.glow_configs_file = glow_configs_file
        self.configs = dict()

        self.load_configs()

    def load_configs(
        self,
    ):
        """
        Load all the configs
        """
        if not Path(self.glow_configs_file).exists():
            Path(self.glow_configs_file).parent.mkdir(parents=True, exist_ok=True)
            return {}
        yaml_conf = open_yaml_conf(str(self.glow_configs_file))
        for name, item in yaml_conf["configs"].items():
            item_value = item["value"]
            os.environ[name] = f"{item_value}"
            self.configs[name] = f"{item_value}"
        return self.configs

    def update_config_env(
        self,
        name: str,
        value: str,
    ):
        """
        Update the config with name
        """
        if not Path(self.glow_configs_file).exists():
            Path(self.glow_configs_file).parent.mkdir(parents=True, exist_ok=True)
            yaml_conf = {"configs": {}}
        else:
            yaml_conf = open_yaml_conf(str(self.glow_configs_file))
            if yaml_conf is None:
                yaml_conf = {"configs": {}}

        yaml_conf["configs"][name] = {
            "name": name,
            "value": value,
        }
        self.configs[name] = value

        # writing it back to the file
        with open(self.glow_configs_file, "w") as f:
            f.write(yaml.dump(yaml_conf))

    def options_seteup(self, name: str):
        options = GLOW_CONFIG_OPTIONS[name]
        cprint(
            f"🎛️ Please select the option for {name}, just input the index number and enter, "
            "if or just specify the configuration value if option is correct",
            [
                "header",
            ],
        )
        for i, option in enumerate(options):
            cprint(f"  [{i+1}]. {option}", ["header"])

        value = input("✅ Please select: ")
        try:
            value = int(value)
            if value > len(options):
                raise ValueError
            value = options[value - 1]
            cprint(f"✨ {name}={value} ADDED ", ["header"])
        except ValueError:
            # using the input value directly
            value = str(value)

        self.update_config_env(name, value)
        return value

    def setup_config(self, name: str) -> str:
        """
        Setup value to a config with name
        """
        if name in self.configs:
            cprint(f"🌟 Config [{name}] already exists, this will overwriting {name}", ["yellow"])
        if name in GLOW_CONFIG_OPTIONS:
            return self.options_seteup(name)
        cprint(f"Please input the value of the config {name}", ["yellow"])
        value = input(f"🎛️ set value to [{name}]: ")
        self.update_config_env(name, value)
        cprint(f"🎛️ ✨ {name}={value} ADDED ", ["cyan"])
        return value

    def remove_configs_key(
        self,
        name: str,
    ):
        if not Path(self.glow_configs_file).exists():
            Path(self.glow_configs_file).parent.mkdir(parents=True, exist_ok=True)
            return {}
        yaml_conf = open_yaml_conf(str(self.glow_configs_file))
        if name in yaml_conf["configs"]:
            del yaml_conf["configs"][name]
        with open(self.glow_configs_file, "w") as f:
            f.write(yaml.dump(yaml_conf))

    def get_or_set_configs(self, name: str) -> str:
        """
        Get config value with name
        """
        if name in self.configs:
            return self.configs[name]
        value = os.environ.get(name)
        if value is not None:
            return value
        else:
            cprint(f"🎛️ Config [{name}] NOT FOUND", ["red"])
            return self.setup_config(name)

    def __getitem__(self, name: str) -> str:
        """
        Syntax sugar for getting config value
        """
        return self.get_or_set_configs(name)

    def build_env(self, filename: str = ".env", *names) -> str:
        """
        build a .env file with configs
        """
        if len(names) == 0:
            self.load_configs()
            names = list(self.configs.keys())
        env = dict()
        for name in names:
            env[name] = self[name]
        with open(filename, "w") as f:
            for key, value in env.items():
                f.write(f'{key}="{value}"\n')
        return filename

    def __call__(self, *args, **data):
        """
        Actions to take when run this in glow command line
        """
        if len(args) == 0 and len(data) == 0:
            configs_help()
            return

        if args[0].lower() == "get":
            # no other arguments provided beyond 'get'
            if len(args) == 1:
                cprint("Please input the name of the config", ["yellow"])
                name = input("🎛️ Name: ")
                value = self[name]
                print(value, end="")
                return value
            else:
                name = args[1]
                value = self[name]
                print(value, end="")
                return value

        if (args[0].lower() == "list") or "list" in data:
            self.load_configs()
            print("🎛️ Available configs:")
            for key, value in self.configs.items():
                cprint(f"  - {key} = {value}", ["cyan"])

        elif (args[0].lower() == "add") or "add" in data:
            # in cases where name wasn't assigned
            if len(args) == 1:
                cprint("Please input the name of the config", ["yellow"])
                name = input("🎛️ Name: ")
            else:
                name = args[1]

            if len(args) < 3:
                return self.setup_config(name)
            else:
                value = args[2]

            self.update_config_env(name, value)

            cprint(f"🎛️ ✨ {name} ADDED ✅", ["cyan"])

        elif (args[0].lower() == "remove") or "remove" in data:
            name = args[1] if len(args) > 1 else data["remove"]
            if name in self.configs:
                del self.configs[name]
            self.remove_configs_key(name)
            cprint(f"❌ config {name} REMOVED ✅", ["cyan"])
            return
        else:
            cprint("🎛️ Please specify the action", ["yellow"])

            configs_help()
            return


def configs_help():
    cprint("✨ GLOW CONFIGS", ["cyan", "bold"])
    cprint(ASCII_ART, ["cyan"])

    cprint(
        """
    Please use `g configs add SOME_CONFIG_NAME` to add a config

    You can use `g configs list` to list all the configs on your local machine

    `g remove SOME_CONFIG_NAME` to remove a config
    """,
        ["cyan"],
    )


GLOW_CONFIGS = GlowConfig()
