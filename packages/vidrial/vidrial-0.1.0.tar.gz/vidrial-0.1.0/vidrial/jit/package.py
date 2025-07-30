import os
from typing import Any
import shutil
import logging
import subprocess
from tqdm import tqdm
import yaml

logger = logging.getLogger(__name__)

FUNCTIONS = []
CONFIG_CACHES = []


def register_runtime(name: str, path: str):
    """
    Register a runtime for a given function. This is used for packaging built
    runtimes for release.

    Args:
        name: The name of the function.
        path: The path to the runtime.
    """
    if os.environ.get('JIT_PACKAGE_MODE', '0') == '1':  
        FUNCTIONS.append(dict(name=name, path=path))


def register_config_cache(cache: Any):
    """
    Register a config cache for a given function. This is used for packaging
    config caches for release.

    Args:
        name: The name of the function.
        cache: The config cache.
    """
    if os.environ.get('JIT_PACKAGE_MODE', '0') == '1':
        CONFIG_CACHES.append(cache)


def get_git_status():
    """ Get the current git status.

    Returns:
        A dictionary containing the git status.
    """
    commands = {
        "root": ["git", "rev-parse", "--show-toplevel"],
        "commit": ["git", "rev-parse", "HEAD"],
        "status": ["git", "status", "--porcelain"],
    }
    info = {}
    for key, cmd in commands.items():
        try:
            info[key] = subprocess.check_output(cmd, cwd=os.getcwd(), text=True).strip()
        except subprocess.CalledProcessError:
            info[key] = "unknown"
    info['status'] = "clean" if info['status'] == "" else "dirty"
    return info


def package_release(version: str, root: str):
    """
    Package the current state of JIT functions for release.

    Args:
        version: The version string to use for the package
        root: The root directory to store the package
    """
    if os.environ.get('JIT_PACKAGE_MODE', '0') == '1':
        os.makedirs(root, exist_ok=True)

    for cache in tqdm(CONFIG_CACHES, desc="Packaging config caches"):
        cache.store(os.path.join(root, f"{cache.fn}.yaml"))
        logger.info(f"Packaged config cache for {cache.fn} to {os.path.join(root, f'{cache.fn}.yaml')}")

    for function in tqdm(FUNCTIONS, desc="Packaging runtimes"):
        shutil.copytree(function["path"], os.path.join(root, os.path.basename(function["path"])), dirs_exist_ok=True)
        logger.info(f"Packaged runtime for {function['name']} to {os.path.join(root, os.path.basename(function['path']))}")

    status = get_git_status()
    status["version"] = version
    with open(os.path.join(root, "version.yaml"), "w") as f:
        yaml.dump(status, f)

    logger.info(f"Kernels packaged to {root}")
