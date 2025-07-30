from typing import Any, Callable, Dict


def create_if_else(key: str, conf: Dict[str, Any]) -> Callable:
    """
    key: name of the input
    conf: configuration of the function
        - values: the possible values of the input
        - input_sequence: optional, the sequence of keys (of data) to be used
    """
    if "values" not in conf:
        raise KeyError(f"'{key}' configuration has no 'values'" +
                       "which is required for if-else")

    def if_else(data: Dict[str, Any]) -> Any:
        """
        A function will map the value according to the known data
            How we map the value is depend on key_sequence, a chain of keys
            to get the value throw multistage of if-else
        """
        values = conf["values"]
        if "key_sequence" in conf:
            for if_key in conf["key_sequence"]:
                if if_key in data:
                    values = values[data[if_key]]
                else:
                    raise KeyError(f"{if_key} not set in data")
        return values
    return if_else


def create_join(key: str, conf: Dict[str, Any]) -> Callable:
    """
    key: name of the input
    conf: configuration of the function
        - from: the data field to join
        - separator: optional, default ',', the separator to join the data
    """
    separator = "," if "separator" not in conf else conf["separator"]
    if "from" not in conf:
        raise KeyError(f"'{key}' configuration has no 'from'" +
                       "which is required for join")

    def join_iterable(data: Dict[str, Any]) -> Any:
        """
        A function will join the iterable on separator
        """
        values = data[conf["from"]]
        if type(values) in [list, tuple]:
            return separator.join(
                list(str(v) for v in values))
        return values
    return join_iterable


def create_mapper_render(key: str, conf: Dict[str, Any]) -> Callable:
    """
    key: name of the input
    conf: configuration of the function
        - template: the row template(for each key, value pair) to render
            the template can only render 2 variables at most
            - `key`
            - `value`
        - from: the data field to map
        - separator: optional, default ' \\\n\t',
            the separator to join the data
    """
    if "template" not in conf:
        raise KeyError(f"'{key}' configuration has no 'template'" +
                       "which is required for mapper_render")
    template_str = conf["template"]
    if "from" not in conf:
        raise KeyError(f"'{key}' configuration has no 'from'" +
                       "which is required for mapper_render")
    separator = " \\\n\t" if "separator" not in conf else conf["separator"]

    def mapper_render(data: Dict[str, Any]) -> str:
        """
        A function will render the key-value mapper data
        """
        render_dict = data[conf["from"]]
        result_list = []
        for key, value in render_dict.items():
            result_list.append(str(
                template_str.format(key=key, value=value)))
        return separator.join(result_list)
    return mapper_render


FUNCTION_FACTORY_MAP = dict(
    if_else=create_if_else,
    join=create_join,
    mapper_render=create_mapper_render,
)
