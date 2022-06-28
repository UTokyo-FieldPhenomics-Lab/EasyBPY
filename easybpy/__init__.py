bl_info = {
    "name": "EasyBPY",
    "author": "Haozhou Wang",
    "version": (1, 0),
    "blender": (3, 2, 0),
    "location": "View3D > Tool Shelf > EasyBPY",
    "description": "A package addon for easy scripting",
    "warning": "",
    "wiki_url": "",
    "category": "Scripting",
}

import bpy

from . import io

cls = (
    io
)

def register():
    bpy.utils.register_classes_factory(cls)

def unregister():
    bpy.utils.unregister_module(cls)


if __name__ == "__main__":
    register()