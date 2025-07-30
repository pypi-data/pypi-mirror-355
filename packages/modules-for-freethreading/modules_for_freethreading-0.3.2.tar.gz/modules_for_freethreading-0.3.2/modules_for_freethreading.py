__all__ = ("add_module", "add_other_name")

from packaging.version import parse
from importlib.metadata import version
import sys
import threading
import subprocess
import time
import builtins

def is_valid_version(version_str: str|None):
    if version_str is None:
        return True
    try:
        parsed = parse(version_str)
        return not parsed.is_prerelease and not parsed.is_devrelease
    except:
        return False

def get_version(name):
    try:
        return version(name)
    except Exception:
        return ''
    
_original_import = __import__

_register_module: dict[str, str] = {}
_other_name: dict[str, str] = {}
def add_module(module_name: str, module_version: str|None = None):
    if not is_valid_version(module_version):
        raise ValueError(f'''Wrong version {module_version}: version must be the official version.
For example: 2.2.0, 2.2.1, etc.
Don't set the version like 2.2.0rc1, 2.2.0dev0, 2.2.0beta, etc.''')

    _register_module[module_name] = module_version if module_version is not None else ""

def add_other_name(module_name: str, module_other_name: str):
    """
    For the module that name in pypi is different from the real name.
    """
    _other_name[module_name] = module_other_name

def _register_import(name, globals=None, locals=None, fromlist=(), level=0):
    def wait_print():
        while not finish:
            for i in ("/", "|", "\\", "-"):
                print(f"install {name}{version_str}", i, end="\r", flush=True)
                time.sleep(0.25)
        print("\r\n", flush=True)
    def setup():
        nonlocal finish
        print_threading = threading.Thread(target=wait_print)
        print_threading.start()
        
        setup_module = subprocess.Popen([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            f"{_other_name.get(name, name)}{version_str}"
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        stdout, stderr = setup_module.communicate()
        finish = True
        print_threading.join()
        return setup_module.returncode, stdout, stderr
    finish = False
    if name not in _register_module:
        return _original_import(name, globals, locals, fromlist, level)
    need_pip = False
    if _register_module.get(name, ''):
        version_str = f"=={_register_module.get(name, '')}"
    else:
        version_str = ''
    if _register_module[name] and get_version(name) != _register_module[name]:
        need_pip = True
    else:
        try:
            return _original_import(name, globals, locals, fromlist, level)
        except Exception:
            need_pip = True
    if need_pip:
        result = setup()
        print(result[1])
        if result[0] != 0:            
            raise ImportError(f"cannot setup {name}: \n{result[2]}")
        print(f"Successfully import {name}{version_str}")
        return _original_import(name, globals, locals, fromlist, level)
    
    
builtins.__import__ = _register_import
