"""
Python Point Plotter for Unreal Engine

Author: Peter Baudains
Date: 25 May 2023

This script reads in a csv file where each row represents a point in two or 
three dimensional space (e.g. longitude, latitude, elevation or British 
National Gird (EPSG:27700) Eastings and Northings). 

Running this script from inside Unreal Engine (UE) will lead to the creation of
static mesh actors such as spheres and cylinders corresponding to the points in
the data file. There are options for assigning colormaps and changing the size 
of the mesh according to other columns in the data file. 

Dependencies:

- unreal Python API. 

This can be enabled in UE by enabling the Python Editor Script Plugin.
See here for more details: 
https://docs.unrealengine.com/5.2/en-US/scripting-the-unreal-editor-using-python/

- Pandas

Pandas is not installed by default in the UE distribution of Python and will
need installing. To install these, first identify the Python executable in your
filesystem which is bundled with UE. In Windows, this will be something like: 

"C:\\Program Files\\Epic Games\\UE_5.1\\Engine\\Binaries\\ThirdParty\\Python3\Win64\\python.exe"

Then Pandas can be installed by running the following in a command window:

"C:\\Program Files\\Epic Games\\UE_5.1\\Engine\\Binaries\\ThirdParty\\Python3\\Win64\\python.exe" -m pip install pandas
"""

# Standard Library
import os
import sys
import csv

# Non-standard
import unreal
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

class UnrealPoint:
    """
    A simple class to spawn a default unreal object and assign various 
    properties that affect its visible characteristics.
    """
    
    def __init__(self, id: int, x:float, y:float, z:float, label_prefix:str):

        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.location = unreal.Vector(x_value, y_value, z_value)

        self.scale = 1
        self.shape = 'Sphere' # Options for shape are: 'Cube', 'Sphere', 'Cylinder', 'Cone'
        self.material = None

        self.tags = []
        self.actor_hidden_in_game = False
        self.actor_label = label_prefix + str(id)


    def spawn_actor_from_blueprint_class(self, unreal_blueprint_path:str):

        self.blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class(unreal_blueprint_path)
        self.actor = unreal.EditorLevelLibrary().spawn_actor_from_class(self.blueprint_class, location=self.location)
        
        # Some actor attributes only become available when the actor is spawned
        # These are added here. All options available at: 
        # https://docs.unrealengine.com/4.27/en-US/PythonAPI/class/Actor.html
        self.actor.tags = self.tags
        self.actor.set_actor_hidden_in_game
        self.actor.set_actor_label(self.actor_label)
        # Keep the shape with uniform scale in three directions
        self.actor.set_actor_scale3d(unreal.Vector(self.scale,self.scale,self.scale))
        
        self.static_mesh_component = self.actor.static_mesh_component
        self.static_mesh_component.set_material(0, self.material)
        
        return self.actor.get_name()


def create_colored_material_instances(unique_values, cmap: matplotlib.colors.Colormap, norm: matplotlib.colors.Normalize = None, mi_directory_path : str = '/Game/', mi_name_prefix: str = ''):
    
    ''' 
    Create material instances in Unreal Engine with different colors for each 
    required material in plotting the points.

    Parameters
    ----------
    unique_values : Iterable
        Contains the set of unique values, each of which will require a 
        separate material instance.
    
    cmap : maptlotlib.color.Colormap 
        Used to map each value in unique value to its corresponding color

    norm : matplotlib.colors.Normalize 
        If a Normalize object is used, then this can be provided to map the 
        unique values to a value in the unit interval.
    
    mi_directory_path : str
        Each created material will be created at this location in the content 
        browser.

    mi_name_prefix : str
        Each material instance is named according to the value it represents - 
        this provides an opportuntiy to provide a prefix, which may be 
        necessary when plotting multiple datasets.
    '''

    try:
        [element for element in unique_values]
    except: 
        TypeError("Range of possible values are not iterable")
    
    material_dict = {}
    AssetTools = unreal.AssetToolsHelpers.get_asset_tools()

    # The material instance needs a parent in order to update properties. 
    # Hard coding to a simple opaque material whose color can be changed. 
    base_mtl = unreal.EditorAssetLibrary.find_asset_data('/Engine/EngineDebugMaterials/M_SimpleOpaque')

    # Create materials for each RGBA value
    for value in unique_values:
        
        unreal.log("Creating material for value %s" % value)
        
        # Convert value to unreal LinearColor object 
        if norm is None:
            # Check the values lie between zero and one.
            raise NotImplementedError

        else:
            rgba = unreal.LinearColor(r=cmap(norm(value))[0], g=cmap(norm(value))[1], b=cmap(norm(value))[2], a=cmap(norm(value))[3])
        
        mi_name = mi_name_prefix + str(value)
        
        if unreal.EditorAssetLibrary.does_asset_exist(mi_directory_path + mi_name):
            # To ensure code idempotence, let's delete any existing materials 
            # with the same name. This may cause problems if the names of 
            # different materials are not changed so let's log what every we 
            # end up deleting.
            unreal.log_warning('Deleting asset %s' % (mi_directory_path + mi_name))
            unreal.EditorAssetLibrary.delete_asset(mi_directory_path + mi_name)

        # Now we can create the asset and set a series of materials. 
        asset = AssetTools.create_asset(mi_name, mi_directory_path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())        
        # Assign base_mtl
        unreal.MaterialEditingLibrary.set_material_instance_parent(asset, base_mtl.get_asset() )
        # Set color parameter
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance=asset, parameter_name="Color", value=rgba)
        
        # Update and save
        unreal.MaterialEditingLibrary.update_material_instance(asset)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        
        # Store the asset object for reference create Static Mesh Actors
        material_dict[value] = asset

    return material_dict


