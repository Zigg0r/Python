bl_info = {
    "name": "DefaultCube",
    "author": "Ziggor",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "description": "Modular addon for VRchat world creation",
    "category": "3D View",
}

from . import Utilities
from . import UVwrap
from . import BatchFBX

modules = [Utilities, UVwrap, BatchFBX]

def register():
    for m in modules:
        m.register()

def unregister():
    for m in reversed(modules):
        m.unregister()
