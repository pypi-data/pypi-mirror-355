# This script is used to load SesamX assemblies and find the SesamX application executable path.

import os
from pythonnet import load

script_dir = os.path.dirname(os.path.abspath(__file__))
assembly_dir = os.path.join(script_dir, r'.dlls') 

load("coreclr", runtime_config= os.path.join(script_dir, 'runtimeconfig.json'))

import clr
import json
from System import Reflection

def load_assemblies():
    """Load required assemblies for SesamX."""

    sesamX_libraries = get_sesamx_path()
    try:
        # Open and read the JSON file
        with open(os.path.join(sesamX_libraries, 'PythonScriptConfig.json'), 'r') as file:
            dll_config = json.load(file)

        # load SesamX assemblies
        for dll in dll_config['dlls']:
            # special handling for System.Configuration.ConfigurationManager.dll
            if dll == 'System.Configuration.ConfigurationManager.dll':
                configMgr = os.path.join(sesamX_libraries, dll)
                Reflection.Assembly.LoadFile(configMgr)
            else:
                clr.AddReference(os.path.join(sesamX_libraries, dll))
    except Exception as e:
        raise RuntimeError(f"Failed to load SesamX assemblies: {e}")
    
def get_sesamx_path():
    """Locate the SesamX application path with DLLs."""

    # load DNV.AppVersionManager.Core to find SesamX application
    try:
        clr.AddReference(os.path.join(assembly_dir, 'DNV.ApplicationVersionManager.Core.dll'))
        from DNV.ApplicationVersionManager.Core import AppVersionServiceLocator
    except Exception as e:
        raise RuntimeError(f"Failed to load Application Version Manager: {e}")

    # locate the SesamX application executable path with the DLLs
    sesamX_libraries = ""
    try:
        sesamX_app = AppVersionServiceLocator.Default.AppVersionSearcher.GetDefaultApplication('SesamX')
        if sesamX_app is None:
            raise RuntimeError("SesamX application not found. Please ensure it is installed")
        
        sesamX_libraries = os.path.dirname(os.path.abspath(sesamX_app.ExeFilePath))
    except Exception as e:
        raise RuntimeError(f"Failed to locate SesamX application: {e}")

    return sesamX_libraries