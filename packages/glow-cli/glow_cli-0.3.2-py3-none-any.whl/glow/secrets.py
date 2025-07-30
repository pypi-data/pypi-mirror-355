import os
from pathlib import Path

import yaml
import getpass

from glow.colors import cprint, mask_print
from glow.constants import ASCII_ART, GLOW_SECRETS_FILE
from glow.utils.yaml import open_yaml_conf


class GlowSecrets:
    """
    Manage the secrets for glow
    """

    def __init__(self, glow_secrets_file: str = GLOW_SECRETS_FILE):
        self.glow_secrets_file = glow_secrets_file
        self.secrets = dict()

        self.load_secrets()

    def load_secrets(self):
        """
        Load all the secrets
        """
        if not Path(self.glow_secrets_file).exists():
            Path(self.glow_secrets_file).parent.mkdir(parents=True, exist_ok=True)
            return {}
        yaml_conf = open_yaml_conf(str(self.glow_secrets_file))
        for name, item in yaml_conf["secrets"].items():
            item_value = item["value"]
            os.environ[name] = f"{item_value}"
            self.secrets[name] = f"{item_value}"
        return self.secrets

    def update_secret_env(self, name: str, value: str):
        """
        Update the secret with name
        """
        if not Path(self.glow_secrets_file).exists():
            Path(self.glow_secrets_file).parent.mkdir(parents=True, exist_ok=True)
            yaml_conf = {"secrets": {}}
        else:
            yaml_conf = open_yaml_conf(str(self.glow_secrets_file))
            if yaml_conf is None:
                yaml_conf = {"secrets": {}}

        if name in yaml_conf["secrets"]:
            yaml_conf["secrets"][name]["value"] = value
        else:
            yaml_conf["secrets"][name] = {
                "name": name,
                "value": value,
            }
        self.secrets[name] = value

        # writing it back to the file
        with open(self.glow_secrets_file, "w") as f:
            f.write(yaml.dump(yaml_conf))

    def remove_secret_key(self, name: str):
        """
        Remove the secret key
        """
        if not Path(self.glow_secrets_file).exists():
            Path(self.glow_secrets_file).parent.mkdir(parents=True, exist_ok=True)
            return {}
        yaml_conf = open_yaml_conf(str(self.glow_secrets_file))
        if name in yaml_conf["secrets"]:
            del yaml_conf["secrets"][name]
        with open(self.glow_secrets_file, "w") as f:
            f.write(yaml.dump(yaml_conf))

    def get_or_set_secrets(self, name: str) -> str:
        """
        Get config value with name
        """
        if name in self.secrets:
            return self.secrets[name]
        value = os.environ.get(name)
        if value is not None:
            return value
        else:
            cprint(f"Secret [{name}] NOT FOUND", ["red"])
            return self.setup_secret(name)

    def setup_secret(self, name: str) -> str:
        """
        Setup value to a secret with name
        """
        if name in self.secrets:
            cprint(f"🌟 Secret [{name}] already exists, this will overwriting {name}", ["yellow"])
        cprint(f"Please input the value of the secret {name}", ["yellow"])
        value = getpass.getpass(f"🤫🔑 set value to [{name}]: ")
        self.update_secret_env(name, value)
        cprint(f"🔑✨ {name}={mask_print(value)} ADDED ", ["cyan"])
        return value

    def __getitem__(self, name: str) -> str:
        """
        Syntax sugar for getting secret value
        """
        return self.get_or_set_secrets(name)

    def __call__(self, *args, **data):
        """
        Actions to take when run this in glow command line
        """
        if len(args) == 0 and len(data) == 0:
            # print help because no args has been passed
            secrets_help()
            return

        if args[0].lower() == "get":
            if len(args) == 1:
                cprint("Please input the name of the secret", ["yellow"])
                name = input("🤫 Name: ")
            else:
                name = args[1]
            secret_value = self.get_or_set_secrets(name)
            if secret_value:
                print(secret_value, end="")
            else:
                cprint(f"❌ Secret {name} NOT FOUND ✅", ["red"])
            return

        if (args[0].lower() == "list") or "list" in data:
            self.load_secrets()
            print("🤫 Available secrets:")
            for key, value in self.secrets.items():
                cprint(f"  - {key} = {mask_print(value)}", ["cyan"])

        elif (args[0].lower() == "add") or "add" in data:
            if len(args) == 1:
                cprint("Please input the name of the secret", ["yellow"])
                name = input("🤫 Name: ")
            else:
                name = args[1]

            if len(args) < 3:
                value = self.setup_secret(name)
            else:
                value = args[2]

            self.update_secret_env(name, value)
            cprint(f"🔑✨ {name}={mask_print(value)} ADDED ✅", ["green"])

        elif (args[0].lower() == "remove") or "remove" in data:
            if len(args) < 2:
                cprint("Please specify the name of the secret to remove", ["yellow"])
                return

            name = args[1]
            if name in self.secrets:
                self.remove_secret_key(name)
                cprint(f"❌ Secret {name} REMOVED ✅", ["green"])
            else:
                cprint(f"❌ Secret {name} NOT FOUND ✅", ["red"])
            return
        else:
            cprint("🔑 Please specify the action", ["yellow"])
            secrets_help()
            return


def secrets_help():
    cprint("✨ GLOW SECRETS", ["green", "bold"])
    cprint(ASCII_ART, ["green"])

    cprint(
        """
    Please use `g secrets add SOME_API_TOKEN` to add a secret

    You can use `g secrets list` to list all the secrets on your local machine

    `g remove SOME_API_TOKEN` to remove a secret
    """,
        ["green"],
    )


GLOW_SECRETS = GlowSecrets()