def create_legend_texture(unique_values, labels, cmap : matplotlib.colors.Colormap, norm : matplotlib.colors.Normalize, texture_path):
    """
    Create a texture for use in a legend that can be added to a widget 
    blueprint
    """
    ax = plt.subplot(111)
    handles = []
    for i in unique_values: 
        handles.append(ax.plot([0], [0], 'o', color=cmap(norm(i))))
    legend = ax.legend(labels)
    fig = legend.figure
    fig.canvas.draw()
    expand = [-5,-5,5,5]
    bbox = legend.get_window_extent()
    bbox = bbox.from_extents(*(bbox.extents + np.array(expand)))
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(unreal.Paths.project_content_dir() + texture_path, bbox_inches=bbox, dpi=600)
    task = unreal.AssetImportTask()
    task.filename = unreal.Paths.project_content_dir() + texture_path
    task.destination_path = "/Game/" + texture_path
    task.replace_existing = True
    task.automated = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    os.remove(unreal.Paths.project_content_dir() + texture_path)


def import_point_display_text(csv_file_name, destination_path, data_table_struct_path):
    # Import csv data into a datatable
    task = unreal.AssetImportTask()
    task.filename = csv_file_name
    task.destination_path = destination_path
    task.replace_existing = True
    task.automated = True
    task.save = True
    csv_factory = unreal.CSVImportFactory()
    csv_factory.automated_import_settings.import_row_struct = unreal.load_object(None, data_table_struct_path)
    task.factory = csv_factory
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    os.remove(csv_file_name)


if __name__=="__main__":
    
    p = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'sample_data', 'FoodHygieneRatings_CityOfLondon_accessed20230525.csv')
    
    df = pd.read_csv(p)

    # For this example, we add a uniform z-value, but other datasets may include elevation.
    z_value = 10000

    # Offset values in Eastings and Northings for Unreal Origin
    # I.e. the origin in UE will be at this point in BNG coordinates
    ue_world_origin_bng_eastings = 532816
    ue_world_origin_bng_northings = 180759

    # Data cleaning
    df = df[df.RatingValue.isin(['1','2','3','4','5'])]
    df['RatingValue'] = pd.to_numeric(df.loc[:, 'RatingValue'])
    
    # Define a norm and cmap
    norm = matplotlib.colors.Normalize(vmin=df['RatingValue'].min(), vmax=df['RatingValue'].max())
    cmap = matplotlib.colormaps.get_cmap('autumn')

    # Get the unique values of the data that needs plotting.
    unique_values = df['RatingValue'].unique()

    # Create colored materials
    material_dict = create_colored_material_instances(unique_values=unique_values, cmap=cmap, norm=norm, mi_directory_path='/Game/', mi_name_prefix='fsa_point_value_')

    # Initalise a list to store cursor over text display
    actor_names = []
    csv_file_name = 'PointText.csv' # % str(uuid.uuid1())

    with open(csv_file_name, 'w') as csvfile:
        csvfile_writer = csv.writer(csvfile)
        csvfile_writer.writerow(['Name', 'Text'])
        # Plot data
        for index, row in df.iterrows():
            rgba = cmap(row['RatingValue'])
            x_value = 100 * (row['Easting'] - ue_world_origin_bng_eastings) # Multiply by 100 since UE coordinates are measured in cm.
            y_value = -1 * 100 * (row['Northing'] - ue_world_origin_bng_northings) # Multiply by 100 since UE coordinates are measured in cm. Multiple by minus 1 since the y-axis in UE is inverted.
            pnt = UnrealPoint(index, x_value, y_value, z_value, 'FSA_point_')
            pnt.material = material_dict[row['RatingValue']]
            pnt.tags = ['fsa']
            unreal_actor_name = pnt.spawn_actor_from_blueprint_class('/Game/Point_Blueprint')
            csvfile_writer.writerow([unreal_actor_name, row['BusinessType'] + '\nRating Date: ' + row['RatingDate'] + '\n' + row['LocalAuthorityName']])

    # import the point display text into a datatable of the same name as the csv file with the structure given by PointLabelStruct
    import_point_display_text(csv_file_name, '/Game/', '/Game/PointLabelStruct.PointLabelStruct')

    # Create legend and load as a texture in UE
    create_legend_texture(unique_values=unique_values, labels=['1', '2', '3', '4', '5'], cmap=cmap, norm=norm, texture_path='DataTextures/fsa_legend.png')