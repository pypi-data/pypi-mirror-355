from typing import Any, Dict

from glow.constants import ASCII_ART, GLOW_COMMANDS
from glow.colors import bcolors, cprint
from glow.utils.yaml import open_yaml_conf
from glow.manage import task_to_path, list_commands


def print_command(cmd_conf: Dict[str, Any], data: Dict[str, Any]) -> None:
    """
    print rendered command safely
    replace the secrets in the rendered command
    and print out the censored version of the rendered command
    """
    command_template = cmd_conf["command"]
    print(bcolors("\nRUNNING COMMAND:", "underline"))

    censored = dict()
    if "inputs" not in cmd_conf:
        censored.update(data)
    else:
        inputs_conf = cmd_conf["inputs"]
        for key, value in data.items():
            if key not in cmd_conf["inputs"]:
                censored[key] = value
                continue
            input_conf = inputs_conf[key]
            if input_conf.get("type", "text") == "secret":
                censored[key] = "*" * len(value)
            else:
                censored[key] = value
    censored_command = command_template.format(**censored)
    print(bcolors(f"{censored_command}", "header"))


def show_help_input(key: str, input_conf: Dict[str, Any]) -> None:
    """
    Print out the help for one input field
    - key: name of the input
    - input_conf: configuration of the input

    This is not only helpful when print out all the doc about a task
        but also when print out the help for a single input, eg. when
        throwing an error on one input field
    """
    cprint(f"\n--{key}:", ["green", "bold"])
    if "default" in input_conf:
        print(f"🏁 Default: {bcolors(input_conf['default'], 'yellow')}")
    if "description" in input_conf:
        print("🦄 Description:")
        print(f"{input_conf['description']}")
    if "examples" in input_conf:
        print("Examples:")
        for example in input_conf["examples"]:
            print("- " + str(bcolors(f"{example}", "yellow")))
    if "options" in input_conf:
        print("Options:")
        for option in input_conf["options"]:
            print("✨ " + str(bcolors(f"{option}", "yellow")))
    if "env_var" in input_conf:
        print(f"Environment variable (if not --{key}):" + str(bcolors(input_conf["env_var"], "yellow")))
    if "key_sequence" in input_conf:
        print("This value is affected by other inputs:")
        for input in input_conf["key_sequence"]:
            print("- " + str(bcolors(f"{input}", "yellow")))
    if "function" in input_conf:
        print("This value will be calculated by the function:" + str(bcolors(f"{input_conf['function']}", "yellow")))


def show_help(task: str) -> None:
    """
    Print out the help for the task

    {task}.yml will be the default task configuration file
    """
    path = task_to_path(task)
    cmd_conf = open_yaml_conf(path)
    cprint(
        ASCII_ART,
        [
            "cyan",
            "bold",
        ],
    )
    title = f"\n💫 TASK:\t{task}"
    cprint("-" * 30, ["cyan"])
    cprint("-" * 40, ["cyan"])
    cprint("-" * 50, ["cyan"])
    cprint(title, ["cyan", "bold"])

    if "description" in cmd_conf:
        cprint("\n🦄 Description:\n", ["blue", "bold"])
        print(cmd_conf["description"])

    if "command" in cmd_conf:
        cprint("📺 Command template:\n", ["blue", "bold"])
        cprint(cmd_conf["command"], "header")

    cprint("\n🌶 Inputs:\n", ["bold", "blue"])
    cprint("\n--help:", ["green", "bold"])
    print("input arguments")
    if "inputs" in cmd_conf:
        for key, input_conf in cmd_conf["inputs"].items():
            show_help_input(key, input_conf)
    print(bcolors(bcolors("\nTransformed inputs (Value will be calculated):", "blue"), "bold"))
    if "transform" in cmd_conf:
        for key, input_conf in cmd_conf["transform"].items():
            show_help_input(key, input_conf)
    if "env-files" in cmd_conf:
        print(bcolors(bcolors("\nPossible paths for env files:", "blue"), "bold"))
        for env_file in cmd_conf["env-files"]:
            print(f"- {bcolors(env_file, 'yellow')}")


def print_list_commands(description: bool = True) -> None:
    """
    Print out the list of commands
    """
    cprint(ASCII_ART, ["cyan", "bold"])

    cprint(f"Available commands are under {GLOW_COMMANDS}:", ["green"])

    for command_file in list_commands():
        command_name = command_file.stem
        print("\n")
        print(f"- 💻 {bcolors(bcolors(command_name, 'yellow'), 'bold')}")
        print("\n")

        if description:
            cmd_conf = open_yaml_conf(command_file)
            if "description" in cmd_conf:
                cprint(f"{cmd_conf['description']}", ["blue"])
            if "command" in cmd_conf:
                cprint("command template:", ["header", "underline"])
                cprint(f"{cmd_conf['command']}", ["header"])
