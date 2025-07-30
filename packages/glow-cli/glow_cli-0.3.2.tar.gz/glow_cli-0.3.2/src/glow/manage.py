import logging
from pathlib import Path
from shutil import copyfile
from typing import Any, Dict, List, Optional, Union

from glow.constants import GLOW_CONF, GLOW_COMMANDS
from glow.colors import bcolors, cprint
from glow.utils.yaml import open_yaml_conf


def find_commands(command_name: str) -> List[Path]:
    """
    find all the commands with the same name
    """
    commands = []
    for path in GLOW_COMMANDS.rglob(f"{command_name}.*"):
        if path.stem == command_name:
            commands.append(path)
    return commands


def list_commands() -> List[Path]:
    """
    list all the commands we can use
    """
    commands = []
    for path in GLOW_COMMANDS.rglob("*"):
        if path.stem not in commands:
            commands.append(path)
    return commands


def install_local(filepath: Path) -> None:
    if filepath.exists() is False:
        cprint(f"❌ {filepath} not found", ["red"])
        return
    if filepath.is_dir():
        cprint(f"❌ {filepath} is a directory", ["red"])
        return
    # copy the file to the glow command folder
    target = GLOW_COMMANDS / filepath.name
    if target.exists():
        cprint(f"✨ {target} already exists, update to new file", ["cyan"])
    copyfile(filepath, target)
    cprint(f"✨📦 {filepath} installed to {target}", ["green"])


def task_to_path(task: str) -> Path:
    """
    get the path of the task configuration file

    According to the task name, we can get the path of the task configuration file
    """
    if task[-4:] != ".yml":
        path = Path(f"{task}.yml")
    else:
        path = Path(task)
    if not path.exists():
        commands = find_commands(task)
        if len(commands) == 0:
            raise FileNotFoundError(f"{path} not found, it should be")
        path = commands[0]
    return path


def is_glow_task(path: Union[Path, str]) -> Optional[Dict[str, Any]]:
    """
    Check if the path is a glow task
    """
    path = Path(path)
    if path.exists() is False:
        return

    # check if we can open it
    try:
        data = open_yaml_conf(path)
    except Exception:
        logging.info(f"task: {path} is not a valid glow task")
        return
    if "description" not in data:
        return
    if "command" not in data:
        return
    if "inputs" not in data:
        return
    return data


def summon() -> None:
    """
    Summon all the tasks
    To see which to run
    """
    cprint("Available tasks for GLOW", ["cyan", "bold"])
    null_ct = False
    for path in Path(".").iterdir():
        if path.suffix != ".yml":
            continue
        data = is_glow_task(path)

        if data is None:
            continue

        description = data.get("description")
        if "inputs" not in data:
            continue
        inputs = ", ".join(str(bcolors(i, "green")) for i in list(data["inputs"].keys()))
        task_title = bcolors(bcolors(f"{path.stem}", "yellow"), "bold")
        print(">>-" * 20)
        print(f"💫 {task_title}:\t{description}")
        print(f"🌶 inputs: {inputs}")
        cprint(f"glow {path.stem} --help", ["header"])
        null_ct = True

    # no task found
    if null_ct is False:
        cprint("\nNo tasks found", ["red"])
