"""
Python script to automate import of FBX files into Unreal Engine assets

Given a directory of fbx files (defined via the fbx_directory variable in the 
script below), this script will loop through each fbx file it can find, and 
allocate it to an unreal.AssetImportTask, which is itself stored in an array.

These import tasks are then executed at the end of the loop, leading to assets 
which can be viewed in Unreal Engine's Content Browser at the given location 
(itself defined by the unreal_asset_directory variable).

The script checks whether or not the asset already exists. If it does, it will
NOT overwrite it.

Finally, this script will not import any associated materials or textures. The
imported assets will be imported as static meshes only.
"""

import unreal
import os
from pathlib import Path

tasks = []

# Set parameters
# Change the below directory path to where the fbx files are located
fbx_directory = str(Path(str(Path.home()) + "/fbx_files/"))
# Change the below directory path to where the unreal assets should be imported
unreal_asset_directory = "/Game/"

for fbx_file in os.listdir(fbx_directory):
    unreal.log("Creating Asset Import Task for file %s" % fbx_file)
    if fbx_file.split('.')[-1]=='fbx':
        asset_path = unreal_asset_directory + fbx_file[:-4]
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path): 
            unreal.log("Specified asset already exists. Skipping file.")
            unreal.log("Current asset will not be altered.")
        else:
            task = unreal.AssetImportTask()
            task.filename = str(Path(fbx_directory + "\\" + fbx_file))
            task.destination_path = unreal_asset_directory
            task.replace_existing = False
            task.automated = True
            task.save = True
            task.options = unreal.FbxImportUI()
            task.options.import_materials = False
            task.options.import_textures = False
            task.options.import_as_skeletal = False
            task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH 
            tasks.append(task)

if len(tasks) > 0:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
