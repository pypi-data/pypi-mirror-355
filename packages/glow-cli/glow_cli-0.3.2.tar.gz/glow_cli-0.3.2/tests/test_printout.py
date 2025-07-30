import unittest

from glow.constants import EXAMPLE_COMMAND
from glow.printout import print_command, show_help


def test_print_command(capfd):
    cmd_conf = {
        "command": "echo {name} {password}",
        "inputs": {
            "name": {
                "type": "text",
                "default": "test",
            },
            "password": {
                "type": "secret",
                "default": "test",
            },
        },
    }
    data = {
        "name": "test",
        "password": "test",
    }
    print_command(cmd_conf, data)

    assert capfd.readouterr().out == "\x1b[4m\nRUNNING COMMAND:\x1b[0m\n\x1b[95mecho test ****\x1b[0m\n"


def test_show_help(capfd):
    with open("/tmp/test.yml", "w") as f:
        f.write(EXAMPLE_COMMAND)
    show_help("/tmp/test.yml")
    output = capfd.readouterr().out
    assert "world" in output
    assert "--people" in output
    assert "\x1b[1m\x1b[96m\n" in output
    assert 'echo "hello ,{people}"'
