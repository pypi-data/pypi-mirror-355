# This file is part of DNV SesamX.
# It defines a list of global functions for working with SesamX workspaces and workspace objects.

# Define global functions for working with workspaces and workspace objects.
from DNVS.Sesam.Commons.Workbench.UI.Shell import WorkspaceSession as ws
from DNVS.Sesam.Commons.ApplicationCore import QuantityProvider
from DNVS.Sesam.Commons.ConceptCore import Concept
from DNVS.Commons.ModelCore import Reference

class WorkspaceSession:
    "Working with SesamX workspaces."

    def __init__(self, path):
        "Initialize a workspace session with the given path to SesamX workspace file."
        global __workspace_session__
        global __quantity_provider__
        __workspace_session__ = ws(saveWorkspaceOnExit=True)
        __quantity_provider__ = QuantityProvider()
        self.session = __workspace_session__
        self.session.OpenWorkspace(path)

    def __enter__(self):
        return None

    def __exit__(self, *args):
        self.session.Dispose()

def Unit(unit_expression):
    "Find a unit by its expression in the workspace."
    return __quantity_provider__.FindUnit(unit_expression)

def FindConcept(concept_path, type_ = Concept):
    "Find a concept in the workspace. type_ can be specified to return a specific type of concept."
    return __workspace_session__.Workspace.Find[type_](concept_path)

def Delete(concept):
    "Delete a concept from the workspace."
    return __workspace_session__.Workspace.GetWorkspaceService().DeleteConcept(concept)