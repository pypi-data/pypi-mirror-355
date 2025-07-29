import os
import json
from .syntax import manifest_check
import uuid
import importlib.util
class _ModWrapper:
    def __init__(self, module_class, params):
        if not isinstance(module_class, type):
            raise TypeError(f"internal error: expected a class, not a {str(type(module_class))}")
        self.mod = module_class(params)

    def start(self):
        return self.mod.start()

    def status(self):
        return self.mod.status()

    def stop(self):
        return self.mod.stop()

    def __getattr__(self, func):
        blacklist = {'start', 'status', 'execute', 'stop', '__init__'}
        if func in blacklist:
            raise ValueError(f"function '{func}' is protected and cannot be called.")
        if not hasattr(self.mod, func):
            raise AttributeError(f"function '{func}' not found in module.")
        
        method = getattr(self.mod, func)
        if not callable(method):
            raise TypeError(f"attribute '{func}' is not callable.")

        return method

class Loader:
    def __init__(self):
        self.params = {"name": "unknown"}
        self.modules = {}
        self.mods = {}
        pass

    def setparams(self, key, value):
        if not isinstance(key, str):
            raise SyntaxError("key is not a string")
        if not isinstance(value, str):
            raise SyntaxError("value is not a string")
        self.params = {key: value}
    def loadmod(self, module):
        if os.path.isdir(module):
            manifest = os.path.join(module, 'manifest.json')
            if not os.path.isfile(manifest):
                raise FileNotFoundError("manifest does not exist")

            with open(manifest, 'r') as man:
                manif = json.load(man)
            if manif['for'] == "any":
                pass
            else:
                if self.params['name'] not in manif['for']:
                    print(f"module does not support this package, only supports: {', '.join(manif['for'])}, package: {self.params['name']}")
                    return False
            manifest = manif
            manifest_check(manif)
            # SyntaxError would be raised if a syntax error was found
            name, forpkg = manifest['name'], manifest['for']
            if isinstance(forpkg, list):
                if self.params['name'] not in forpkg:
                    raise FileNotFoundError(f"The module that you tried to load does not support this package, it only supports: {json.dumps(forpkg).join(', ')}")
            else:
                pass
            spec = importlib.util.spec_from_file_location(name, os.path.join(module, name + '.py'))

            if spec is None:
                raise ImportError(f"Cannot find module at {mod_path}")

            module = importlib.util.module_from_spec(spec)
            entry = manifest.get("entry", "Module")
            spec.loader.exec_module(module)
            try:
                mod_class = getattr(module, entry)
            except AttributeError:
                print("error: entry is invalid")
                return False

        else:
            # TODO: extract the module into a temporary directory
            pass
        uid = uuid.uuid1()
        self.modules[manifest['name']] = uid
        self.mods[uid] = _ModWrapper(mod_class, self.params)
        return self.mods[uid]
    def delete(self, module):
        if module not in self.modules:
            print("module does not exist")
            return False
        del self.mods[self.modules[module]]
        del self.modules[module]
        return True
    
