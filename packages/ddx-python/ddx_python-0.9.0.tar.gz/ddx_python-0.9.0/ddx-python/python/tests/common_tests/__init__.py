import importlib
import pkgutil

# Dynamically import all the modules in the current package
for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
    # Ensure the module is not a package (directory) itself
    if not is_pkg:
        # Load module dynamically using importlib
        importlib.import_module("." + module_name, __package__)
