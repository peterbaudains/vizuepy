"""
Python script to automate the spawning of assets within an unreal directory at 
a designated location within the current level.

"""
import unreal 

## Set parameters

# Change the below path to spawn a directory of assets from within the Content
# browser within unreal.
unreal_asset_directory_to_spawn = "/Game/Test/"

# Set the location in the unreal level where the spawned asset should be placed
# Note - this acts more like an offset rather than a location since fbx files 
# typically have geometry already defined. The spawning process doesn't replace
# this geometry, but instead shifts the entire mesh according to the below 
# location.
assets_location_offset_x = -53281600.0
assets_location_offset_y = 18075900.0
assets_location_offset_z = 0.0

asset_registry = unreal.AssetRegistryHelpers().get_asset_registry()
assets = asset_registry.get_assets_by_path(package_path=unreal_asset_directory_to_spawn)

for asset in assets:
    obj = unreal.EditorAssetLibrary.load_asset(asset.package_name)
    obj_name = obj.get_name()
    unreal.log("Spawning object %s" % obj_name)
    loc = [assets_location_offset_x,assets_location_offset_y, assets_location_offset_z]
    actor = unreal.EditorLevelLibrary().spawn_actor_from_object(obj, loc)
