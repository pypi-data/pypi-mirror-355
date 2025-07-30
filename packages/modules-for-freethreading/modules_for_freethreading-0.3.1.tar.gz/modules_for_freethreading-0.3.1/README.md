
# Modules for free-threading built python

## Description

See [https://github.com/python/cpython/pull/135550](https://github.com/python/cpython/pull/135550), [PEP779](https://peps.python.org/pep-0779/#open-issues).
Now the free-threading is not a experimental feature anymore. However, the `.pyd` files are different between two executable.
This repository is make sure that if the `.pyd` files are not the files for the executable version, it will be reinstall for the currently version.

## Note

Make sure that the packages have at least a version that is compatible with the current python executable version.
The `cp313-cp313` should be used for the normal, while the `cp313-cp313t` should be used for the free-threading.

## Usage

```sh
pip install modules_for_freethreading
```

The code below is an example of using the `numpy` module. If the `numpy` module is not compatible with the current python executable version, it will be reinstalled for the corrently version.
```python
import modules_for_freethreading
modules_for_freethreading.add_module("numpy"[, module_version="2.2.0"])
import numpy
```

## Note

If the module's name is different from the install name, you should set it : 
```python
import modules_for_freethreading
modules_for_freethreading.add_module("jpype")
modules_for_freethreading.add_other_name("jpype", "jpype1")
import jpype
```

## License

MIT
