# dnv-sesamx

dnv-sesamx is a Python library loading DNV SesamX .NET libraries that allows to work with DNV workspaces (*.sesx).

This is a release candidate version of the library.
It is intended for final testing before the official stable release.
While all major features are implemented, there may still be minor issues or bugs.
We encourage users to try this version and provide feedback, but it is not recommended for use in production environments.

Requirements: 
- DNV SesamX (distributed on request)
- Python 3.10 or later

## Usage/Examples

Installing the library:

`pip install dnv-sesamx --pre`

Usage example:

```python
import os

# loading SesamX assemblies
from dnv.sesamx import load_assemblies
load_assemblies()

# import from SesamX .NET libraries required to work with
from DNVS.Sesam.Commons.Workbench.UI.Shell import WorkspaceSession
from DNVS.Sesam.Commons.ConceptCore import PlotsFolder, Plot

session = any
try:
    session = WorkspaceSession(saveWorkspaceOnExit=True)
    workspace = session.CreateWorkspace(os.getcwd(), "demoWorkspace")

    # creates plot folder
    folder = session.CreateConcept[PlotsFolder](session.Workspace)

    # creates a plot
    session.CreateConcept[Plot](folder)
except Exception as e:
    print(f"An error occurred: {e}")
finally: #ensures workspace gets saved on exit
    session.Dispose()
```

## Build

Setup build tools:

```
python -m pip install --upgrade toml-cli
python -m pip install --upgrade build
```

Prepare build environment and version:

`toml set --toml-path src/dnv.sesamx/pyproject.toml project.version 1.0.0`

Build the package:

`python -m build src/dnv.sesamx`

Install package from a local source:

`pip install dnv-sesamx --no-index --find-links file:///C:\Git\SesamX.Python\src\dnv.sesamx\dist`


## License

[MIT](https://choosealicense.com/licenses/mit/)

## Support

If you encounter any issues, have questions, or want to provide feedback, please get in touch with our support team at software.support@dnv.com. We are committed to continuously improving SesamX and providing timely assistance to our users.
