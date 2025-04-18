import importlib
import glob
from os.path import dirname, basename, isfile, join

# Import all modules
mod_paths = glob.glob(join(dirname(__file__), "*.py"))
ALL_MODULES = [
    basename(f)[:-3]
    for f in mod_paths
    if isfile(f) and not f.endswith("__init__.py")
]

# Import all modules dynamically
imported_mods = {}
for module_name in ALL_MODULES:
    imported_mods[module_name] = importlib.import_module(f"modules.{module_name}")

# Create ALL_MODULES list with actual module objects
ALL_MODULES = list(imported_mods.values())

# Add 'groupchat' to ALL_MODULES list
ALL_MODULES.append("groupchat")

__all__ = ["ALL_MODULES"] + ALL_MODULES 
