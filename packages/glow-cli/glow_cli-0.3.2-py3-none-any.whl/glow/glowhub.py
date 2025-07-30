import requests

from glow.colors import cprint
from glow.configs import GLOW_CONFIGS
from glow.constants import GLOW_COMMANDS
from glow.secrets import GLOW_SECRETS


def download_glow_hub(*args, **data) -> None:
    """
    Download a script from glow hub
    glow hub is any repo on github that contains glow scripts
    Please set up the following environment variables:
    ```
    g configs add GLOW_HUB_OWNER xxxx
    g configs add GLOW_HUB_REPO xxxx
    g secrets add GH_PAT
    ```

    in args:
    - script: the file name of the script to download, eg `abc.yml`
    - path: the path of the script to download

    in data:
    - script: the file name of the script to download, eg `abc.yml`
    - path: the path of the script to download
    - branch: the branch of the script to download
    """
    glow_hub_owner = GLOW_CONFIGS["GLOW_HUB_OWNER"]
    glow_hub_repo = GLOW_CONFIGS["GLOW_HUB_REPO"]
    gh_pat = GLOW_SECRETS["GH_PAT"]

    if "script" in data:
        script = data["script"]
    else:
        if len(args) < 1:
            raise Exception("Please specify the script to download")
        script = args[0]

    if "path" in data:
        path = data["path"]
    elif len(args) > 1:
        path = args[1]
    else:
        path = "glow"

    if "branch" in data:
        branch = data["branch"]
    else:
        branch = "main"

    url = f"https://raw.githubusercontent.com/{glow_hub_owner}/{glow_hub_repo}/{branch}/{path}/{script}"
    headers = {
        "Authorization": f"Bearer {gh_pat}",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to download {script} from {url}")
    with open(GLOW_COMMANDS / script, "w") as f:
        f.write(response.text)
    cprint(f"✨📦 {script} installed to {GLOW_COMMANDS / script}", ["green"])
