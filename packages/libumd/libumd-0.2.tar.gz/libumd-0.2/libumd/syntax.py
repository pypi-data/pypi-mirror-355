# this checks for syntax errors in the manifest
import json
def manifest_check(manifest: dict):
    for key in ["name", "version", "author", "description", "for"]:
        if key not in manifest:
            raise SyntaxError(f"manifest error: \"{key}\" not found in manifest")
    if isinstance(manifest['for'], str):
       pass
    elif isinstance(manifest['for'], list):
        pass
    else:
        raise SyntaxError("manifest error: \"for\" is not a string or a list")
    for i in ["name", "version", "author", "description", "entry"]:
        if not isinstance(manifest[i], str):
            raise SyntaxError(f"manifest error: {i} is not a string")
    return True