#!/usr/bin/env python
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fire import Fire

from glow.colors import bcolors, cprint
from glow.configs import GLOW_CONFIGS
from glow.constants import ASCII_ART
from glow.glowhub import download_glow_hub
from glow.llm.run import run_llm
from glow.logics import FUNCTION_FACTORY_MAP
from glow.manage import install_local, open_yaml_conf, summon, task_to_path
from glow.printout import print_command, show_help, show_help_input, print_list_commands
from glow.secrets import GLOW_SECRETS
from glow.utils.command import run_command
from glow.utils.dotenv import load_dot_env_file
from glow.utils.yaml import open_yaml_conf


def run_foundation(found_configure: Dict[str, str], data: Dict[str, Any]) -> None:
    """
    run a foundation task
    - found_configure: configuration of the foundation task
        - context: the context directory of the foundation task
        - task: the name of the foundation task
            "{task}.yml" shall be the default task configuration file
            under the context directory
    - data: the data to pass to the foundation task

    This function will to following steps:
    - travel to another context directory
    - run the foundation task
    - return to the original context directory
    """
    current = Path(".").absolute()
    context = found_configure["context"]
    context_folder = current / context
    # cd into build_folder
    os.chdir(context_folder)
    run_sh(found_configure["task"], **data)
    os.chdir(current)


def run_sh(task: Optional[str] = None, *args, **data) -> None:
    """
    Run a shell command on a task
    - task: the name of the task
        "{task}.yml" shall be the default task configuration file
    - data: the data to pass to the task
        This will be the keyed inputs set by `fire.Fire`

    Some preserved keywords:
    - task: the name of the task
    - help: show the help for the task
    - configs: run the configs management
    - secrets: run the secrets management
    - llm: run the llm generation
    - code: run the code generation
    - foundation: run the foundation task
    """
    # if task is not specified, we summon all the tasks
    quiet = True if "quiet" in data else False
    if task is None:
        print_list_commands()
        return
    if task == "list":
        print_list_commands()
        return
    if task == "summon":
        cprint(ASCII_ART, ["cyan", "bold"])
        summon()
        return
    if task == "secrets":
        GLOW_SECRETS(*args, **data)
        return
    if task == "configs":
        GLOW_CONFIGS(*args, **data)
        return
    if task == "install":
        if "file" in data:
            install_local(Path(data["file"]))
            return
        elif len(args) == 1:
            install_local(Path(args[0]))
            return
        else:
            cprint("please specify the file to install with --file", ["yellow"])
            return

    if task == "glowhub":
        download_glow_hub(*args, **data)
        return

    if task == "llm":
        system_content = None
        if "s" in data:
            system_content = data["s"]
        if "system" in data:
            system_content = data["system"]
        if "q" in data:
            run_llm(data["q"], system_content)
            return
        elif "question" in data:
            run_llm(data["question"], system_content)
            return
        elif len(args) == 1:
            question = args[0]
            run_llm(question, system_content)
            return
        elif len(args) == 2:
            question, system_content = args
            run_llm(question, system_content)
            return
        elif len(args) > 2:
            run_llm(" ".join(args), system_content)
            return
        else:
            cprint("please specify the question", ["yellow"])
            return

    if "help" in data:
        show_help(task)
        return

    path = task_to_path(task)
    cmd_conf = open_yaml_conf(path)

    results = data

    # read values from env-files
    if "env-files" in cmd_conf:
        for env_file in cmd_conf["env-files"]:
            load_dot_env_file(env_file)

    # non-templating command
    if "inputs" not in cmd_conf:
        command = cmd_conf["command"]
        cprint("💻 running command:", ["green", "underline"])
        cprint(command, ["green"])
        run_command(command)
        return

    if len(args) > 0 and len(data) == 0:
        cprint("Setting positional args to keyword args:", ["green", "underline"])
        input_keys = list(cmd_conf["inputs"].keys())
        data = dict(zip(input_keys, args))
        for key, value in data.items():
            ckey = bcolors(bcolors(key, "header"), "bold")
            cvalue = bcolors(bcolors(value, "green"), "bold")
            print(f"set {ckey} = {cvalue}")

    for key, input_conf in cmd_conf["inputs"].items():
        if key in data:
            # validate the input
            if "options" in input_conf:
                if data[key] not in input_conf["options"]:
                    show_help_input(key, input_conf)
                    raise ValueError(f"{data[key]} is not a valid option for {key}")
            results[key] = data[key]
        elif "env_var" in input_conf:
            # read environment variable
            if input_conf["env_var"] in os.environ:
                results[key] = os.environ[input_conf["env_var"]]
            elif "default" in input_conf:
                results[key] = input_conf["default"]
            else:
                # if not provided, we will ask for it
                results[key] = GLOW_SECRETS[key]
        elif "default" in input_conf:
            # use default
            results[key] = input_conf["default"]
        else:
            show_help_input(key, input_conf)
            raise KeyError(f"--{key} not found")

    # some data are not preset or input by the user
    # instead they are calculated through if conditions upon other data
    if "transform" in cmd_conf:
        for key, transform in cmd_conf["transform"].items():
            # transform field values can be overwritten instead of calculated
            if key in results:
                continue
            if "function" not in transform:
                show_help_input(key, transform)
                raise KeyError(f"{key} has no function," + "please specify a function name for transform")

            callable_factory = FUNCTION_FACTORY_MAP.get(transform["function"])
            if callable_factory is None:
                show_help_input(key, transform)
                raise KeyError(f"{transform['function']} is not a valid function")

            # build the transforming function from factory
            callable = callable_factory(key, transform)

            # apply the  transforming function to get new data field
            results[key] = callable(results)

    if "command" not in cmd_conf:
        raise KeyError(f"command not found in {task}," + "probably not a 'glow' config file")
    command_template = cmd_conf["command"]
    command = command_template.format(**results)

    if quiet is False:
        print_command(cmd_conf, results)

    if "dry" not in data:
        # if dry run, we only show the command
        if ("foundation" in cmd_conf) and ("foundation" in data):
            # if there are other command we should run
            for foundation in cmd_conf["foundation"]:
                run_foundation(foundation, results)
        run_command(command)


# exposure to command lines
def main():
    Fire(run_sh)


if __name__ == "__main__":
    main()
