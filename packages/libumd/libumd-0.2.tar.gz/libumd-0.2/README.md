
# libumd


libumd is a simple on-runtime module loader designed for programs that need to load modules on runtime.

Its similar to `importlib` in perspective but quite different on functionality
## Example
Load the `test` module and run the `greet` function from it 

```python
import libumd

loader = libumd.Loader()
loader.setparams('name', 'John')

mod = loader.loadmod('test')
mod.start()
mod.greet()
mod.stop()
```


## How It Works

libumd loads a module from a directory, and parses `manifest.json`, it looks for these modules

- `name`: The name of the module
- `description`: A small description of the module
- `author`: The name of the module creator
- `for`: An array of packages it supports or `"any"`, which lets it run on any package
- `entry`: The name of the main class

It then looks up for a python file called after the `name` key and ends in `.py`, which should contain a class named after `entry`.

The class is expected to have these functions and features

- Receive and store an argument (`libumd_params`) in `__init__`
- A `start`, `stop` and `status` functions
- Be named after the `entry` key from `manifest.json`

After this, it assigns the module a unique id, and returns a wrapper that allows calling the module functions safely.

You can view a sample in the `greet` directory of this repository.

## License

libumd is licensed with the MIT License, read `LICENSE`