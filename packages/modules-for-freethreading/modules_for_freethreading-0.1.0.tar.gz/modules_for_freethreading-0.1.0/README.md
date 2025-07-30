# Modules for freethreading built python

## Description

See [https://github.com/python/cpython/pull/135550](https://github.com/python/cpython/pull/135550).
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
modules_for_freethreading.add_module("numpy")
```

## License

MIT
