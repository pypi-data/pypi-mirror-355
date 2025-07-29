import sys
import os
import importlib
import inspect

root = os.path.dirname(inspect.getfile(lambda: None))
hcli_hst_manpage_path = root + "/data/hcli_hst.1"
plugin_path = root + "/cli"
cli = None

""" we setup dynamic loading of the cli module to allow for independent development and loading, independent of hcli_core development """
def set_plugin_path(p):
    global plugin_path
    global cli
    if p is not None:
        plugin_path = p

    sys.path.insert(0, plugin_path)
    cli = importlib.import_module("cli", plugin_path)
