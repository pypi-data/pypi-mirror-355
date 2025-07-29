# -*- coding: utf-8 -*-
"""
Created on Thu 16 Dec 2021

@author: Alexandre Kenshilik Coche
@contact: alexandre.co@hotmail.fr

This module is a collection of tools for manipulating hydrological space-time
data, especially netCDF data. It has been originally developped to provide
preprocessing tools for CWatM (https://cwatm.iiasa.ac.at/) and HydroModPy
(https://gitlab.com/Alex-Gauvain/HydroModPy), but most functions have been
designed to be of general use.

"""

#%% Imports:
import logging
logging.basicConfig(level=logging.ERROR) # DEBUG < INFO < WARNING < ERROR < CRITICAL
logger = logging.getLogger(__name__)

import xarray as xr
xr.set_options(keep_attrs = True)
# import rioxarray as rio # Not necessary, the rio module from xarray is enough
import json
import pandas as pd
from pandas.errors import (ParserError as pd_ParserError)
import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
from affine import Affine
# from shapely.geometry import Point
# from shapely.geometry import Polygon
from shapely.geometry import mapping
import os
import re
import sys
import gc # garbage collector
import pathlib
# import matplotlib.pyplot as plt

from pysheds.grid import Grid
from pysheds.view import Raster, ViewFinder
from pysheds.pgrid import Grid as pGrid

# ========== see reproject() §Rasterize ======================================
# import geocube
# from geocube.api.core import make_geocube
# from geocube.rasterize import rasterize_points_griddata, rasterize_points_radial
# import functools
# =============================================================================

# import whitebox
# wbt = whitebox.WhiteboxTools()
# wbt.verbose = False

#%% LEGENDE: 
# ---- ° = à garder mais mettre à jour
# ---- * = à inclure dans une autre fonction ou supprimer


#%% LOADING & INITIALIZING DATASETS
###############################################################################
def use_standard_time(data_ds, *, var = None, infer_from = 'dims',):
    """
    Use a standard time variable as the temporal coordinate.
    Standardize its names into 'time'. If not the main time coordinate, swap 
    it with the main time coordinate.

    Parameters
    ----------
    data_ds : xarray.dataset
        Dataset whose temporal coordinate should be renamed.
    var : str, optional, default None
        ...
    infer_from : {'dims', 'coords', 'all'}
        Only used for xarray variables.
        To specify if the time coordinate should be infered from dimensions,
        coordinates or all variables (coordinates and data variables).

    Returns
    -------
    data_ds : xarray.dataset
        Dataset with the modified name for the temporal coordinate.

    """
# =============================================================================
#     # Rename 'valid_time' into 'time' (if necessary)
#     for time_avatar in ['valid_time', 'date']:
#         if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
#             if ((time_avatar in data_ds.coords) | (time_avatar in data_ds.data_vars)) \
#                 & ('time' not in data_ds.coords) & ('time' not in data_ds.data_vars):
#                 data_ds = data_ds.rename({time_avatar: 'time'})
#                 
#         elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
#             if (time_avatar in data_ds.columns) & ('time' not in data_ds.columns):
#                 data_ds = data_ds.rename(columns = {time_avatar: 'time'})
#     
#     
# =============================================================================
    
    print("Standardizing time dimension...")

    if isinstance(data_ds, xr.Dataset):
        if ('time' in data_ds.data_vars) | ('time' in data_ds.coords):
            data_ds = data_ds.rename(time = 'time0')
            print("   _ A variable 'time' was already present and was renammed to 'time0'")

    elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)): # Note: gpd.GeoDataFrame are also pd.DataFrames
        if 'time' in data_ds.columns:
            data_ds = data_ds.rename(columns = {'time': 'time0'})
            print("   _ A variable 'time' was already present and was renammed to 'time0'")
    elif isinstance(data_ds, xr.DataArray):
        if 'time' in data_ds.coords:
            data_ds = data_ds.rename(time = 'time0')
            print("   _ A variable 'time' was already present and was renammed to 'time0'")

    if infer_from == 'dims':
        time_dims = main_time_dims(data_ds)
        time_coords = main_time_dims(data_ds)
    elif infer_from == 'coords':
        time_dims = main_time_dims(data_ds)
        time_coords = main_time_dims(data_ds, all_coords = True)
    elif infer_from == 'all':
        time_dims = main_time_dims(data_ds)
        time_coords = main_time_dims(data_ds, all_coords = True, all_vars = True)
        
    if isinstance(time_dims, str): time_dims = [time_dims]
    if isinstance(time_coords, str): time_coords = [time_coords]
    
    
    if var is not None:
        # Rename the var specified by user into 'time'
        new_tvar = var
    else:
        # Rename the time coord into 'time'
        if time_coords != []:
            new_tvar = time_coords[0]
        else: # safeguard
            print("   _ Warning: No time dimension has been identified. Consider using `infer_from = 'coords'` or `infer_from = 'all'` arguments.")
            return data_ds
        
    if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
        data_ds = data_ds.rename({new_tvar: 'time'})
        print(f"   _ The variable '{new_tvar}' has been renamed into 'time'")
        
        # In the case of xarray variables, if the user-specified var is
        # not a dim, the function will try to swap it with the time dim
        if new_tvar not in time_dims:
            for d in time_dims:
                # Swap dims with the first dimension that has the same 
                # length as 'time'
                if data_ds['time'].size == data_ds.sizes[d]:
                    data_ds = data_ds.swap_dims({d: 'time'})
                    print(f"   _ The new variable 'time' (prev. '{new_tvar}') has been swaped with the dimension '{d}'")
                    break
                
                else:
                    print(r"   _ Warning: The new variable 'time' (prev. '{new_tvar}') is not a dimension, and no current dimension has been found to match. Consider trying `infer_from = 'coords'` or `infer_from = 'all'` arguments")
            
    elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
        data_ds = data_ds.rename(columns = {new_tvar: 'time'})
        print(f"   _ The variable '{new_tvar}' has been renamed into 'time'")

            
# =============================================================================
#     if not infer:
#         if isinstance(time_coord, str):
#             if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
#                 data_ds = data_ds.rename({time_coord: 'time'})
#             elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
#                 data_ds = data_ds.rename(columns = {time_coord: 'time'})
#         elif isinstance(time_coord, list):
#             print("Warning: Time could not be standardized because there are several time coordinate candidates. Consider passing the argument 'infer = True' in ghc.use_standard_time()")
#     
#     else:
#         if isinstance(time_coord, list):
#             time_coord = time_coord[0]
#         if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
#             time_coord_avatars = ['t', 'time', 'valid_time',
#                                   'forecast_period', 'date',
#                                   ]
#             time_vars = list(set(list(data_ds.data_vars)).intersection(set(time_coord_avatars)))
#             
#         elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
#             data_ds = data_ds.rename(columns = {time_coord: 'time'})
#     
#     # Swap the coordinate (if necessary)
#     if time_coord != []:
#         if time_coord != 'time':
#             data_ds = data_ds.swap_dims({time_coord: 'time'})
# =============================================================================
    
    # Make sure the time variable is a datetime
    if not np.issubdtype(data_ds.time, (np.datetime64)):
        try: data_ds['time'] = pd.to_datetime(data_ds['time'])
        except: print(f"   _ Warning: New 'time' variable (prev. '{new_tvar}') could not be converted into datetime dtype. Consider using `infer_from = 'coords'` or `infer_from = 'all'` arguments.")

    return data_ds


###############################################################################
def load_any(data, *, rebuild_time_val=False, name = None, decode_coords = 'all', 
             decode_times = True, **kwargs):
             # decode_times=True, decode_cf=True, decode_coords='all'):
    r"""
    This function loads any common spatio-temporal file or variable, without
    the need to think about the file or variable type.
    
    import geoconvert as gc
    data_ds = gc.load_any(r'D:\data.nc', decode_times = True, decode_coords = 'all')

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.
    name : str, optional, default None
        Name of main variable for tif or asc files.
    **kwargs: keyword args
        Argument passed to the xarray.open_dataset function call.
        May contain: 
            . decode_coords
            . decode_times
            . decode_cf
            > help(xr.open_dataset)

    Returns
    -------
    data_ds : TYPE
        DESCRIPTION.

    """
    # initialization
    kwargs['decode_coords'] = decode_coords
    kwargs['decode_times'] = decode_times
    
    # data is a variable
    if isinstance(data, (xr.Dataset, xr.DataArray)):
        data_ds = data.copy()
    
    elif isinstance(data, (gpd.GeoDataFrame, pd.DataFrame)):
        data_ds = data.copy()
    
    # data is a string/path
    elif isinstance(data, (str, pathlib.Path)):
        print("\nLoading data...")
        
        if not os.path.isfile(data):
            print("   Err: the path provided is not a file")
            return
        
        else:
            extension_src = os.path.splitext(data)[-1]
            
            # Adapt load kwargs:
            # These arguments are only used in pandas.DataFrame.to_csv():
            if extension_src != '.csv':
                for arg in ['sep', 'encoding']: 
                    if arg in kwargs: kwargs.pop(arg)
            # These arguments are only used in pandas.DataFrame.to_json():
            if extension_src != '.json':
                for arg in ['force_ascii']:
                    if arg in kwargs: kwargs.pop(arg)
            # These arguments are only used in xarray.open_dataset():
            if extension_src != '.nc':
                for arg in ['decode_coords']: 
                    if arg in kwargs: kwargs.pop(arg)    
            # These arguments are only used in xarray.open_dataset():
            if extension_src not in ['.nc', '.tif', '.asc']:
                for arg in ['decode_times']: 
                    if arg in kwargs: kwargs.pop(arg)  

            if extension_src in ['.shp', '.json', '.gpkg']:
                try: 
                    data_ds = gpd.read_file(data, **kwargs)
                except: # DataSourceError
                    try:
                        data_ds = pd.read_json(data, **kwargs)
                    except:
                        data_ds = json.load(open(data, "r"))
                        print("   Warning: The JSON file could not be loaded as a pandas.DataFrame and was loaded as a dict")
            
            elif os.path.splitext(data)[-1] in ['.csv']:
                try:
                    data_ds = pd.read_csv(data, **kwargs)
                except pd_ParserError:
                    logger.exception("")
                    print("\nTry to pass additional arguments to `geobricks.load_any()` such as column separator `sep` (see `help(pandas.read_csv)`)\n")
                    return
            
            elif extension_src == '.nc':
                try:
                    with xr.open_dataset(data, **kwargs) as data_ds:
                        data_ds.load() # to unlock the resource
    
                except:
                    kwargs['decode_times'] = False
                    print("   _ decode_times = False")
                    try:
                        with xr.open_dataset(data, **kwargs) as data_ds:
                            data_ds.load() # to unlock the resource
                    
                    except:
                        kwargs['decode_coords'] = False
                        print("   _ decode_coords = False")
                        with xr.open_dataset(data, **kwargs) as data_ds:
                            data_ds.load() # to unlock the resource      
                    
                    if rebuild_time_val:
                        print("   _ inferring time axis...")
                        time_coords = main_time_dims(data_ds, all_coords = True, all_vars = True)
                        time_coord = time_coords[0]
                        print(f"      . inferred time coordinate is {time_coord}")
                        units, reference_date = data_ds[time_coord].attrs['units'].split('since')
                        if units.replace(' ', '').casefold() in ['month', 'months', 'M']: 
                            freq = 'M'
                        elif units.replace(' ', '').casefold() in ['day', 'days', 'D']:
                            freq = 'D'
                        start_date = pd.date_range(start = reference_date, 
                                                   periods = int(data_ds[time_coord][0].values)+1, 
                                                   freq = freq) 
                        try:
                            data_ds[time_coord] = pd.date_range(start = start_date[-1], 
                                                            periods = data_ds.sizes[time_coord], 
                                                            freq = freq)
                        except: # SPECIAL CASE to handle truncated output files (from failed CWatM simulations)
                            data_ds = data_ds.where(data_ds[time_coord]<1e5, drop = True)
                            data_ds[time_coord] = pd.date_range(start = start_date[-1], 
                                                            periods = data_ds.sizes[time_coord], 
                                                            freq = freq)
                            
                        print(f"     . initial time = {data_ds[time_coord][0].values.strftime('%Y-%m-%d')} | final time = {data_ds[time_coord][-1].values.strftime('%Y-%m-%d')} | units = {units}")
                        
    
            elif extension_src in ['.tif', '.asc']:
                with xr.open_dataset(data, **kwargs) as data_ds:
                    data_ds.load() # to unlock the resource   
                
                if 'band' in data_ds.dims:
                    if data_ds.sizes['band'] == 1:
                        data_ds = data_ds.squeeze('band')
                        data_ds = data_ds.drop('band')
                if name is not None:
                    data_ds = data_ds.rename(band_data = name)
        
    else:
        print("Err: `data` input does not exist")
        return
    
    # Return
    return data_ds


###############################################################################
def main_var(data_ds):
    if isinstance(data_ds, xr.Dataset): # raster
        var = list(set(list(data_ds.data_vars)) - set(['x', 'y', 'X','Y', 'i', 'j',
                                                       'lat', 'lon', 
                                                       'spatial_ref', 
                                                       'LambertParisII',
                                                       'bnds', 'time_bnds',
                                                       'valid_time', 't', 'time',
                                                       'date',
                                                       'forecast_reference_time',
                                                       'forecast_period']))
# =============================================================================
#         if len(var) == 1:
#             var = var[0]
# =============================================================================
    
    elif isinstance(data_ds, xr.DataArray):
        var = data_ds.name
        
        if (var is None) | (var == ''):
            var = input("Name of the main variable: ")
    
    elif isinstance(data_ds, (gpd.GeoDataFrame, pd.DataFrame)): # vector
# =============================================================================
#         var = data_ds.loc[:, data_ds.columns != 'geometry']
# =============================================================================
        print("Name or id of the main data variable : ")
        i = 1
        for c in data_ds.columns:
            print(f"   {i}. {c}")
            i += 1
        col = input("")
        if col in data_ds.columns: var = col # selection by name
        else: var = data_ds.columns[int(col)-1] # selection by id
    
    elif isinstance(data_ds, pd.Series):
        var = data_ds.name
        
        if (var is None) | (var == ''):
            var = input("Name of the main variable: ")
    
    return var


###############################################################################
def main_space_dims(data_ds):
    
    if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
        x_var = list(set(list(data_ds.dims)).intersection(set(['x', 'X', 'lon', 'longitude'])))
        y_var = list(set(list(data_ds.dims)).intersection(set(['y', 'Y', 'lat', 'latitude'])))
    
    elif isinstance(data_ds, gpd.GeoDataFrame):
        x_var = list(set(list(data_ds.columns)).intersection(set(['x', 'X', 'lon', 'longitude'])))
        y_var = list(set(list(data_ds.columns)).intersection(set(['y', 'Y', 'lat', 'latitude'])))
    
    if len(x_var) == 1:
        x_var = x_var[0]
    if len(y_var) == 1:
        y_var = y_var[0]
    
    return x_var, y_var


###############################################################################
def main_time_dims(data_ds, all_coords = False, all_vars = False):
    """
    

    Parameters
    ----------
    data_ds : str, pathlib.Path, xarray.Dataset, xarray.DataArray or geopandas.GeoDataFrame
        Data to reproject. Supported file formats are *.tif*, *.asc*, *.nc* and vector 
        formats supported by geopandas (*.shp*, *.json*, ...) and pandas (*.csv...).
    all_coords : bool, optional, defualt False
        Only used if data_ds is a xarray variable.
        If ``False``, only dimensions are considered as potential time coordinates.
        If ``True``, even coordinates not associated to any dimension will be 
        considered as well as potential time coordinates (along ``dims``).
    all_vars : bool, optional, defualt False
        Only used if data_ds is a xarray variable.
        If ``True``, data variables (``data_vars``) will be considered as well 
        as potential time coordinates (along ``dims``).

    Returns
    -------
    var : str or list
        List of potential time coordinate names, the first one being the most relevant.
        If there is only one name, it is output directly as a string.

    """
    
    time_coord_avatars = ['time', 't', 'valid_time',
                          'forecast_period', 'date',
                          'time0',
                          # 'time_bnds',
                          # 'forecast_reference_time',
                          ]
    if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
        var = list(set(list(data_ds.dims)).intersection(set(time_coord_avatars)))
        if all_coords: # in this case, even non-dim coordinates will be considered as potential time coordinates
            var = list(set(var).union(set(list(data_ds.coords)).intersection(set(time_coord_avatars))))
        if all_vars: # in this case, even data variables will be considered as potential time coordinates
            if isinstance(data_ds, xr.Dataset):
                var = list(set(var).union(set(list(data_ds.data_vars)).intersection(set(time_coord_avatars))))
            elif isinstance(data_ds, xr.DataArray):
                print("Note: `all_vars` argument is unnecessary with xarray.DataArrays")

    elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
        var = list(set(list(data_ds.columns)).intersection(set(time_coord_avatars)))
    
# =============================================================================
#     if len(var) == 1:
#         var = var[0]
# =============================================================================
    if len(var) > 1:
        # If there are several time coordinate candidates, the best option will
        # be put in first position. The best option is determined via a series
        # of rules:
            
        candidates = []
        
        if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
            # Only 1D datetime variables will be considered
            for v in var:
                if np.issubdtype(data_ds[v], np.datetime64):
                    if len(data_ds[v].dims) == 1:
                        candidates.append(v)
            
            # The first remaining candidate with the largest number of values will
            # be selected
            coords_length = {data_ds[v].size:v for v in candidates}
            first_var = coords_length[max(coords_length.keys())]
            
        elif isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
            # Only datetime variables will be considered
            for v in var:
                if np.issubdtype(data_ds[v], np.datetime64):
                    candidates.append(v)
            
            # The first remaining candidate will be selected
            first_var = candidates[0]
        
        var.pop(var.index(first_var))
        var.insert(0, first_var)
    
    return var


###############################################################################
def get_filelist(data, 
                 *, extension = None,
                 tag = ''):
    """
    This function converts a folder (or a file) in a list of relevant files.

    Parameters
    ----------
    data: str or iterable
        Folder, filepath or iterable of filepaths
    extension: str
        Extension.

    Returns
    -------
    data_folder : str
        Root of the files.
    tiletype : str
        Extension of files to retrieve.

    """
    
    # if extension[0] == '.': extension = extension[1:]
    if isinstance(extension, str):
        if extension[0] != '.': extension = '.' + extension
    
    # ---- Data is a single element
    
    # if data is a single string/path
    if isinstance(data,  (str, pathlib.Path)): 
        # if this string points to a folder
        if os.path.isdir(data): 
            data_folder = data    
            filelist = [f for f in os.listdir(data_folder)
                             if ( (os.path.isfile(os.path.join(data_folder, f))) \
                                 & (os.path.splitext(os.path.join(data_folder, f))[-1] == extension) \
                                     & (len(re.compile(f".*({tag}).*").findall(f)) > 0) )]
            
        # if this string points to a file
        else: 
            data_folder = os.path.split(data)[0]    # root of the file 
            filelist = [data]
    
    # ---- Data is an iterable
    elif isinstance(data, (list, tuple)):
        # [Safeguard] It is assumed that data contains an iterable of files
        if not os.path.isfile(data[0]):
            print("Err: Argument should be a folder, a filepath or a list of filepath")
            return
        
        data_folder = os.path.split(data[0])[0] # root of the first element of the list
        filelist = list(data)
        
        
    return data_folder, filelist 


###############################################################################
#%%% ° pick_dates_fields
def pick_dates_fields(*, input_file, output_format = 'NetCDF', **kwargs):
    """
    % DESCRIPTION:
    This function extracts the specified dates or fields from NetCDF files that
    contain multiple dates or fields, and exports it as a single file.
    
    
    % EXAMPLE:
    import geoconvert as gc
    gc.pick_dates_fields(input_file = r"D:/path/test.nc", 
                  dates = ['2020-10-15', '2021-10-15'])

    % OPTIONAL ARGUMENTS:
    > output_format = 'NetCDF' (default) | 'GeoTIFF'
    > kwargs:
        > dates = ['2021-10-15', '2021-10-19']
        > fields = ['T2M', 'PRECIP', ...]
    """    
    
    with xr.open_dataset(input_file) as _dataset:
        _dataset.load() # to unlock the resource
    
    #% Get arguments (and build output_name):
    # ---------------------------------------
    _basename = os.path.splitext(input_file)[0]
    
    # Get fields:
    if 'fields' in kwargs:
        fields = kwargs['fields']
        if isinstance(fields, str): fields = [fields]
        else: fields = list(fields) # in case fields are string or tuple
    else:
        fields = list(_dataset.data_vars) # if not input_arg, fields = all
    
    # Get dates:
    if 'dates' in kwargs:
        dates = kwargs['dates']
        if isinstance(dates, str): 
            output_file = '_'.join([_basename, dates, '_'.join(fields)])
            dates = [dates]
        else: 
            dates = list(dates) # in case dates are tuple
            output_file = '_'.join([_basename, dates[0], 'to', 
                                    dates[-1], '_'.join(fields)])

    else:
        dates = ['alldates'] # if not input_arg, dates = all  
        output_file = '_'.join([_basename, '_'.join(fields)])
        
    
    #% Standardize terms:
    # -------------------
    if 't' in list(_dataset.dims):
        print('Renaming time coordinate')
        _dataset = _dataset.rename(t = 'time')    

    if 'lon' in list(_dataset.dims) or 'lat' in list(_dataset.dims):
        print('Renaming lat/lon coordinates')
        _dataset = _dataset.rename(lat = 'latitude', lon = 'longitude')
        # Change the order of coordinates to match QGIS standards:
        _dataset = _dataset.transpose('time', 'latitude', 'longitude')
        # Insert georeferencing metadata to match QGIS standards:
        _dataset.rio.write_crs("epsg:4326", inplace = True)
        # Insert metadata to match Panoply standards: 
        _dataset.longitude.attrs = {'units': 'degrees_east',
                                    'long_name': 'longitude'}
        _dataset.latitude.attrs = {'units': 'degrees_north',
                                    'long_name': 'latitude'}
    
    if 'X' in list(_dataset.dims) or 'Y' in list(_dataset.dims):
        print('Renaming X/Y coordinates')
        _dataset = _dataset.rename(X = 'x', Y = 'y')
        # Change the order of coordinates to match QGIS standards:
        _dataset = _dataset.transpose('time', 'y', 'x')
        # Insert metadata to match Panoply standards: 
        _dataset.x.attrs = {'standard_name': 'projection_x_coordinate',
                            'long_name': 'x coordinate of projection',
                            'units': 'Meter'}
        _dataset.y.attrs = {'standard_name': 'projection_y_coordinate',
                            'long_name': 'y coordinate of projection',
                            'units': 'Meter'}

        
# =============================================================================
#     # Rename coordinates (ancienne version):
#     try:
#         _dataset.longitude
#     except AttributeError:
#         _dataset = _dataset.rename({'lon':'longitude'})
#     try:
#         _dataset.latitude
#     except AttributeError:
#         _dataset = _dataset.rename({'lat':'latitude'})    
#     try:
#         _dataset.time
#     except AttributeError:
#         _dataset = _dataset.rename({'t':'time'}) 
# =============================================================================
    
    #% Extraction and export:
    # -----------------------
    # Extraction of fields:
    _datasubset = _dataset[fields]
    # Extraction of dates:
    if dates != 'alldates':
        _datasubset = _datasubset.sel(time = dates)

    if output_format == 'NetCDF':
        _datasubset.attrs = {'Conventions': 'CF-1.6'} # I am not sure...
        
        # Export:
        _datasubset.to_netcdf(output_file + '.nc')
    
    elif output_format == 'GeoTIFF':
        _datasubset.rio.to_raster(output_file + '.tiff')
        
        
#%% GEOREFERENCING
###############################################################################
# Georef (ex-decorate_NetCDF_for_QGIS)
def georef(data, *, data_type = 'other', include_crs = True, export_opt = False, crs = None, **time_kwargs):   
    r"""
    Description
    -----------
    Il est fréquent que les données de source externe présentent des défauts
    de formattage (SCR non inclus, coordonnées non standard, incompatibilité
    avec QGIS...).
    Cette fonction permet de générer un raster ou shapefile standardisé, 
    en particulier du point de vue de ses métadonnées, facilitant ainsi les
    opérations de géotraitement mais aussi la visualisation sous QGIS.
    
    Exemple
    -------
    import geoconvert as gc
    gc.georef(data = r"D:\CWatM\raw_results\test1\modflow_watertable_monthavg.nc", 
              data_type = 'CWatM')
    
    Parametres
    ----------
    data : str or xr.Dataset (or xr.DataArray)
        Chemin d'accès au fichier à modifier
        (le fichier original ne sera pas altéré, un nouveau fichier '(...)_QGIS.nc'
         sera créé.)
    data_type : str
        Type de données :
            'modflow' | 'DRIAS-Climat 2020' | 'DRIAS-Eau 2021' \ 'SIM 2021' |
            'DRIAS-Climat 2022' \ 'Climat 2022' | 'DRIAS-Eau 2024' \ 'SIM 2024' |
            'CWatM' | 'autre' \ 'other'
            (case insensitive)
    include_crs : bool, optional
        DESCRIPTION. The default is True.
    export_opt : bool, optional
        DESCRIPTION. The default is True.
        Le NetCDF crée est directement enregistré dans le même dossier que 
        le fichier d'origine, en rajoutant 'georef' à son nom.
    crs : int, optional
        Destination CRS, only necessary when data_type == 'other' The default is None.
    **time_kwargs : 
        Arguments for ``use_standard_time`` function:
            - var : time variable name (str), optional, default None
            - infer_from : {'dims', 'coords', 'all'}, optional, default 'dims' 

    Returns
    -------
    xarray.Dataset or geopandas.GeoDataFrame. 
    
    """
    
# =============================================================================
#     if include_crs is False:
#         if crs is not None:
#             include_crs = True
# =============================================================================
    
    # ---- NetCDF de ModFlow
    # --------------------
    if data_type.casefold() == 'modflow': 
        # Load
        data_ds = load_any(data, decode_coords = 'all', decode_times = False)
        
        print("\nFormatting data...")
        # Add standard attributes for coordinates (mandatory for QGIS to correctly read data)
        data_ds.x.attrs = {'standard_name': 'projection_x_coordinate',
                            'long_name': 'x coordinate of projection',
                            'units': 'Meter'}
        data_ds.y.attrs = {'standard_name': 'projection_y_coordinate',
                            'long_name': 'y coordinate of projection',
                            'units': 'Meter'}
        print("   _ Standard attributes added for coordinates x and y")
        
        # Add CRS
        data_epsg = 2154 # Lambert 93
        crs_suffix = ''
        if include_crs:
            data_ds.rio.write_crs(data_epsg, inplace = True)
            print(f'   _ Coordinates Reference System (epsg:{data_epsg}) included.')
        else:
            print(f'   _ Coordinates Reference System not included. {data_epsg} has to be manually specified in QGIS')
            crs_suffix = 'nocrs'
        
    # ========== USELESS ==========================================================
    #     data_ds = data_ds.transpose('time', 'y', 'x')
    # =============================================================================


    # ---- NetCDF de CWatM
    # Inclusion du SCR
    # ------------------
    elif data_type.casefold() == 'cwatm'.casefold():
        # Load
        data_ds = load_any(data, decode_coords = 'all', decode_times = False)
        
        print("\nFormatting data...")
        # Add CRS
        data_epsg = 2154 # Lambert 93
        crs_suffix = ''
        if include_crs:
            data_ds.rio.write_crs(data_epsg, inplace = True)
            print(f'   _ Coordinates Reference System (epsg:{data_epsg}) included.')
        else:
            print(f'   _ Coordinates Reference System not included. {data_epsg} has to be manually specified in QGIS')
            crs_suffix = 'nocrs'
    
    
    # ---- NetCDF de la DRIAS-Climat 2020 et de la DRIAS-Eau 2021
    # Données SAFRAN (tas, prtot, rayonnement, vent... ) "DRIAS-2020"
    # ainsi que : 
    # Données SURFEX (evapc, drainc, runoffc, swe, swi...) "EXPLORE2-SIM2 2021"
    # ------------------------------------------------------------
    if data_type.replace(" ", "").casefold() in ['drias2020', 'drias-climat2020',
                                'sim2021', 'drias-eau2021']:         
        # Load
        data_ds = load_any(decode_coords = 'all')
        
        print("\nFormating data...")
        # Create X and Y coordinates if necessary, from i and j
        list_var_lowcase = [v.casefold() for v in list(data_ds.coords) + list(data_ds.data_vars)]
        if 'x' not in list_var_lowcase:
            data_ds = data_ds.assign_coords(
                X = ('i', 52000 + data_ds.i.values*8000))
            print("   _ X values created from i")
        if 'y' not in list_var_lowcase:
            data_ds = data_ds.assign_coords(
                Y = ('j', 1609000 + data_ds.j.values*8000))
            print("   _ Y values created from j")
        # Replace X and Y as coordinates, and rename them
        data_ds = data_ds.swap_dims(i = 'X', j = 'Y')
        print("   _ Coordinates i and j replaced with X and Y")
        data_ds = data_ds.rename(X = 'x', Y = 'y')
        print("   _ Coordinates renamed as lowcase x and y [optional]")
        # Get main variable
        var = main_var(data_ds)
        print(f"   _ Main variables are: {', '.join(var)}")
        # Ensure that lat, lon, i and j will be further loaded by xarray as coords
        data_ds[var].attrs['coordinates'] = 'x y i j lat lon'
        print("   _ x, y, i, j, lat, lon ensured to be read as coordinates")

# ============== USELESS ======================================================
#         # Reorder data, to ensure QGIS Mesh detects the correct data set   
#         data_ds = data_ds[[var, 'x', 'y', 'time']]
#         print("   _ Data reordered [safety]")
# =============================================================================
# ============== USELESS ======================================================
#         # To avoid conflicts with missing values
#         data_ds[var].encoding.pop('missing_value')
#         data_ds['lat'].encoding.pop('missing_value')
#         # data_ds['lat'].encoding['_FillValue'] = np.nan
#         data_ds['lon'].encoding.pop('missing_value')
#         # data_ds['lon'].encoding['_FillValue'] = np.nan
# =============================================================================
        
        # Add standard attributes for coordinates (mandatory for QGIS to correctly read data)
        data_ds.x.attrs = {'standard_name': 'projection_x_coordinate',
                            'long_name': 'x coordinate of projection',
                            'units': 'Meter'}
        data_ds.y.attrs = {'standard_name': 'projection_y_coordinate',
                            'long_name': 'y coordinate of projection',
                            'units': 'Meter'}
        print("   _ Standard attributes added for coordinates x and y")
        
        # Add CRS
        data_epsg = 27572 # Lambert zone II
        crs_suffix = ''
        if include_crs:
            data_ds.rio.write_crs(data_epsg, inplace = True)
            print(f'   _ Coordinates Reference System (epsg:{data_epsg}) included. (NB: This might alter Panoply georeferenced vizualisation)')
        else:
            print(f'   _ Coordinates Reference System not included. {data_epsg} has to be manually specified in QGIS')
            crs_suffix = 'nocrs'
         # Incompatibilité QGIS - Panoply :
         # Pour une raison inconnue, l'inclusion du CRS 27572 ("Lambert 
         # Zone II" / "NTF (Paris)" pose problème pour le géo-référencement
         # dans Panoply (c'est comme si Panoply prenait {lat = 0 ; lon = 0} 
         # comme origine de la projection). Sans 'spatial_ref' incluse dans le
         # netCDF, Panoply géo-référence correctement les données, probablement
         # en utilisant directement les variables 'lat' et 'lon'.
      
        
    # ---- NetCDF de la DRIAS-Climat 2022 
    # Données SAFRAN (tas, prtot, rayonnement, vent... ) "EXPLORE2-Climat 2022" 
    # -------------------------------------------------------------------------
    elif data_type.replace(" ", "").casefold() in ['drias2022', 'climat2022', 'drias-climat2022']:
        # Load
        data_ds = load_any(data, decode_cf = False)

        print("\nFormating data...")
        # Correcting the spatial_ref
# =============================================================================
#         data_ds['LambertParisII'] = xr.DataArray(
#             data = np.array(-2147220352.0),
#             coords = {'LambertParisII': -2147220352.0},
#             attrs = {'grid_mapping_name': 'lambert_conformal_conic_1SP',
#                      'latitude_of_origin': 52.0,
#                      'central_meridian': 0.0,
#                      'false_easting': 600000.0,
#                      'false_northing': 2200000.0,
#                      'epsg': 27572,
#                      'references': 'http://www.umr-cnrm.fr/spip.php?article125&lang=en'}) 
#         crs_suffix = 'georef'
# =============================================================================
        data_epsg = 27572 # Lambert zone II
        if include_crs:
            # data_ds = data_ds.drop('LambertParisII')
            # data_ds.rio.write_crs(f'epsg:{data_epsg}', inplace = True)
            data_ds = standard_grid_mapping(data_ds, data_epsg)
            print(f'   _ Coordinates Reference System (epsg:{data_epsg}) included. (NB: This might alter Panoply georeferenced vizualisation)')
            crs_suffix = ''
        else:
            print(f'   _ Coordinates Reference System not included. {data_epsg} has to be manually specified in QGIS')
            crs_suffix = 'nocrs'
        # Get main variable
        var = main_var(data_ds)
        print(f"   _ Main variable are: {', '.join(var)}")
        # Ensure that lat, and lon will be further loaded by xarray as coords
        data_ds[var].encoding['coordinates'] = 'x y lat lon'
        if 'coordinates' in data_ds[var].attrs:
            data_ds[var].attrs.pop('coordinates')
        data_ds.lat.encoding['grid_mapping'] = data_ds[var].encoding['grid_mapping']
        data_ds.lon.encoding['grid_mapping'] = data_ds[var].encoding['grid_mapping']
        print("   _ x, y, lat, lon ensured to be read as coordinates [safety]")
        # Remove grid_mapping in attributes (it is already in encoding)
        if 'grid_mapping' in data_ds[var].attrs:
            data_ds[var].attrs.pop('grid_mapping')
    
    
    # ---- NetCDF de la DRIAS-Eau 2024 
    # Données SURFEX (evapc, drainc, runoffc, swe, swi...) "EXPLORE2-SIM2 2024" 
    # -------------------------------------------------------------------------
    elif data_type.replace(" ", "").replace("-", "").casefold() in [
            'sim2024', 'driaseau2024']: 
        # Load
        data_ds = load_any(data, decode_cf = False)

        print("\nFormating data...")
        # Correcting the spatial_ref
# =============================================================================
#         data_ds['LambertParisII'] = xr.DataArray(
#             data = np.array(-2147220352.0),
#             coords = {'LambertParisII': -2147220352.0},
#             attrs = {'grid_mapping_name': 'lambert_conformal_conic_1SP',
#                      'latitude_of_origin': 52.0,
#                      'central_meridian': 0.0,
#                      'false_easting': 600000.0,
#                      'false_northing': 2200000.0,
#                      'epsg': 27572,
#                      'references': 'http://www.umr-cnrm.fr/spip.php?article125&lang=en'}) 
#         crs_suffix = ''
# =============================================================================
        data_epsg = 27572 # Lambert zone II
        if include_crs:
            # if ('LambertParisII' in data_ds.coords) | ('LambertParisII' in data_ds.data_vars):
            #     data_ds = data_ds.drop('LambertParisII')
            # data_ds.rio.write_crs(data_epsg, inplace = True)
            data_ds = standard_grid_mapping(data_ds, data_epsg)
            print(f'   _ Coordinates Reference System (epsg:{data_epsg}) included. (NB: This might alter Panoply georeferenced vizualisation)')
            crs_suffix = ''
        else:
            print(f'   _ Coordinates Reference System not included. {data_epsg} has to be manually specified in QGIS')
            crs_suffix = 'nocrs'
        
        # Create X and Y coordinates if necessary, from i and j
        list_var_lowcase = [v.casefold() for v in list(data_ds.coords) + list(data_ds.data_vars)]
        data_ds = data_ds.assign_coords(
            X = ('x', 52000 + data_ds.x.values*8000))
        print("   _ X values corrected from erroneous x")
        data_ds = data_ds.assign_coords(
            Y = ('y', 1609000 + data_ds.y.values*8000))
        print("   _ Y values corrected from erroneous y")
        # Replace X and Y as coordinates, and rename them
        data_ds = data_ds.swap_dims(x = 'X', y = 'Y')
        print("   _ Coordinates x and y replaced with X and Y")
        data_ds = data_ds.drop(['x', 'y'])
        print("   _ Previous coordinates x and y removed")
        data_ds = data_ds.rename(X = 'x', Y = 'y')
        print("   _ Coordinates renamed as lowcase x and y [optional]")
        # Get main variable
        var = main_var(data_ds)
        print(f"   _ Main variable are: {', '.join(var)}")
        
        # Ensure that lat, and lon will be further loaded by xarray as coords
        data_ds[var].encoding['coordinates'] = 'x y lat lon'
        if 'coordinates' in data_ds[var].attrs:
            data_ds[var].attrs.pop('coordinates')
        # Reporting grid_mapping to coords/vars that should not be displayed in QGIS:
        for c in ['lat', 'lon']: 
            if (c in data_ds.coords) | (c in data_ds.data_vars):
                data_ds[c].encoding['grid_mapping'] = data_ds[var].encoding['grid_mapping']
        print("   _ x, y, lat, lon ensured to be read as coordinates [safety]")
       # ======== USELESS ============================================================
       #         for c in ['lat', 'lon', 'time_bnds']:
       #             if c in data_ds.data_vars:
       #                 data_ds = data_ds.set_coords([c])
       # =============================================================================
        
       # Remove grid_mapping in attributes (it is already in encoding)
        if 'grid_mapping' in data_ds[var].attrs:
            data_ds[var].attrs.pop('grid_mapping')
        
# ============== USELESS ======================================================
#         # Reorder data, to ensure QGIS Mesh detects the correct data set   
#         data_ds = data_ds[[var, 'x', 'y', 'time']]
#         print("   _ Data reordered [safety]")
# =============================================================================
# ============== USELESS ======================================================
#         # To avoid conflicts with missing values
#         data_ds[var].encoding.pop('missing_value')
#         data_ds['lat'].encoding.pop('missing_value')
#         # data_ds['lat'].encoding['_FillValue'] = np.nan
#         data_ds['lon'].encoding.pop('missing_value')
#         # data_ds['lon'].encoding['_FillValue'] = np.nan
# =============================================================================
        
        # Add standard attributes for coordinates (mandatory for QGIS to correctly read data)
        data_ds.x.attrs = {'standard_name': 'projection_x_coordinate',
                            'long_name': 'x coordinate of projection',
                            'units': 'metre'}
        data_ds.y.attrs = {'standard_name': 'projection_y_coordinate',
                            'long_name': 'y coordinate of projection',
                            'units': 'metre'}
        print("   _ Standard attributes added for coordintes x and y")


    # ---- Autres fichiers ou variables
    # Inclusion du SCR
    # ------------------
# =============================================================================
#     elif data_type.casefold() in ['autre', 'other']:
# =============================================================================
    else:
        # Load
        data_ds = load_any(data, decode_times = True, decode_coords = 'all')
        
        x_var, y_var = main_space_dims(data_ds)
# ====== old standard time handling ===========================================
#         time_coord = main_time_dims(data_ds)
# =============================================================================
        
        # Standardize spatial coords
# =============================================================================
#         if 'X' in data_ds.coords:
#             data_ds = data_ds.rename({'X': 'x'})
#         if 'Y' in data_ds.coords:
#             data_ds = data_ds.rename({'Y': 'y'})
#         if 'latitude' in data_ds.coords:
#             data_ds = data_ds.rename({'latitude': 'lat'})
#         if 'longitude' in data_ds.coords:
#             data_ds = data_ds.rename({'longitude': 'lon'})
# =============================================================================
        if x_var == 'X':
            data_ds = data_ds.rename({'X': 'x'})
        if y_var == 'Y':
            data_ds = data_ds.rename({'Y': 'y'})
        if y_var == 'latitude':
            data_ds = data_ds.rename({'latitude': 'lat'})
        if x_var == 'longitude':
            data_ds = data_ds.rename({'longitude': 'lon'})
        
        # Standardize time coord
# ====== old standard time handling ===========================================
#         if len(time_coord) == 1:
#             data_ds = data_ds.rename({time_coord: 'time'})
# =============================================================================
        data_ds = use_standard_time(data_ds, **time_kwargs)
        
        if isinstance(data_ds, gpd.GeoDataFrame):
            print("\nFormatting data...")
            # Add CRS
            crs_suffix = ''
            if include_crs:
                if crs is not None:
                    data_epsg = crs
                    data_ds.set_crs(epsg = crs, 
                                    inplace = True, 
                                    allow_override = True)
                    # data_ds = standard_grid_mapping(data_ds, crs)
                    print(f'   _ Coordinates Reference System (epsg:{crs}) included.')
                else:
                    print("   _ Warning: No crs argument was passed")
            else:
                print('   _ Coordinates Reference System not included.')
                crs_suffix = 'nocrs'
        
        elif isinstance(data_ds, xr.Dataset):        
            print("\nFormatting data...")
            # Add CRS
            crs_suffix = ''
            if include_crs:
                if crs is not None:
                    data_ds.rio.write_crs(crs, inplace = True)
                    print(f'   _ Coordinates Reference System (epsg:{crs}) included.')
                else:
                    print("   _ Warning: No crs argument was passed")
            else:
                print('   _ Coordinates Reference System not included.')
                crs_suffix = 'nocrs'
            
            # Add standard attributes for coordinates (mandatory for QGIS to correctly read data)
            if ('x' in list(data_ds.coords)) & ('y' in list(data_ds.coords)):
                data_ds.x.attrs = {'standard_name': 'projection_x_coordinate',
                                    'long_name': 'x coordinate of projection',
                                    'units': 'metre'}
                data_ds.y.attrs = {'standard_name': 'projection_y_coordinate',
                                    'long_name': 'y coordinate of projection',
                                    'units': 'metre'}
                print("   _ Standard attributes added for coordinates x and y")
            elif ('lon' in list(data_ds.coords)) & ('lat' in list(data_ds.coords)):
                data_ds.lon.attrs = {'standard_name': 'longitude',
                                     'long_name': 'longitude',
                                     'units': 'degrees_east'}
                data_ds.lat.attrs = {'standard_name': 'latitude',
                                     'long_name': 'latitude',
                                     'units': 'degrees_north'}
                print("   _ Standard attributes added for coordinates lat and lon")


    # ---- General changes
    var_list = main_var(data_ds)
    for var in var_list:
        for optional_attrs in ['AREA_OR_POINT', 'STATISTICS_MAXIMUM',
                               'STATISTICS_MEAN', 'STATISTICS_MINIMUM',
                               'STATISTICS_STDDEV', 'STATISTICS_VALID_PERCENT']:
            if optional_attrs in data_ds[var].attrs:
                data_ds[var].attrs.pop(optional_attrs)
    
    # ---- Export
    # ---------
    if export_opt == True:
        print('\nExporting...')
        # Output filepath
        if isinstance(data, (str, pathlib.Path)):
            (folder_name, _basename) = os.path.split(data)
            (file_name, file_extension) = os.path.splitext(_basename)
            output_file = os.path.join(folder_name, f"{'_'.join([file_name, 'georef', crs_suffix])}{file_extension}")
        else:
            print("   _ As data input is not a file, the result is exported to a standard directory")
            output_file = os.path.join(os.getcwd(), f"{'_'.join(['data', 'georef', crs_suffix])}.nc")
        
        # Export
        export(data_ds, output_file)
        
        
    # ---- Return variable
    return data_ds


    # =========================================================================
    #%    Mémos / Corrections bugs
    # =========================================================================
    # Si jamais il y a un problème de variable qui se retrouve en 'data_var'
    # au lieu d'etre en 'coords' : 
    #     data_ds = data_ds.set_coords('i')
    
    # S'il y a un problème d'incompatibilité 'missing_value' / '_FillValue' :
    #     data_ds['lon'] = data_ds.lon.fillna(np.nan)
    #     data_ds['lat'] = data_ds.lat.fillna(np.nan)
    
    # Si jamais une variable non essentielle pose problème à l'export : 
    #     data_ds = data_ds.drop('lon')
    #     data_ds = data_ds.drop('lat')
    
    # Pour trouver les positions des valeurs nan :
    #     np.argwhere(np.isnan(data_ds.lon.values))
    
    # Pour reconvertir la date
    #     units, reference_date = ds.time.attrs['units'].split('since')
    #     ds['time'] = pd.date_range(start = reference_date, 
    #                                periods = ds.sizes['time'], freq = 'MS')
    # =========================================================================


    # Créer les coordonnées 'x' et 'y'...
# =============================================================================
#         # ... à partir des lon.lat :
#         # LAISSÉ TOMBÉ, PARCE QUE LEURS VALEURS DE LATITUDE SONT FAUSSES [!]
#         coords_xy = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(4326), 
#                                             rasterio.crs.CRS.from_epsg(27572), 
#                                             np.array(data_ds.lon).reshape((data_ds.lon.size), order = 'C'),
#                                             np.array(data_ds.lat).reshape((data_ds.lat.size), order = 'C'))
#         
#         # data_ds['x'] = np.round(coords_xy[0][0:data_ds.lon.shape[1]], -1) 
#         
#         # Arrondi à la dizaine à cause de l'approx. initiale sur les lat/lon :                                               
#         x = np.round(coords_xy[0], -1).reshape(data_ds.lon.shape[0], 
#                                                data_ds.lon.shape[1], 
#                                                order = 'C')
#         # donne un motif qui se répète autant de fois qu'il y a de latitudes
#         y = np.round(coords_xy[1], -1).reshape(data_ds.lon.shape[1], 
#                                                data_ds.lon.shape[0], 
#                                                order = 'F')
#         # donne un motif qui se répète autant de fois qu'il y a de longitudes
#         
#         # data_ds['x'] = x[0,:] 
#         # data_ds['y'] = y[0,:]
#         data_ds = data_ds.assign_coords(x = ('i', x[0,:]))
#         data_ds = data_ds.assign_coords(y = ('j', y[0,:]))
# =============================================================================


###############################################################################
def standard_grid_mapping(data, epsg = None):
    """
    QGIS needs a standard structure for grid_mapping information:
       - grid_mapping info should be in encodings and not in attrs
       - grid_mapping info should be stored in a coordinate names 'spatial_ref'
       - ...
    In MeteoFrance data, these QGIS standards are not met.
    This function standardizes grid_mapping handling, so that it is 
    compatible with QGIS.

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.
    epsg : TYPE
        DESCRIPTION.

    Returns
    -------
    data_ds : TYPE
        DESCRIPTION.

    """
    # ---- Load
    data_ds = load_any(data)
    # Get main variable
    var_list = main_var(data_ds)
    
    for var in var_list[::-1]:
        # ---- Get the potential names of grid_mapping variable and clean all 
        # grid_mapping information
        
        # Remove all the metadata about grid_mapping, and save grid_mapping names
        names = set()
        if 'grid_mapping' in data_ds.attrs:
            names.add(data_ds.attrs['grid_mapping'])
            data_ds.attrs.pop('grid_mapping')
        if "grid_mapping" in data_ds.encoding:
            names.add(data_ds.encoding['grid_mapping'])
            data_ds.encoding.pop('grid_mapping')
        if 'grid_mapping' in data_ds[var].attrs:
            names.add(data_ds[var].attrs['grid_mapping'])
            data_ds[var].attrs.pop('grid_mapping')
        if "grid_mapping" in data_ds[var].encoding:
            names.add(data_ds[var].encoding['grid_mapping'])
            data_ds[var].encoding.pop('grid_mapping')

    # Drop all variable or coord corresponding to the previously founded 
    # grid_mapping names
    for n in list(names):
        if n in data_ds.data_vars:
            temp = data_ds[n]
            data_ds = data_ds.drop(n)
        if n in data_ds.coords:
            temp = data_ds[n]
            data_ds = data_ds.reset_coords(n, drop = True)
        
    if epsg is None:
        # Use the last grid_mapping value as the standard spatial_ref
        dummy_epsg = 2154
        data_ds.rio.write_crs(dummy_epsg, inplace = True) # creates the spatial_ref structure and mapping
        data_ds['spatial_ref'] = temp
    else:
        data_ds.rio.write_crs(epsg, inplace = True)

    
    return data_ds


###############################################################################
def standard_fill_value(data_ds, *, var=None, attrs=None, encod=None):
    
    # Initializations
    if var is None:
        var_list = main_var(data_ds)
    elif isinstance(var, str):
        var_list = [var]
    elif isinstance(var, list):
        var_list = var
    
    if isinstance(data_ds, xr.Dataset):
        for var in var_list:
            if attrs is None:
                attrs = data_ds[var].attrs
            if encod is None:
                encod = data_ds[var].encoding
            
            # Clean all fill_value info
            if '_FillValue' in data_ds[var].attrs:
                data_ds[var].attrs.pop('_FillValue')
            if 'missing_value' in data_ds[var].attrs:
                data_ds[var].attrs.pop('missing_value')
            if 'missing_value' in data_ds[var].attrs:
                data_ds[var].attrs.pop('missing_value')
                
            # Set the fill_value, according to a hierarchical rule
            if '_FillValue' in encod:
                nodata = encod['_FillValue']
                data_ds[var].encoding['_FillValue'] = nodata
            elif '_FillValue' in attrs:
                nodata = attrs['_FillValue']
                data_ds[var].encoding['_FillValue'] = nodata
            elif 'missing_value' in encod:
                nodata = encod['missing_value']
                data_ds[var].encoding['_FillValue'] = nodata
            elif 'missing_value' in attrs:
                nodata = attrs['missing_value']
                data_ds[var].encoding['_FillValue'] = nodata
            else:
                nodata = np.nan
                data_ds[var].encoding['_FillValue'] = nodata
        
    elif isinstance(data_ds, xr.DataArray):
        if attrs is None:
            attrs = data_ds.attrs
        if encod is None:
            encod = data_ds.encoding
        
        # Clean all fill_value info
        if '_FillValue' in data_ds.attrs:
            data_ds.attrs.pop('_FillValue')
        if 'missing_value' in data_ds.attrs:
            data_ds.attrs.pop('missing_value')
        if 'missing_value' in data_ds.attrs:
            data_ds.attrs.pop('missing_value')
            
        # Set the fill_value, according to a hierarchical rule
        if '_FillValue' in encod:
            nodata = encod['_FillValue']
            data_ds.encoding['_FillValue'] = nodata
        elif '_FillValue' in attrs:
            nodata = attrs['_FillValue']
            data_ds.encoding['_FillValue'] = nodata
        elif 'missing_value' in encod:
            nodata = encod['missing_value']
            data_ds.encoding['_FillValue'] = nodata
        elif 'missing_value' in attrs:
            nodata = attrs['missing_value']
            data_ds.encoding['_FillValue'] = nodata
        else:
            nodata = np.nan
            data_ds.encoding['_FillValue'] = nodata
        
    return data_ds, nodata


#%% FILE MANAGEMENT
###############################################################################
def merge_data(data, 
               *, extension = None, 
               tag = '', 
               flatten = False):
    """
    This function merge all NetCDF inside a folder.

    Parameters
    ----------
    data: str or iterable
        Folder, filepath or iterable of filepaths.

    Returns
    -------
    Merged xarray.Dataset.
    """
    
    # ---- Load file list
    # If data is a list of files:
    if isinstance(data, (list, tuple)):
        # If the list contains paths
        if all([isinstance(data[i], (str, pathlib.Path)) 
                for i in range(0, len(data))]): 
            data_folder = os.path.split(data[0])[0]
            filelist = data 
            #filelist = [os.path.split(d)[-1] for d in data]
            extension = os.path.splitext(filelist[0])[-1]
        # If the list contains xarray or geopandas variables
        elif all([isinstance(data[i], (xr.Dataset, xr.DataArray, 
                                       gpd.GeoDataFrame, pd.DataFrame)) 
                  for i in range(0, len(data))]):
            data_folder = None
            filelist = data
        else:
            print("Err: Mixed data types")
            return
    # If data is a folder:
    elif isinstance(data, (str, pathlib.Path)):
        data_folder, filelist = get_filelist(data, extension = extension, tag = tag)
        filelist = [os.path.join(data_folder, f) for f in filelist]
    # If data is a xarray or a geopandas variable
    elif isinstance(data, (xr.Dataset, xr.DataArray, gpd.GeoDataFrame, pd.DataFrame)):
        data_folder = None
        filelist = [data]
        
    # if extension[0] == '.': extension = extension[1:]
    if isinstance(extension, str):
        if extension[0] != '.': extension = '.' + extension

    if len(filelist) > 1:
        print("Merging files...")
        
        if (extension in ['.nc', '.tif', '.asc']) | all([isinstance(data[i], (xr.Dataset, xr.DataArray)) 
                                                     for i in range(0, len(data))]): 
            c = 1
            ds_list = []
            # ---- Append all xr.Datasets into a list
            for f in filelist:
                ds_list.append(load_any(f, 
                                        decode_coords = 'all', 
                                        decode_times = True))
                if isinstance(f, (str, pathlib.Path)):
                    f_text = f
                else:
                    f_text = type(f)
                print(f"      . {f_text}  ({c}/{len(filelist)})")
                c += 1
                
            # ---- Backup of attributes and encodings
            var_list = main_var(ds_list[0])
    # ========== useless ==========================================================
    #         attrs = ds_list[0][var].attrs.copy()
    # =============================================================================
            encod = {}
            for var in var_list:
                encod[var] = ds_list[0][var].encoding.copy()
        
            # ---- Merge
            merged_ds = xr.merge(ds_list) # Note: works only when doublons are identical
    # ========== wrong ============================================================
    #         merged_ds = xr.concat(ds_list, dim = 'time')
    # =============================================================================
            # Order y-axis from max to min (because order is altered with merge)
            _, y_var = main_space_dims(merged_ds)
            merged_ds = merged_ds.sortby(y_var, ascending = False)
    # ========== useless ==========================================================
    #         merged_ds = merged_ds.sortby('time') # In case the files are not loaded in time order   
    # =============================================================================
            
            # ---- Transferring encodings (_FillValue, compression...)
            for var in var_list:
                merged_ds[var].encoding = encod[var]
            return merged_ds
        
        elif (extension in ['.shp', '.json', '.geojson']) | all([isinstance(data[i], gpd.GeoDataFrame) 
                                                             for i in range(0, len(data))]):
            ### Option 1: data is flattened over the time axis
            if flatten:
                # This variable will store the names of the concatenated columns
                global varying_columns
                varying_columns = []
                
                def agg_func(arg):
                    global varying_columns
    
                    if len(set(arg.values)) == 1:
                        return arg.values[0]
                    else:
                        varying_columns.append(arg.name)
                        return ', '.join(str(v) for v in arg.values)
    # =========== list of texts are not correctly reloaded in python... ===========
    #                     return list(arg.values)
    # =============================================================================
                
                c = 1
# =============================================================================
#                 gdf_list = []
#                 # ---- Append all gpd.GeoDataFrame into a list
#                 for f in filelist:
#                     gdf_list.append(load_any(f))
#                     print(f"      . {f}  ({c}/{len(filelist)})")
#                     c += 1
#                 
#                 merged_gdf = pd.concat(gdf_list)
# =============================================================================
                f = filelist[0]
                merged_gdf = load_any(f)
                if isinstance(f, (str, pathlib.Path)):
                    f_text = f
                else:
                    f_text = type(f)
                print(f"      . {f_text}  ({c}/{len(filelist)})")
                for f in filelist[1:]:
                    merged_gdf = merged_gdf.merge(load_any(f), 
                                                  how = 'outer',
                                                  # on = merged_df.columns, 
                                                  )
                    if isinstance(f, (str, pathlib.Path)):
                        f_text = f
                    else:
                        f_text = type(f)
                    print(f"      . {f_text}  ({c}/{len(filelist)})")
                    c += 1
                
    # ========== previous method ==================================================
                # x_var, y_var = main_space_dims(gdf_list[0])
                # merged_gdf = merged_gdf.dissolve(by=[x_var, y_var], aggfunc=agg_func)
                # # Convert the new index (code_ouvrage) into a column as at the origin
                # merged_gdf.reset_index(inplace = True, drop = False)
    # =============================================================================
                merged_gdf['geometry2'] = merged_gdf['geometry'].astype(str)
                merged_gdf = merged_gdf.dissolve(by='geometry2', aggfunc=agg_func)
                # Convert the new index (code_ouvrage) into a column as at the origin
                merged_gdf.reset_index(inplace = True, drop = True)
                
                varying_columns = list(set(varying_columns))
                
                # Correct the dtypes of the concatenated columns, because fiona does
                # not handle list dtypes
                merged_gdf[varying_columns] = merged_gdf[varying_columns].astype(str)
                
                return merged_gdf
            
            else: # No flattening
                c = 1
# ========= previous method with concat =======================================
#                 gdf_list = []
#                 # ---- Append all gpd.GeoDataFrame into a list
#                 for f in filelist:
#                     gdf_list.append(load_any(f))
#                     gdf_list[c]['annee'] = pd.to_datetime(gdf_list[c]['annee'], format = '%Y')
#                     print(f"      . {f}  ({c}/{len(filelist)})")
#                     c += 1
#                 
#                 merged_gdf = pd.concat(gdf_list)
# =============================================================================
                f = filelist[0]
                merged_gdf = load_any(f)
                if isinstance(f, (str, pathlib.Path)):
                    f_text = f
                else:
                    f_text = type(f)
                print(f"      . {f_text}  ({c}/{len(filelist)})")
                for f in filelist[1:]:
                    merged_gdf = merged_gdf.merge(load_any(f), 
                                                  how = 'outer',
                                                  # on = merged_df.columns, 
                                                  )
                    if isinstance(f, (str, pathlib.Path)):
                        f_text = f
                    else:
                        f_text = type(f)
                    print(f"      . {f_text}  ({c}/{len(filelist)})")
                    c += 1
                
                return merged_gdf      
    
        elif (extension in ['.csv']) | all([isinstance(data[i], pd.DataFrame) 
                                          for i in range(0, len(data))]):
            c = 1
            f = filelist[0]
            merged_df = load_any(f)
            if isinstance(f, (str, pathlib.Path)):
                f_text = f
            else:
                f_text = type(f)
            print(f"      . {f_text}  ({c}/{len(filelist)})")
            for f in filelist[1:]:
                merged_df = merged_df.merge(load_any(f), 
                                            how = 'outer',
                                            # on = merged_df.columns, 
                                            )
                if isinstance(f, (str, pathlib.Path)):
                    f_text = f
                else:
                    f_text = type(f)
                print(f"      . {f_text}  ({c}/{len(filelist)})")
                c += 1
            
            return merged_df  
            
    
    elif len(filelist) == 1:
        print("Warning: Only one file was found.")
        return load_any(filelist[0])
    
    elif len(filelist) == 0:
        print("Err: No file was found")
        return



#%% REPROJECTION
###############################################################################
def reproject(data, *, src_crs=None, base_template=None, bounds=None,  
              x0=None, y0=None, mask=None, rasterize = False, main_vars = None,
              rasterize_mode = ['sum', 'dominant', 'and'], **rio_kwargs):
    r"""
    Reproject space-time data, and rasterize it if specified.

    Parameters
    ----------
    data : str, pathlib.Path, xarray.Dataset, xarray.DataArray or geopandas.GeoDataFrame
        Data to reproject. Supported file formats are *.tif*, *.asc*, *.nc* and vector 
        formats supported by geopandas (*.shp*, *.json*, ...).
    src_crs : int or str or rasterio.crs.CRS, optional, default None
        Coordinate reference system of the source (``data``).    
        When passed as an *integer*, ``src_crs`` refers to the EPSG code. 
        When passed as a *string*, ``src_crs`` can be OGC WKT string or Proj.4 string.
    base_template : str, pathlib.Path, xarra.Dataarray or geopandas.GeoDataFrame, optional, default None
        Filepath, used as a template for spatial profile. Supported file formats
        are *.tif*, *.nc* and vector formats supported by geopandas (*.shp*, *.json*, ...).
    bounds : iterable or None, optional, default None
        Boundaries of the target domain as a tuple (x_min, y_min, x_max, y_max).
    x0: number, optional, default None
        Origin of the X-axis, used to align the reprojection grid. 
    y0: number, optional, default None
        Origin of the Y-axis, used to align the reprojection grid. 
    mask : str, pathlib.Path, xarra.Dataarray or geopandas.GeoDataFrame, optional, default None
        Filepath of mask used to clip the data. 
    rasterize : bool, default False
        Option to rasterize data (if ``data`` is a vector data).
    main_vars : iterable, default None
        Data variables to rasterize. Only used if ``rasterize`` is ``True``.
        If ``None``, all variables in ``data`` are rasterized.
    rasterize_mode : str or list of str, or dict, default ['sum', 'dominant', 'and']
        Defines the mode to rasterize data:
            
            - for numeric variables: ``'mean'`` or ``'sum'`` (default)
            - for categorical variables: ``'percent'`` or ``'dominant'`` (default)
            
                - ``'dominant'`` rises the most frequent level for each cell
                - ``'percent'`` creates a new variable per level, which stores 
                the percentage (from 0 to 100) of occurence of this level compared
                to all levels, for each cell.
                
            - for boolean variables: ``'or'`` or ``'and'`` (default)
        The modes can be specified for each variable by passing ``rasterize_mode``
        as a dict: ``{'<var1>': 'mean', '<var2>': 'percent', ...}``. This argument
        specification makes it possible to force a numeric variable to be rasterized
        as a categorical variable. Unspecified variables will be rasterized with the default mode.
        
    
    **rio_kwargs : keyword args, optional, defaults are None
        Argument passed to the ``xarray.Dataset.rio.reproject()`` function call.
        
        **Note**: These arguments are prioritary over ``base_template`` attributes.
        
        May contain: 
            
            - ``dst_crs`` : str
            - ``resolution`` : float or tuple
            - ``shape`` : tuple (int, int)
            - ``transform`` : Affine
            - ``nodata`` : float or None
            - ``resampling`` : 
                
               - see ``help(rasterio.enums.Resampling)``
               - most common are: ``5`` (average), ``13`` (sum), ``0`` (nearest), 
                 ``9`` (min), ``8`` (max), ``1`` (bilinear), ``2`` (cubic)...
               - the functionality ``'std'`` (standard deviation) is also available
            
            - see ``help(xarray.Dataset.rio.reproject)``

    Returns
    -------
    Reprojected xarray.Dataset or geopandas.GeoDataFrame.

    """
    
    #%%%% Load data, base and mask
    # ===========================
    data_ds = load_any(data, decode_times = True, decode_coords = 'all')
    base_ds = None
    if base_template is not None:
        base_ds = load_any(base_template, decode_times = True, decode_coords = 'all')
    if mask is not None:
        mask_ds = load_any(mask, decode_times = True, decode_coords = 'all')
    
    if src_crs is not None:
        if isinstance(data_ds, xr.Dataset): # raster
            data_ds.rio.write_crs(src_crs, inplace = True)
        elif isinstance(data_ds, gpd.GeoDataFrame): # vector
            data_ds.set_crs(epsg = src_crs, inplace = True, allow_override = True)
    
    # Identify spatial coord names
# =============================================================================
#     for yname in ['latitude', 'lat', 'y', 'Y']:
#         if yname in data_ds.coords:
#             yvar = yname
#     for xname in ['longitude', 'lon', 'x', 'X']:
#         if xname in data_ds.coords:
#             xvar = xname
# =============================================================================
    xvar, yvar = main_space_dims(data_ds)
    
    # Initialize x0 and y0 if None
    if isinstance(data_ds, (xr.Dataset, xr.DataArray)): # raster
        x_res, y_res = data_ds.rio.resolution()
        if x0 is None:
            x0 = data_ds[xvar][0].item() + x_res/2
        if y0 is None:
            y0 = data_ds[yvar][0].item() + y_res/2
    elif isinstance(data_ds, gpd.GeoDataFrame): # vector
        if x0 is None:
            x0 = data_ds.total_bounds[0] # xmin
        if y0 is None:
            y0 = data_ds.total_bounds[1] # ymin
    
    #%%%% Compute parameters
    # =====================
    print("\nComputing parameters...")
    
    # ---- Safeguards against redundant arguments
    # -------------------------------------------
    if ('transform' in rio_kwargs) & ('shape' in rio_kwargs) & (bounds is not None):
        print("   _ Err: bounds cannot be passed alongside with both transform and shape")
        return
    
    if 'resolution' in rio_kwargs:
        if ('shape' in rio_kwargs) | ('transform' in rio_kwargs):
        # safeguard to avoid RioXarrayError
            print("   _ Err: resolution cannot be used with shape or transform.")
            return
        
    if (bounds is not None) & (mask is not None):
        print("   _ Err: bounds and mask cannot be passed together")
        return
    
    
    # ---- Backup of rio_kwargs
    # -------------------------
    rio_kwargs0 = rio_kwargs.copy()
    
    # Info message
    if ('transform' in rio_kwargs) & (bounds is not None):
        if (bounds[0] != rio_kwargs['transform'][2]) | (bounds[3] != rio_kwargs['transform'][5]):
            print("   _ ...")
    
    
    # ---- No base_template
    # ---------------------
    if base_ds is None:
        ### Retrieve <dst_crs> (required parameter)
        if 'dst_crs' not in rio_kwargs:
            if isinstance(data_ds, (xr.Dataset, xr.DataArray)): # raster
                rio_kwargs['dst_crs'] = data_ds.rio.crs.to_epsg()
            elif isinstance(data_ds, gpd.GeoDataFrame): # vector
                rio_kwargs['dst_crs'] = data_ds.crs.to_epsg()

            
    # ---- Base_template
    # ------------------
    # if there is a base, it will be used after being updated with passed parameters
    else:
        base_kwargs = {}
        
        ### 1. Retrieve all the available info from base:
        if isinstance(base_ds, (xr.Dataset, xr.DataArray)):
            # A- Retrieve <dst_crs> (required parameter)
            if 'dst_crs' not in rio_kwargs:
                try:
                    rio_kwargs['dst_crs'] = base_ds.rio.crs.to_epsg()
                except:
                    if isinstance(data_ds, (xr.Dataset, xr.DataArray)): # raster
                        rio_kwargs['dst_crs'] = data_ds.rio.crs.to_epsg()
                    elif isinstance(data_ds, gpd.GeoDataFrame): # vector
                        rio_kwargs['dst_crs'] = data_ds.crs.to_epsg()
            
            # B- Retrieve <shape> and <transform>
            base_kwargs['shape'] = base_ds.rio.shape
            base_kwargs['transform'] = base_ds.rio.transform()
            # Note that <resolution> is ignored from base_ds
                
        elif isinstance(base_ds, gpd.GeoDataFrame):
            # A- Retrieve <dst_crs> (required parameter)
            if 'dst_crs' not in rio_kwargs:
                try:
                    rio_kwargs['dst_crs'] = base_ds.crs.to_epsg()
                except:
                    if isinstance(data_ds, (xr.Dataset, xr.DataArray)): # raster
                        rio_kwargs['dst_crs'] = data_ds.rio.crs.to_epsg()
                    elif isinstance(data_ds, gpd.GeoDataFrame): # vector
                        rio_kwargs['dst_crs'] = data_ds.crs.to_epsg()
            
            # B- Retrieve <shape> and <transform>
            if 'resolution' in rio_kwargs:
                # The bounds of gpd base are used with the user-defined resolution
                # in order to compute 'transform' and 'shape' parameters:
                x_res, y_res = format_xy_resolution(
                    resolution = rio_kwargs['resolution'])
                shape, x_min, y_max = get_shape(
                    x_res, y_res, base_ds.total_bounds, x0, y0)
                base_kwargs['transform'] = Affine(x_res, 0.0, x_min,
                                                  0.0, y_res, y_max)
                base_kwargs['shape'] = shape
            else:
                print("   _ Err: resolution needs to be passed when using a vector base")
                return
            
        ### 2. Update <base_kwargs> with <rio_kwargs>
        for k in rio_kwargs:
            base_kwargs[k] = rio_kwargs[k]
        # Replace rio_kwargs with the updated base_kwargs
        rio_kwargs = base_kwargs
    
    
    # ---- Mask
    # ---------
    # <mask> has priority over bounds or rio_kwargs
    if mask is not None:
        # Reproject the mask
        if isinstance(mask_ds, gpd.GeoDataFrame):
            mask_ds.to_crs(crs = rio_kwargs['dst_crs'], inplace = True)
            bounds_mask = mask_ds.total_bounds
        elif isinstance(mask_ds, (xr.Dataset, xr.DataArray)):
            mask_ds = mask_ds.rio.reproject(dst_crs = rio_kwargs['dst_crs'])
            bounds_mask = (mask_ds.rio.bounds()[0], mask_ds.rio.bounds()[3],
                           mask_ds.rio.bounds()[2], mask_ds.rio.bounds()[1])
    else:
        bounds_mask = None
    
    
    # ---- Bounds
    # -----------
    # <bounds> has priority over rio_kwargs
    if (bounds is not None) | (bounds_mask is not None):
        if bounds is not None:
            print("   _ Note that bounds should be in the format (x_min, y_min, x_max, y_max)")
        elif bounds_mask is not None:
            bounds = bounds_mask
            
        ### Apply <bounds> values to rio arguments
        if ('shape' in rio_kwargs0):
            # resolution will be defined from shape and bounds
            x_res, y_res = format_xy_resolution(bounds = bounds, 
                                                shape = rio_kwargs['shape'])
            rio_kwargs['transform'] = Affine(x_res, 0.0, bounds[0],
                                              0.0, y_res, bounds[3])
            
        elif ('resolution' in rio_kwargs0):
            # shape will be defined from resolution and bounds
            x_res, y_res = format_xy_resolution(
                resolution = rio_kwargs['resolution'])
            shape, x_min, y_max = get_shape(
                x_res, y_res, bounds, x0, y0)
            rio_kwargs['transform'] = Affine(x_res, 0.0, x_min,
                                              0.0, y_res, y_max)
            rio_kwargs['shape'] = shape
            
        # elif ('transform' in rio_kwargs0):
        else:
            if isinstance(data_ds, (xr.Dataset, xr.DataArray)):
                # shape will be defined from transform and bounds
                if not 'transform' in rio_kwargs:
                    rio_kwargs['transform'] = data_ds.rio.transform()
                x_res, y_res = format_xy_resolution(
                    resolution = (rio_kwargs['transform'][0],
                                  rio_kwargs['transform'][4]))
                shape, x_min, y_max = get_shape(
                    x_res, y_res, bounds, x0, y0)
                rio_kwargs['transform'] = Affine(x_res, 0.0, x_min,
                                                  0.0, y_res, y_max)
                rio_kwargs['shape'] = shape
        
    
    # ---- Resolution
    # ---------------
    if ('resolution' in rio_kwargs) and ('transform' in rio_kwargs):
        x_res, y_res = format_xy_resolution(
            resolution = rio_kwargs['resolution'])
        transform = list(rio_kwargs['transform'])
        transform[0] = x_res
        transform[4] = y_res
        rio_kwargs['transform'] = Affine(*transform[0:6])
        rio_kwargs.pop('resolution')   
        
    
    # ---- Resampling
    # ---------------
    if 'resampling' not in rio_kwargs:
        # by default, resampling is 5 (average) instead of 0 (nearest)
        rio_kwargs['resampling'] = rasterio.enums.Resampling(5)


    #%%%% Reproject
    # ===========
    print("\nReprojecting...")
    
    if isinstance(data_ds, (xr.Dataset, xr.DataArray)): # raster
        # ---- Reproject raster
        # Backup of attributes and encodings
        if isinstance(data_ds, xr.Dataset):
            attrs_dict = {var: data_ds[var].attrs.copy() for var in data_ds.data_vars}
            encod_dict = {var: data_ds[var].encoding.copy() for var in data_ds.data_vars}
        elif isinstance(data_ds, xr.DataArray):
            attrs_dict = data_ds.attrs.copy()
            encod_dict = data_ds.encoding.copy()
        
        # Handle timedelta, as they are not currently supported (https://github.com/corteva/rioxarray/discussions/459)
        if isinstance(data_ds, xr.Dataset):
            NaT_dict = {}
            for var in data_ds.data_vars:
                NaT_dict[var] = False
    # ========== previous handmade method =========================================
    #             # Get one non-nan value
    #             sample_non_nan_val = data_ds[var].median(skipna = True)
    #             # If this value is a timedelta:
    #             if isinstance(sample_non_nan_val, (pd.Timedelta, np.timedelta64)):
    # =============================================================================
                if np.issubdtype(data_ds[var], np.timedelta64):
                    NaT_dict[var] = True
                    
                    data_ds[var] = data_ds[var].dt.days
                    data_ds[var].encoding = encod_dict[var]
        elif isinstance(data_ds, xr.DataArray):
            NaT_dict = False
            if np.issubdtype(data_ds, np.timedelta64):
                NaT_dict = True
                
                data_ds = data_ds.dt.days
                data_ds.encoding = encod_dict
        
        if ('x' in list(data_ds.coords)) & ('y' in list(data_ds.coords)) & \
            (('lat' in list(data_ds.coords)) | ('lon' in list(data_ds.coords))):
            # if lat and lon are among coordinates, they should be temporarily moved
            # to variables to be reprojected
            data_ds = data_ds.reset_coords(['lat', 'lon'])
        
        if rio_kwargs['resampling'] == 'std': # special case for standard deviation
                                              # because std is not part of rasterio
                                              # resampling methods.
            rio_kwargs.pop('resampling')
            
            data_reprj_mean = data_ds.rio.reproject(
                resampling = rasterio.enums.Resampling(5), # average
                **rio_kwargs)
            
            square_ds = data_ds**2
            
            sumsquare = square_ds.rio.reproject(
                resampling = rasterio.enums.Resampling(13), # sum,
                **rio_kwargs)
            
            n_upscale = abs(np.prod(data_reprj_mean.rio.resolution())/np.prod(data_ds.rio.resolution()))
            if n_upscale > 1:
                data_reprj = np.sqrt(abs(1/n_upscale*sumsquare - data_reprj_mean**2))
            else:
                print("Err: Standard Deviation can only be computed if there is a downscaling. A resolution argument should be passed")
        
        else: # normal case
            data_reprj = data_ds.rio.reproject(**rio_kwargs) # rioxarray

        
        if ('x' in list(data_ds.coords)) & ('y' in list(data_ds.coords)) & \
            (('lat' in list(data_ds.coords)) | ('lon' in list(data_ds.coords))):
            # if lat and lon are among coordinates, they should be temporarily moved
            # to variables to be reprojected
            data_reprj = data_reprj.set_coords(['lat', 'lon'])
        
# ======= NOT FINISHED ========================================================
#         # Handle timedelta
#         if NaT:
#             val = pd.to_timedelta(data_reprj[var].values.flatten(), unit='D').copy()
#             data_reprj[var] = val.to_numpy().reshape(data_reprj[var].shape)
#             # It is still required to precise the dimensions...
# =============================================================================
        
        ds_reprj = data_reprj
        
        # Correct _FillValues for all data_variables
        if isinstance(data_ds, xr.Dataset):
            for var in attrs_dict:
                data_reprj, _ = standard_fill_value(
                    data_ds = data_reprj, var = var, 
                    encod = encod_dict[var], attrs = attrs_dict[var])
                if NaT_dict[var]:
                    data_reprj[var] = pd.to_timedelta(data_reprj[var], units = 'D')
        elif isinstance(data_ds, xr.DataArray):
            data_reprj, _ = standard_fill_value(
                data_ds = data_reprj, 
                encod = encod_dict, attrs = attrs_dict)
            if NaT_dict:
                data_reprj = pd.to_timedelta(data_reprj, units = 'D')
    
    elif isinstance(data_ds, gpd.GeoDataFrame): # vector
        # ---- Reproject vector
        data_reprj = data_ds.to_crs(epsg = rio_kwargs['dst_crs'], inplace = False)
        
        # ---- Clip vector
        if mask is not None:
            if isinstance(mask_ds, gpd.GeoDataFrame):
                data_reprj = data_reprj.clip(mask = mask_ds)
            elif isinstance(mask_ds, (xr.Dataset, xr.DataArray)):
                data_reprj = data_reprj.clip(mask = bounds_mask) # faster
        
        if rasterize: 
        # ---- Rasterize vector
            # Safeguard (maybe useless)
            if 'transform' not in rio_kwargs:
                if 'resolution' in rio_kwargs:
                    x_res, y_res = format_xy_resolution(
                        resolution = rio_kwargs['resolution'])
                    shape, x_min, y_max = get_shape(
                        x_res, y_res, data_reprj.total_bounds, x0, y0)
                    
                    transform_ = Affine(x_res, 0.0, x_min,
                                        0.0, y_res, y_max)
                    
                    rio_kwargs['transform'] = transform_
                    rio_kwargs.pop('resolution')
                    
                else:
                    print("Err: A resolution is needed to rasterize vector data")
                    return
            # height = int((data_ds.total_bounds[3] - data_ds.total_bounds[1]) / rio_kwargs['resolution'])
            # width = int((data_ds.total_bounds[2] - data_ds.total_bounds[0]) / rio_kwargs['resolution'])

            # transform_ = Affine(rio_kwargs['resolution'], 0.0, data_ds.total_bounds[0], 
            #                     0.0, -rio_kwargs['resolution'], data_ds.total_bounds[3])
        
            
# =============================================================================
#             global measure_main_var
#             measure_main_var = main_var(data_reprj)                
# =============================================================================
# =============================================================================
#             for var in data_reprj.loc[:, data_reprj.columns != 'geometry']:
# =============================================================================
            if main_vars is None:
                # var_list = data_ds[:, data_ds.columns != 'geometry'].columns
                var_list = data_ds.drop('geometry', axis = 1).columns
            else:
                var_list = main_vars
            
            if 'geometry' in var_list: var_list = list(set(var_list) - set('geometry'))
            
            
# =============================================================================
#             geo_grid = make_geocube(
#                 vector_data = data_reprj,
#                 measurements = [var],
#                 # measurements = data_reprj.columns[:-1], # chaque colonne deviendra un xr.DataArray
#                 # out_shape = shape,
#                 # transform = rio_kwargs['transform'],
#                 resolution = (rio_kwargs['transform'][0], rio_kwargs['transform'][4]),
#                 rasterize_function = functools.partial(rasterize_image, merge_alg = merge_alg),
#                 )
# =============================================================================
# Between rasterio and geocube, rasterio has been chosen, for several reasons:
#   - rasterio installation raises less conflicts
#   - advantages of geocube are almost as complexe to use as to implement them with rasterio:
#      - the 'categorical_enums' functionality is affected by merge_alg
#      - no way to output the most common level
            
            ds_reprj = xr.Dataset()
            x_coords = np.arange(x_min, x_min + shape[1]*x_res, x_res).astype(np.float32)
            y_coords = np.arange(y_max, y_max + shape[0]*y_res, y_res).astype(np.float32)
            coords = [y_coords, x_coords]
            dims = ['y', 'x']
            
            numeric_col = data_reprj.select_dtypes(include = 'number').columns
            timedelta_col = data_reprj.select_dtypes(include = ['timedelta']).columns
            bool_col = data_reprj.select_dtypes(include = bool).columns
            categorical_col = data_reprj.select_dtypes(include = [object, 'category'], 
                                                     exclude = ['number', 'datetime', 'datetimetz', 'timedelta', bool]).columns
            
            # Format <rasterize_mode>:
            # ------------------------
            # Correct categorical_col if unusual categorical variables are indicated in rasterize_mode 
            if isinstance(rasterize_mode, dict):
                for var in rasterize_mode:
                    # if user has specified a 'categorical' mode for a variable
                    if rasterize_mode[var] in ['dominant', 'percent']:
                        # data_reprj[var].astype('category')
                        # and if this variable has not already been identified as categorical (for example if it is numeric)
                        if not var in categorical_col:
                            # then it is appended to categorical variables list
                            categorical_col.append(var)
            
            # Safeguard
            if isinstance(rasterize_mode, str):
                rasterize_mode = [rasterize_mode]
            
            if isinstance(rasterize_mode, list):
                rm_dict = {}
                for rm in rasterize_mode: 
                    if rm in ['sum', 'mean']:
                        rm_dict_add = {num_var: rm for num_var in (set(numeric_col).union(set(timedelta_col))).intersection(set(var_list))}
                    elif rm in ['dominant', 'percent']:
                        rm_dict_add = {num_var: rm for num_var in set(categorical_col).intersection(set(var_list))}
                    elif rm in ['and', 'or']:
                        rm_dict_add = {num_var: rm for num_var in set(bool_col).intersection(set(var_list))}
                    
                    rm_dict = {**rm_dict, **rm_dict_add} # merge dictionnaries
                
                rasterize_mode = rm_dict
            
            for var in var_list:
                if var not in rasterize_mode:
                    if var in set(numeric_col).union(set(timedelta_col)):
                        rasterize_mode[var] = 'sum'
                    elif var in categorical_col:
                        rasterize_mode[var] = 'dominant'
                    elif var in bool_col:
                        rasterize_mode[var] = 'and'
            
            x_var, y_var = main_space_dims(data_reprj)
            if not isinstance(x_var, list):
                x_var = [x_var]
            if not isinstance(y_var, list):
                y_var = [y_var]
            # Numeric space variables are not summed
            for x in x_var:
                if x in rasterize_mode:
                    rasterize_mode[x] = "mean"
            for y in y_var:
                if y in rasterize_mode:
                    rasterize_mode[y] = "mean"            

            # Time axis management
# ======== previous version ===================================================
#             datetime_col = data_reprj.select_dtypes(include = ['datetime', 'datetimetz']).columns
# =============================================================================
            datetime_col = main_time_dims(data_reprj)
            if len(datetime_col) == 1:
                print(f"A time axis has been detected in column '{datetime_col[0]}'")
                t_coords = data_reprj[datetime_col[0]].unique()
                coords = [t_coords] + coords
                dims = ['time'] + dims
                
                for num_var in (set(numeric_col).union(set(timedelta_col))).intersection(set(var_list)):
                    data_3D = []
                    for t in t_coords:
                        data_reprj_temp = data_reprj[data_reprj[datetime_col[0]] == t]   
                    
                        rasterized_data = rasterio.features.rasterize(
                            [(val['geometry'], val[num_var]) for _, val in data_reprj_temp.iterrows()],
                            out_shape = shape,
                            transform = rio_kwargs['transform'],
                            fill = 0, # np.nan
                            merge_alg = rasterio.enums.MergeAlg.add,
                            all_touched = False,
                            # dtype = rasterio.float64, # rasterio.float32,
                            )
                        
                        # Normalize if mode == 'mean' instead of 'sum'
                        if rasterize_mode[num_var] == "mean":
                            rasterized_weight = rasterio.features.rasterize(
                                [(val['geometry'], 1) for _, val in data_reprj_temp.iterrows()],
                                out_shape = shape,
                                transform = rio_kwargs['transform'],
                                fill = 0, # np.nan
                                merge_alg = rasterio.enums.MergeAlg.add,
                                all_touched = False,
                                # dtype = rasterio.float64, # rasterio.float32,
                                )

                            # Normalize
                            rasterized_data = rasterized_data / rasterized_weight
                            
                            # Replace inf with np.nan
                            np.nan_to_num(rasterized_data, posinf = np.nan)
                        
                        data_3D.append(rasterized_data)
                        
                    # Fill the dataset
                    ds_reprj[num_var] = xr.DataArray(np.array(data_3D),
                                                     coords = coords,
                                                     dims = dims)
                    
                        # Replace 0 with np.nan
# =============================================================================
#                         ds_reprj = ds_reprj.where(ds_reprj != 0)
# =============================================================================

                # Categorical variables: level by level
                for cat_var in set(categorical_col).intersection(set(var_list)):
                    # Case 'dominant' (more frequent):
                    if rasterize_mode[cat_var] == "dominant":
                        data_3D = []
                        for t in t_coords:
                            data_reprj_temp = data_reprj[data_reprj[datetime_col[0]] == t]   
                        
                            levels = data_reprj[cat_var].unique()
                            # String/categorical data are not handled well by GIS softwares...
                            id_levels = {i:levels[i] for i in range(0, len(levels))}
                            for i in id_levels:
                                data_reprj_lvl = data_reprj_temp[data_reprj_temp[cat_var] == levels[i]] 
                                rasterized_levels = rasterio.features.rasterize(
                                    [(val['geometry'], 1) for _, val in data_reprj_lvl.iterrows()],
                                    out_shape = shape,
                                    transform = rio_kwargs['transform'],
                                    fill = 0, # np.nan
                                    merge_alg = rasterio.enums.MergeAlg.add,
                                    all_touched = False,
                                    # dtype = rasterio.float32,
                                    )
                                
                                if i == 0: # 1er passage
                                    rasterized_data = rasterized_levels.copy().astype(int)
                                    rasterized_data[:] = -1
                                    rasterized_data[rasterized_levels > 0] = i
                                    rasterized_levels_prev = rasterized_levels.copy()
                                else:
                                    rasterized_data[rasterized_levels > rasterized_levels_prev] = i
                                    rasterized_levels_prev = np.maximum(rasterized_levels,
                                                                        rasterized_levels_prev)
                                    
                            data_3D.append(rasterized_data)
                        
                        ds_reprj[cat_var] = xr.DataArray(np.array(data_3D),
                                                         coords = coords,
                                                         dims = dims)
                        
                        # Inform
                        nodata_level = {-1: 'nodata'}
                        id_levels = {**nodata_level, **id_levels}
                        ds_reprj[f"{cat_var}_levels"] = ', '.join([f"{k}: {id_levels[k]}" for k in id_levels]) # str(id_levels)
                        ds_reprj[cat_var].attrs['levels'] = ', '.join([f"{k}: {id_levels[k]}" for k in id_levels])
# =============================================================================
#                         print(f"Info: Variable `{cat_var}` is categorized as follow:")
#                         print('\n'.join([f"  . {k}: {id_levels[k]}" for k in id_levels]))
# =============================================================================
                        
                    # Case 'percent' (compute frequency among other levels):
                    elif rasterize_mode[cat_var] == "percent":
                        levels = data_reprj[cat_var].unique()
                        for l in levels:
                            data_reprj_lvl = data_reprj[data_reprj[cat_var] == l]
                            
                            data_3D = []
                            for t in t_coords:
                                data_reprj_temp = data_reprj_lvl[data_reprj_lvl[datetime_col[0]] == t]   
                                
                                rasterized_levels = rasterio.features.rasterize(
                                    [(val['geometry'], 1) for _, val in data_reprj_temp.iterrows()],
                                    out_shape = shape,
                                    transform = rio_kwargs['transform'],
                                    fill = 0, # np.nan
                                    merge_alg = rasterio.enums.MergeAlg.add,
                                    all_touched = False,
                                    # dtype = rasterio.float32,
                                    )
                                
                                data_3D.append(rasterized_levels)
                            
                            ds_reprj[f"{cat_var}_{l}"] = xr.DataArray(np.array(data_3D),
                                                                      coords = coords,
                                                                      dims = dims)
                            
                        # Normalize
                        all_level_sum = ds_reprj[f"{cat_var}_{levels[0]}"]
                        for i in range(1, len(levels)):
                            all_level_sum = all_level_sum + ds_reprj[f"{cat_var}_{levels[i]}"]
                        # all_level_sum = ds_reprj[[f"{cat_var}:{l}" for l in levels]].sum()
                        for l in levels:
                            ds_reprj[f"{cat_var}_{l}"] = ds_reprj[f"{cat_var}_{l}"] / all_level_sum * 100
                    
                ds_reprj = ds_reprj.sortby(datetime_col[0]) # reorder time-axis values

                
            else:
                if len(datetime_col) > 1:
                    print(f"Too many datetime columns: {datetime_col}. No time axis is inferred")
            
                for num_var in (set(numeric_col).union(set(timedelta_col))).intersection(set(var_list)):
                    rasterized_data = rasterio.features.rasterize(
                        [(val['geometry'], val[num_var]) for _, val in data_reprj.iterrows()],
                        out_shape = shape,
                        transform = rio_kwargs['transform'],
                        fill = 0, # np.nan
                        merge_alg = rasterio.enums.MergeAlg.add,
                        all_touched = False,
                        # dtype = rasterio.float64, # rasterio.float32,
                        )
                    
                    # Normalize if mode == 'mean' instead of 'sum'
                    if rasterize_mode[num_var] == "mean":
                        rasterized_weight = rasterio.features.rasterize(
                            [(val['geometry'], 1) for _, val in data_reprj.iterrows()],
                            out_shape = shape,
                            transform = rio_kwargs['transform'],
                            fill = 0, # np.nan
                            merge_alg = rasterio.enums.MergeAlg.add,
                            all_touched = False,
                            # dtype = rasterio.float64, # rasterio.float32,
                            )
                        
                        # Normalize
                        rasterized_data = rasterized_data / rasterized_weight
                        
                        # Replace inf with np.nan
                        np.nan_to_num(rasterized_data, posinf = np.nan)
                    
                    # Fill the dataset
                    ds_reprj[num_var] = xr.DataArray(rasterized_data,
                                                     coords = coords,
                                                     dims = dims)

                # Replace 0 with np.nan
# =============================================================================
#                 ds_reprj = ds_reprj.where(ds_reprj != 0)
# =============================================================================
                    
                # Categorical variables: level by level
                for cat_var in set(categorical_col).intersection(set(var_list)):
                    # Case 'dominant' (more frequent):
                    if rasterize_mode[cat_var] == "dominant":
                        levels = data_reprj[cat_var].unique()
                        # String/categorical data are not handled well by GIS softwares...
                        id_levels = {i:levels[i] for i in range(0, len(levels))}
                        for i in id_levels:
                            data_reprj_lvl = data_reprj[data_reprj[cat_var] == levels[i]] 
                            rasterized_levels = rasterio.features.rasterize(
                                [(val['geometry'], 1) for _, val in data_reprj_lvl.iterrows()],
                                out_shape = shape,
                                transform = rio_kwargs['transform'],
                                fill = 0, # np.nan
                                merge_alg = rasterio.enums.MergeAlg.add,
                                all_touched = False,
                                # dtype = rasterio.float32,
                                )
                            
                            if i == 0: # 1er passage
                                rasterized_data = rasterized_levels.copy().astype(int)
                                rasterized_data[:] = -1
                                rasterized_data[rasterized_levels > 0] = i
                                rasterized_levels_prev = rasterized_levels.copy()
                            else:
                                rasterized_data[rasterized_levels > rasterized_levels_prev] = i
                                rasterized_levels_prev = np.maximum(rasterized_levels,
                                                                    rasterized_levels_prev)
                        
                        ds_reprj[cat_var] = xr.DataArray(rasterized_data,
                                                         coords = coords,
                                                         dims = dims)
                        
                        # Inform
                        nodata_level = {-1: 'nodata'}
                        id_levels = {**nodata_level, **id_levels}
                        ds_reprj[f"{cat_var}_levels"] = ', '.join([f"{k}: {id_levels[k]}" for k in id_levels]) # str(id_levels)
                        ds_reprj[cat_var].attrs['levels'] = ', '.join([f"{k}: {id_levels[k]}" for k in id_levels])
# =============================================================================
#                         print(f"Info: Variable {cat_var} is categorized as follow:")
#                         print('\n'.join([f"  . {k}: {id_levels[k]}" for k in id_levels]))
# =============================================================================
                        
                        
                    # Case 'percent' (compute frequency among other levels):
                    elif rasterize_mode[cat_var] == "percent":
                        levels = data_reprj[cat_var].unique()
                        for l in levels:
                            data_reprj_lvl = data_reprj[data_reprj[cat_var] == l] 
                            rasterized_levels = rasterio.features.rasterize(
                                [(val['geometry'], 1) for _, val in data_reprj_lvl.iterrows()],
                                out_shape = shape,
                                transform = rio_kwargs['transform'],
                                fill = 0, # np.nan
                                merge_alg = rasterio.enums.MergeAlg.add,
                                all_touched = False,
                                # dtype = rasterio.float32,
                                )
                        
                            ds_reprj[f"{cat_var}_{l}"] = xr.DataArray(rasterized_levels,
                                                                      coords = coords,
                                                                      dims = dims)
                        
                        # Normalize
                        all_level_sum = ds_reprj[f"{cat_var}_{levels[0]}"]
                        for i in range(1, len(levels)):
                            all_level_sum = all_level_sum + ds_reprj[f"{cat_var}_{levels[i]}"]
                        # all_level_sum = ds_reprj[[f"{cat_var}:{l}" for l in levels]].sum()
                        for l in levels:
                            ds_reprj[f"{cat_var}_{l}"] = ds_reprj[f"{cat_var}_{l}"] / all_level_sum * 100
                        
            
                
# =============================================================================
#                 # convert levels to values
#                 ds_reprj['levels'] = levels
#                 ds_reprj[cat_var] = ds_reprj['levels'][ds_reprj[cat_var].astype(int)].drop('levels')
# =============================================================================
            
# =============================================================================
#                 # Replace 0 with np.nan
#                 ds_reprj = ds_reprj.where(ds_reprj != 0)
# =============================================================================
            
       
        else:
            ds_reprj = data_reprj
        
        # ds_reprj.rio.write_crs(rio_kwargs['dst_crs'], inplace = True)
        if isinstance(ds_reprj, (xr.Dataset, xr.DataArray)):
            ds_reprj = georef(data = ds_reprj, 
                              include_crs = True, 
                              crs = rio_kwargs['dst_crs'])

    return ds_reprj  


###############################################################################
#%%% * Clip
# =============================================================================
# def clip(data, mask, src_crs=None, dst_crs=None):
#     """
#     The difference between clipping with clip() and with reproject() is that
#     clip() keeps the same grid as input, whereas reproject() aligns on the 
#     passed x0 and y0 values (by default x0=0 and y0=0).
# 
#     Parameters
#     ----------
#     data : TYPE
#         DESCRIPTION.
#     mask : TYPE
#         DESCRIPTION.
#     src_crs : TYPE, optional
#         DESCRIPTION. The default is None.
#     dst_crs : TYPE, optional
#         DESCRIPTION. The default is None.
# 
#     Returns
#     -------
#     TYPE
#         DESCRIPTION.
# 
#     """
#     kwargs = {}
#     if dst_crs is not None:
#         kwargs['dst_crs'] = dst_crs
#     
#     x_res, y_res = data.rio.resolution()
#     x0 = data.x[0].item() + x_res/2
#     y0 = data.y[0].item() + y_res/2
#     
#     return reproject(data, src_crs = src_crs, mask = mask, 
#                      x0 = x0, y0 = y0, **kwargs)
# =============================================================================

###############################################################################
#%%% Align on the closest value
def nearest(x = None, y = None, x0 = 700012.5, y0 = 6600037.5, res = 75): 
    """
    
    
    Exemple
    -------
    import geoconvert as gc
    gc.nearest(x = 210054)
    gc.nearest(y = 6761020)
    
    Parameters
    ----------
    x : float, optional
        Valeur de la coordonnée x (ou longitude). The default is None.
    y : float, optional
        Valeur de la coordonnée y (ou latitude). The default is None.

    Returns
    -------
    Par défault, cette fonction retourne la plus proche valeur (de x ou de y) 
    alignée sur la grille des cartes topo IGN de la BD ALTI.
    Il est possible de changer les valeurs de x0, y0 et res pour aligner sur
    d'autres grilles.
    """
    
    # ---- Paramètres d'alignement : 
    # ---------------------------
# =============================================================================
#     # Documentation Lambert-93
#     print('\n--- Alignement d'après doc Lambert-93 ---\n')
#     x0 = 700000 # origine X
#     y0 = 6600000 # origine Y
#     res = 75 # résolution
# =============================================================================
    
    # Coordonnées des cartes IGN BD ALTI v2
    if (x0 == 700012.5 or y0 == 6600037.5) and res == 75:
        print('\n--- Alignement sur grille IGN BD ALTI v2 (defaut) ---')   
    
    closest = []

    if x is not None and y is None:
        # print('x le plus proche = ')
        if (x0-x)%res <= res/2:
            closest = x0 - (x0-x)//res*res
        elif (x0-x)%res > res/2:
            closest = x0 - ((x0-x)//res + 1)*res
    
    elif y is not None and x is None:
        # print('y le plus proche = ')
        if (y0-y)%res <= res/2:
            closest = y0 - (y0-y)//res*res
        elif (y0-y)%res > res/2:
            closest = y0 - ((y0-y)//res + 1)*res
    
    else:
        print('Err: only one of x or y parameter should be passed')
        return
        
    return closest


###############################################################################
#%%% Format x_res and y_res
def format_xy_resolution(*, resolution=None, bounds=None, shape=None):
    """
    Format x_res and y_res from a resolution value/tuple/list, or from 
    bounds and shape.

    Parameters
    ----------
    resolution : number | iterable, optional
       xy_res or (x_res, y_res). The default is None.
    bounds : iterable, optional
        (x_min, y_min, x_max, y_max). The default is None.
    shape : iterable, optional
        (height, width). The default is None.

    Returns
    -------
    x_res and y_res

    """
    if (resolution is not None) & ((bounds is not None) | (shape is not None)):
        print("Err: resolution cannot be specified alongside with bounds or shape")
        return
    
    if resolution is not None:
        if isinstance(resolution, (tuple, list)):
            x_res = abs(resolution[0])
            y_res = -abs(resolution[1])
        else:
            x_res = abs(resolution)
            y_res = -abs(resolution)
            
    if ((bounds is not None) & (shape is None)) | ((bounds is None) & (shape is not None)):
        print("Err: both bounds and shape need to be specified")
    
    if (bounds is not None) & (shape is not None):
        (height, width) = shape
        (x_min, y_min, x_max, y_max) = bounds
        x_res = (x_max - x_min) / width
        y_res = -(y_max - y_min) / height
        
    return x_res, y_res


###############################################################################
#%%% Get shape
def get_shape(x_res, y_res, bounds, x0=0, y0=0):
    # bounds should be xmin, ymin, xmax, ymax
    # aligne sur le 0, arrondit, et tutti quanti
    (x_min, y_min, x_max, y_max) = bounds
    
    x_min2 = nearest(x = x_min, res = x_res, x0 = x0)
    if x_min2 > x_min:
        x_min2 = x_min2 - x_res
        
    y_min2 = nearest(y = y_min, res = y_res, y0 = y0)
    if y_min2 > y_min:
        y_min2 = y_min2 - abs(y_res)
        
    x_max2 = nearest(x = x_max, res = x_res, x0 = x0)
    if x_max2 < x_max:
        x_max2 = x_max2 + x_res
        
    y_max2 = nearest(y = y_max, res = y_res, y0 = y0)
    if y_max2 < y_max:
        y_max2 = y_max2 + abs(y_res)
    
    
    width = (x_max2 - x_min2)/x_res
    height = -(y_max2 - y_min2)/y_res
    if (int(width) == width) & (int(height) == height):
        shape = (int(height), int(width))
    else:
        print(f"Warning: shape values are not integers: ({width}, {height})")
        rel_err = (abs((np.rint(width) - width)/np.rint(width)),
                   abs((np.rint(height) - height)/np.rint(height)))
        print(f".                               errors: ({rel_err[0]*100} %, {rel_err[1]*100} %)")
        # Safeguard
        if (rel_err[0] > 1e-8) | (rel_err[1] > 1e-8):
            print("Error")
            shape = None
        else:
            shape = (int(np.rint(height)), int(np.rint(width)))
    
    return shape, x_min2, y_max2

           
#%% COMPRESS & UNCOMPRESS
###############################################################################
def unzip(data):
    """
    In some cases, especially for loading in QGIS, it is much quicker to load
    uncompressed netcdf than compressed netcdf.
    This function only applies to non-destructive compression.

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Load
    data_ds = load_any(data, decode_times = True, decode_coords = 'all')
    # Get main variable
    var_list = main_var(data_ds)
    
    for var in var_list:
        # Deactivate zlib
        data_ds[var].encoding['zlib'] = False
        
    # Return
    return data_ds
    # Export
# =============================================================================
#     outpath = '_'.join([
#         os.path.splitext(data)[0], 
#         'unzip.nc',
#         ])
#     export(data_ds, outpath)
# =============================================================================
    

###############################################################################
def gzip(data, complevel = 3, shuffle = False):
    """
    Quick tool to apply lossless compression on a NetCDF file using gzip.
    
    examples
    --------
    gc.gzip(filepath_comp99.8, complevel = 4, shuffle = True)
    gc.gzip(filepath_drias2022like, complevel = 5)

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Load
    data_ds = load_any(data, decode_times = True, decode_coords = 'all')
    # Get main variable
    var_list = main_var(data_ds)
    
    for var in var_list:
        # Activate zlib
        data_ds[var].encoding['zlib'] = True
        data_ds[var].encoding['complevel'] = complevel
        data_ds[var].encoding['shuffle'] = shuffle
        data_ds[var].encoding['contiguous'] = False
        
    # Return
    return data_ds
    # Export
# =============================================================================
#     outpath = '_'.join([
#         os.path.splitext(data)[0], 
#         'gzip.nc',
#         ])
#     export(data_ds, outpath)
# =============================================================================
    
    
###############################################################################
def pack(data, nbits = 16):
    """

    
    examples
    --------

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    if (nbits != 16) & (nbits != 8):
        print("Err: nbits should be 8 or 16")
        return

    # Load
    data_ds = load_any(data, decode_times = True, decode_coords = 'all')
    # Get main variable
    var_list = main_var(data_ds)

    for var in var_list:
        # Compress
        bound_min = data_ds[var].min().item()
        bound_max = data_ds[var].max().item()
        # Add an increased max bound, that will be used for _FillValue
        bound_max = bound_max + (bound_max - bound_min + 1)/(2**nbits)
        scale_factor, add_offset = compute_scale_and_offset(
            bound_min, bound_max, nbits)
        data_ds[var].encoding['scale_factor'] = scale_factor
    
        data_ds[var].encoding['dtype'] = f'uint{nbits}'
        data_ds[var].encoding['_FillValue'] = (2**nbits)-1
        data_ds[var].encoding['add_offset'] = add_offset
        print("   Compression (lossy)")
        # Prevent _FillValue issues
        if ('missing_value' in data_ds[var].encoding) & ('_FillValue' in data_ds[var].encoding):
            data_ds[var].encoding.pop('missing_value')
        
    # Return
    return data_ds



#%%% Packing netcdf (previously packnetcdf.py)
"""
Created on Wed Aug 24 16:48:29 2022

@author: script based on James Hiebert's work (2015):
    http://james.hiebert.name/blog/work/2015/04/18/NetCDF-Scale-Factors.html

RAPPEL des dtypes :
    uint8 (unsigned int.)       0 to 255
    uint16 (unsigned int.)      0 to 65535
    uint32 (unsigned int.)      0 to 4294967295
    uint64 (unsigned int.)      0 to 18446744073709551615
    
    int8    (Bytes)             -128 to 127
    int16   (short integer)     -32768 to 32767
    int32   (integer)           -2147483648 to 2147483647
    int64   (integer)           -9223372036854775808 to 9223372036854775807 
    
    float16 (half precision float)      10 bits mantissa, 5 bits exponent (~ 4 cs ?)
    float32 (single precision float)    23 bits mantissa, 8 bits exponent (~ 8 cs ?)
    float64 (double precision float)    52 bits mantissa, 11 bits exponent (~ 16 cs ?)
"""

###############################################################################
def compute_scale_and_offset(min, max, n):
    """
    Computes scale and offset necessary to pack a float32 (or float64?) set 
    of values into a int16 or int8 set of values.
    
    Parameters
    ----------
    min : float
        Minimum value from the data
    max : float
        Maximum value from the data
    n : int
        Number of bits into which you wish to pack (8 or 16)

    Returns
    -------
    scale_factor : float
        Parameter for netCDF's encoding
    add_offset : float
        Parameter for netCDF's encoding
    """
    
    # stretch/compress data to the available packed range    
    add_offset = min
    scale_factor = (max - min) / ((2 ** n) - 1)
    
    return (scale_factor, add_offset)


###############################################################################
def pack_value(unpacked_value, scale_factor, add_offset):
    """
    Compute the packed value from the original value, a scale factor and an 
    offset.

    Parameters
    ----------
    unpacked_value : numeric
        Original value.
    scale_factor : numeric
        Scale factor, multiplied to the original value.
    add_offset : numeric
        Offset added to the original value.

    Returns
    -------
    numeric
        Packed value.

    """
    
    # print(f'math.floor: {math.floor((unpacked_value - add_offset) / scale_factor)}')
    return int((unpacked_value - add_offset) / scale_factor)


###############################################################################
def unpack_value(packed_value, scale_factor, add_offset):
    """
    Retrieve the original value from a packed value, a scale factor and an
    offset.

    Parameters
    ----------
    packed_value : numeric
        Value to unpack.
    scale_factor : numeric
        Scale factor that was multiplied to the original value to retrieve.
    add_offset : numeric
        Offset that was added to the original value to retrieve.

    Returns
    -------
    numeric
        Original unpacked value.

    """
    return packed_value * scale_factor + add_offset


#%% EXPORT
###############################################################################
def export(data, output_filepath, **kwargs):
    extension_dst = os.path.splitext(output_filepath)[-1]
    
    data_ds = load_any(data, decode_times = True, decode_coords = 'all')
    
    # Safeguards
    # These arguments are only used in pandas.DataFrame.to_csv():
    if extension_dst != '.csv':
        for arg in ['sep', 'encoding']: 
            if arg in kwargs: kwargs.pop(arg)
    # These arguments are only used in pandas.DataFrame.to_json():
    if (extension_dst != '.json') & isinstance(data_ds, pd.DataFrame):
        for arg in ['force_ascii']:
            if arg in kwargs: kwargs.pop(arg)
    
    if isinstance(data_ds, xr.DataArray):
        if 'name' in kwargs:
            name = kwargs['name']
        else:
            name = main_var(data_ds)[0]
        data_ds = data_ds.to_dataset(name = name)
            
    
    print("\nExporting...")
    
    if isinstance(data_ds, gpd.GeoDataFrame):
        if extension_dst in ['.shp', '.json', '.geojson', '.gpkg']:
            data_ds.to_file(output_filepath, **kwargs)
            print(f"   _ Success: The data has been exported to the file '{output_filepath}'")

        elif extension_dst in ['.nc', '.tif']:
            print("Err: To convert vector to raster, use geoconvert.reproject() instead")
            return
        
        elif extension_dst in ['.csv']:
            data_ds.drop(columns = 'geometry').to_csv(output_filepath, **kwargs)
            print(f"   _ Success: The data has been exported to the file '{output_filepath}'")
        
        else:
            print("Err: Extension is not supported")
            return
    
    elif isinstance(data_ds, xr.Dataset):
        if extension_dst == '.nc':
            data_ds.to_netcdf(output_filepath, **kwargs)
        
        elif extension_dst in ['.tif', '.asc']:
            data_ds.rio.to_raster(output_filepath, **kwargs) # recalc_transform = False
            
        else:
            print("Err: Extension is not supported")
            return
        
        print(f"   _ Success: The data has been exported to the file '{output_filepath}'")
    
    elif isinstance(data_ds, pd.DataFrame): # Note: it is important to test this
    # condition after gpd.GeoDataFrame because GeoDataFrames are also DataFrames
        if extension_dst in ['.json']:
            data_ds.to_json(output_filepath, **kwargs)
        
        elif extension_dst in ['.csv']:
            data_ds.to_csv(output_filepath, **kwargs)
        
        print(f"   _ Success: The data has been exported to the file '{output_filepath}'")
        
   

#%% OPERATIONS
###############################################################################
def hourly_to_daily(data, *, mode = 'sum'):
   
    # ---- Process data
    #% Load data:
    data_ds = load_any(data, decode_coords = 'all', decode_times = True)
    
    var_list = main_var(data_ds)
        
    mode_dict = {}
    if isinstance(mode, str):
        for var in var_list:
            mode_dict[var] = mode
            
    elif isinstance(mode, dict):
        mode_dict = mode
        if len(var_list) > len(mode_dict):
            diff = set(var_list).difference(mode_dict)
            print(f"   _ Warning: {len(diff)} variables were not specified in 'mode': {', '.join(diff)}. They will be assigned the mode 'sum'.")
            for d in diff:
                mode_dict[d] = 'sum'
    
    time_coord = main_time_dims(data_ds)
    
    datarsmpl = xr.Dataset()
    
    #% Resample:
    print("   _ Resampling time...")
    for var in var_list:
        if mode_dict[var] == 'mean':
            datarsmpl[var] = data_ds[var].resample({time_coord: '1D'}).mean(dim = time_coord,
                                                                            keep_attrs = True)
        elif mode_dict[var] == 'max':
            datarsmpl[var] = data_ds[var].resample({time_coord: '1D'}).max(dim = time_coord,
                                                                           keep_attrs = True)
        elif mode_dict[var] == 'min':
            datarsmpl[var] = data_ds[var].resample({time_coord: '1D'}).min(dim = time_coord,
                                                                           keep_attrs = True)
        elif mode_dict[var] == 'sum':
            datarsmpl[var] = data_ds[var].resample({time_coord: '1D'}).sum(dim = time_coord,
                                                                           skipna = False,
                                                                           keep_attrs = True)
        
        # ---- Preparing export   
        # Transfer encodings   
        datarsmpl[var].encoding = data_ds[var].encoding
            
        # Case of packing
        if ('scale_factor' in datarsmpl[var].encoding) | ('add_offset' in datarsmpl[var].encoding):
            # Packing (lossy compression) induces a loss of precision of 
            # apprx. 1/1000 of unit, for a quantity with an interval of 150 
            # units. The packing is initially used in some original ERA5-Land data.
            if mode == 'sum':
                print("   Correcting packing encodings...")
                datarsmpl[var].encoding['scale_factor'] = datarsmpl[var].encoding['scale_factor']*24
                datarsmpl[var].encoding['add_offset'] = datarsmpl[var].encoding['add_offset']*24

    # Transfert coord encoding
    for c in list(datarsmpl.coords):
        datarsmpl[c].encoding = data_ds[c].encoding
        datarsmpl[c].attrs = data_ds[c].attrs
    datarsmpl[time_coord].encoding['units'] = datarsmpl[time_coord].encoding['units'].replace('hours', 'days')
        
    return datarsmpl


###############################################################################
def to_instant(data, derivative = False):
    data_ds = load_any(data, decode_coords = 'all', decode_times = True)
    time_coord = main_time_dims(data_ds)
    if isinstance(time_coord, list):
        time_coord = time_coord[0]
    
    if derivative:
        inst_ds = data_ds.diff(dim = time_coord)/data_ds[time_coord].diff(dim = time_coord)
    else:
        inst_ds = data_ds.diff(dim = time_coord)
    
    return inst_ds
    

###############################################################################
def convert_unit(data, operation, *, var = None):
    
    metric_prefixes = ['p', None, None, 'n', None, None, 'µ', None, None, 
                       'm', 'c', 'd', '', 'da', 'h', 'k', None, None, 'M', 
                       None, None, 'G']
    
    # ---- Load data and operands
    data_ds = load_any(data)
    
    if not isinstance(operation, str):
        print("Err: 'operation' should be a str.")
        return
    else:
        operation = operation.replace(' ', '').replace('x', '*').replace('×', '*').replace('÷', '/')
        operand = operation[0]
        factor = float(operation[1:])
    
    
    if isinstance(data_ds, (pd.DataFrame, gpd.GeoDataFrame)):
        if var is None:
            mvar = main_var(data_ds)
        else:
            mvar = var
        
        # ---- Operation        
        if operand == '*':
            data_ds[mvar] = data_ds[mvar] * factor
        elif operand == '/':
            data_ds[mvar] = data_ds[mvar] / factor
        elif operand == '+':
            data_ds[mvar] = data_ds[mvar] + factor
        elif operand == '-':
            data_ds[mvar] = data_ds[mvar] - factor
        
        return data_ds  
        
    
    elif isinstance(data_ds, xr.Dataset):
        mvar = main_var(data_ds)
        if len(mvar) == 1:
            data_da = data_ds[mvar[0]]
        else: # mvar is a list
            if var is not None:
                data_da = data_ds[var]
            else:
                print("Err: convert_unit can only be used on xarray.DataArrays or xarray.Datasets with one variable. Consider passing the argument 'var'.")
                return
    elif isinstance(data_ds, xr.DataArray):
        data_da = data_ds
  
    # ---- Preparing export
    attrs = data_da.attrs
    encod = data_da.encoding
    
    # ---- Operation        
    # exec(f"data_da = data_da {operation}") # vulnerability issues
    if operand == '*':
        data_da = data_da * factor
    elif operand == '/':
        data_da = data_da / factor
    elif operand == '+':
        data_da = data_da + factor
    elif operand == '-':
        data_da = data_da - factor
    
    # ---- Transfert metadata
    data_da.encoding = encod
    data_da.attrs = attrs # normally unnecessary
    for unit_id in ['unit', 'units']:
        if unit_id in data_da.attrs:
            if operand in ['*', '/']:                
                significand, exponent = f"{factor:e}".split('e')
                significand = float(significand)
                exponent = int(exponent)
                # if factor_generic%10 == 0:
                if significand == 1:
                    current_prefix = data_da.attrs[unit_id][0]
                    current_idx = metric_prefixes.index(current_prefix)
                    # new_idx = current_idx + int(np.log10(factor_generic))
                    if operand == "*":
                        new_idx = current_idx - exponent
                        new_unit = data_da.attrs[unit_id] + f" {operand}{significand}e{exponent}" # By default
                    elif operand == "/":
                        new_idx = current_idx + exponent
                        new_unit = data_da.attrs[unit_id] + f" *{significand}e{-exponent}" # By default
                        
                    if (new_idx >= 0) & (new_idx <= len(metric_prefixes)):
                        if metric_prefixes[new_idx] is not None:
                            new_unit = metric_prefixes[new_idx] + data_da.attrs[unit_id][1:]
                    
                    data_da.attrs[unit_id] = new_unit
                
                else:
                    new_unit = data_da.attrs[unit_id] + f" {operand}{significand}e{exponent}" # By default
                    data_da.attrs[unit_id] = new_unit
                

    # Case of packing
    if ('scale_factor' in data_da.encoding) | ('add_offset' in data_da.encoding):
        # Packing (lossy compression) induces a loss of precision of 
        # apprx. 1/1000 of unit, for a quantity with an interval of 150 
        # units. The packing is initially used in some original ERA5-Land data.
        if operand == '+':
            data_da.encoding['add_offset'] = data_da.encoding['add_offset'] + factor
        elif operand == '-':
            data_da.encoding['add_offset'] = data_da.encoding['add_offset'] - factor
        elif operand == '*':
            data_da.encoding['add_offset'] = data_da.encoding['add_offset'] * factor
            data_da.encoding['scale_factor'] = data_da.encoding['scale_factor'] * factor
        elif operand == '/':
            data_da.encoding['add_offset'] = data_da.encoding['add_offset'] / factor
            data_da.encoding['scale_factor'] = data_da.encoding['scale_factor'] / factor
    
    if isinstance(data_ds, xr.Dataset):
        if len(mvar) == 1:
            data_ds[mvar[0]] = data_da
        else: # mvar is a list
            if var is not None:
                data_ds[var] = data_da
            else:
                print("Err: convert_unit can only be used on xarray.DataArrays or xarray.Datasets with one variable. Consider passing the argument 'var'.")
                return
    elif isinstance(data_ds, xr.DataArray):
        data_ds = data_da

    return data_ds    



###############################################################################
#%%% * hourly_to_daily (OLD)
def hourly_to_daily_old(*, data, mode = 'mean', **kwargs):
    # Cette version précédente (mise à jour) gère des dossiers
    
    """
    Example
    -------
    import geoconvert as gc
    # full example:
    gc.hourly_to_daily(input_file = r"D:/2011-2021_hourly Temperature.nc",
                       mode = 'max',
                       output_path = r"D:/2011-2021_daily Temperature Max.nc",
                       fields = ['t2m', 'tp'])
    
    # input_file can also be a folder:
    gc.hourly_to_daily(input_file = r"D:\2- Postdoc\2- Travaux\1- Veille\4- Donnees\8- Meteo\ERA5\Brittany\test", 
                       mode = 'mean')
    
    Parameters
    ----------
    input_file : str, or list of str
        Can be a path to a file (or a list of paths), or a path to a folder, 
        in which cas all the files in this folder will be processed.
    mode : str, or list of str, optional
        = 'mean' (default) | 'max' | 'min' | 'sum'
    **kwargs 
    --------
    fields : str or list of str, optional
        e.g: ['t2m', 'tp', 'u10', 'v10', ...]
        (if not specified, all fields are considered)
    output_path : str, optional
        e.g: [r"D:/2011-2021_daily Temperature Max.nc"]
        (if not specified, output_name is made up according to arguments)
        
    Returns
    -------
    None. Processed files are created in the output destination folder.

    """

    # ---- Get input file path(s)
    data_folder, filelist = get_filelist(data, extension = '.nc')
        
    #% Safeguard for output_names:
    if len(filelist) > 1 and 'output_path' in kwargs:
        print('Warning: Due to multiple output, names of the output files are imposed.') 
    
    
    # ---- Format modes
    if isinstance(mode, str): mode = [mode]
    else: mode = list(mode)
    
    if len(mode) != len(filelist):
        if (len(mode) == 1) & (len(filelist)>1):
            mode = mode*len(filelist)
        else:
            print("Error: lengths of input file and mode lists do not match")
            return
            
        
    # ---- Process data
    for i, f in enumerate(filelist):  
        print(f"\n\nProcessing file {i+1}/{len(filelist)}: {f}...")
        print("-------------------")
        #% Load data:
        data_ds = load_any(os.path.join(data_folder, f), 
                           decode_coords = 'all', decode_times = True)

        #% Get fields:
        if 'fields' in kwargs:
            fields = kwargs['fields']
            if isinstance(fields, str): fields = [fields]
            else: fields = list(fields) # in case fields are string or tuple
        else:
            fields = list(data_ds.data_vars) # if not input_arg, fields = all
        
        #% Extract subset according to fields
        fields_intersect = list(set(fields) & set(data_ds.data_vars))
        data_subset = data_ds[fields_intersect]
        print("   _ Extracted fields are {}".format(fields_intersect))
        if fields_intersect != fields:
            print('Warning: ' + ', '.join(set(fields) ^ set(fields_intersect)) 
                  + ' absent from ' + data)
        
        #% Resample:
        print("   _ Resampling time...")
        if mode[i] == 'mean':
            datarsmpl = data_subset.resample(time = '1D').mean(dim = 'time',
                                                                keep_attrs = True)
        elif mode[i] == 'max':
            datarsmpl = data_subset.resample(time = '1D').max(dim = 'time',
                                                               keep_attrs = True)
        elif mode[i] == 'min':
            datarsmpl = data_subset.resample(time = '1D').min(dim = 'time',
                                                               keep_attrs = True)
        elif mode[i] == 'sum':
            datarsmpl = data_subset.resample(time = '1D').sum(dim = 'time',
                                                               skipna = False,
                                                               keep_attrs = True)
        
        #% Build output name(s):
        if len(filelist) > 1 or not 'output_path' in kwargs:         
            basename = os.path.splitext(f)[0]
            output_name = os.path.join(
                data_folder, 'daily',
                basename + ' daily_' + mode[i] + '.nc')
            ## Regex solution, instead of splitext:
            # _motif = re.compile('.+[^\w]')
            # _basename = _motif.search(data).group()[0:-1]
            
            if not os.path.isdir(os.path.join(data_folder, 'daily')):
                os.mkdir(os.path.join(data_folder, 'daily'))
            
        else:
            output_name = kwargs['output_path']
        
        
        # ---- Preparing export   
        # Transfer encodings
        for c in list(datarsmpl.coords):
            datarsmpl[c].encoding = data_ds[c].encoding
        
        for f in fields_intersect:
            datarsmpl[f].encoding = data_ds[f].encoding
            
            # Case of packing
            if ('scale_factor' in datarsmpl[f].encoding) | ('add_offset' in datarsmpl[f].encoding):
                # Packing (lossy compression) induces a loss of precision of 
                # apprx. 1/1000 of unit, for a quantity with an interval of 150 
                # units. The packing is initially used in some original ERA5-Land data.
                if mode[i] == 'sum':
                    print("   Correcting packing encodings...")
                    datarsmpl[f].encoding['scale_factor'] = datarsmpl[f].encoding['scale_factor']*24
                    datarsmpl[f].encoding['add_offset'] = datarsmpl[f].encoding['add_offset']*24
            
        #% Export
        export(datarsmpl, output_name)


def dummy_input(base, value):
    """
    Creates a dummy space-time map with the same properties as the base, but with
    a dummy value.

    Parameters
    ----------
    base : TYPE
        DESCRIPTION.
    value : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    data_ds = load_any(base)
    var_list = main_var(data_ds)
    
    for var in var_list:
        data_ds[var] = data_ds[var]*0 + value
        
    return data_ds


#%% EXTRACTIONS
###############################################################################
#%%% ° times_series
def time_series(*, input_file, epsg_coords = None, epsg_data = None, 
                coords = None, mode = 'mean', dates = None, 
                fields = None, cumul = False):
    """
    % DESCRIPTION:
    This function extracts the temporal data in one location given by 
    coordinate.
    
    % EXAMPLE:
    import geoconvert as gc
    era5 = gc.time_series(input_file = r"D:\2- Postdoc\2- Travaux\1- Veille\4- Donnees\8- Meteo\ERA5\Brittany\daily/2011-2021_Temperature_daily_mean.nc", 
                          coords = (-2.199337, 48.17824), epsg = 4326, 
                          fields = 't2m')
    cwatm_ds = gc.time_series(input_file = r"D:\2- Postdoc\2- Travaux\3_CWatM_EBR\results\raw_results\005_calib_groundwater\01_base_Ronan\sum_gwRecharge_daily.nc", 
                          coords = (3417964, 2858067), epsg = 3035)

    % OPTIONAL ARGUMENTS:
        > coords = coordinates of one point
            /!\ Coordinates should be indicated in (X,Y) or (lon,lat) order 
            (and not (lat,lon) !!!)
        > coords can also indicate a mask: 
            coords = 'all' | filepath to a mask.tiff | filepath to a mask.shp
        > epsg_coords = 4326 | 3035 | 2154 | 27572 | etc.
            EPSG of the coords ! Useless if coords is a mask that includes a CRS 
        > epsg_data = same principle, for data without any included information about CRS
        > mode = 'mean' (standard) | 'sum' | 'max' | 'min'
    > dates = ['2021-09', '2021-12-01' ...]
    > fields = ['T2M', 'PRECIP', ...]
    """  
    _dataset = load_any(input_file, decode_times = True, decode_coords = 'all')
    
    #% Get and process arguments:
    # ---------------------------
    if epsg_coords is not None:
        if isinstance(epsg_coords, str):
            if epsg_coords.casefold()[0:5] == 'epsg:':
                epsg_coords = int(epsg_coords[5:])
                
    if fields is not None:
        if isinstance(fields, str): fields = [fields]
        else: fields = list(fields) # in case fields are string or tuple
    else:
        fields = list(_dataset.data_vars) # if not input_arg, fields = all
    
    if dates is not None:
        if not isinstance(dates, tuple): fields = tuple(fields)
        # in case dates are a list instead of a tuple
        
    if not isinstance(coords, str): 
    # if coords is not None:
        if not isinstance(coords, tuple): coords = tuple(coords)
        # in case coords are a list instead of a tuple
    
    
    #% Standardize terms:
    # -------------------
# =============================================================================
#     if 'lon' in list(_dataset.dims) or 'lat' in list(_dataset.dims):
#         print('Renaming lat/lon coordinates')
#         _dataset = _dataset.rename(lat = 'latitude', lon = 'longitude')
# =============================================================================
    if 'lon' in list(_dataset.dims) or 'lat' in list(_dataset.dims):
        print('Renaming lat/lon coordinates')
        _dataset = _dataset.rename(lat = 'y', lon = 'x')
    if 'longitude' in list(_dataset.dims) or 'latitude' in list(_dataset.dims):
        print('Renaming lat/lon coordinates')
        _dataset = _dataset.rename(latitude = 'y', longitude = 'x')
    if 'X' in list(_dataset.dims) or 'Y' in list(_dataset.dims):
        print('Renaming X/Y coordinates')
        _dataset = _dataset.rename(X = 'x', Y = 'y')
        
    _dataset.x.attrs = {'standard_name': 'projection_x_coordinate',
                                'long_name': 'x coordinate of projection',
                                'units': 'Meter'}
    _dataset.y.attrs = {'standard_name': 'projection_y_coordinate',
                                'long_name': 'y coordinate of projection',
                                'units': 'Meter'}
        
# =============================================================================
#     #% Convert temperature:
#     for _field in fields:
#         if 'units' in _dataset[_field].attrs:
#             if _dataset[_field].units == 'K':
#                 _dataset[_field] = _dataset[_field]-273.15
#                 # _datasubset[_field].units = '°C'
# =============================================================================
    
    print('Fields = {}'.format(str(fields)))
        
    
    if not isinstance(coords, str):
        if epsg_coords is not None:
            0
            # print('Coordinates = {} in epsg:{}'.format(str(coords), str(epsg_coords)))
        else:
            print('For numerical coords, it is necessary to indicate their CRS, by using the *epsg_coords* argument.')
            return
            
        #% Convert into appropriate CRS = CRS from the data:
        if epsg_data is not None:
            # 1re méthode de conversion : (x,y) ou (lon,lat) :
            coords_conv = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(epsg_coords), 
                                                  rasterio.crs.CRS.from_epsg(epsg_data), 
                                                  [coords[0]], [coords[1]])
            coords_conv = (coords_conv[0][0], coords_conv[1][0])
            # (pour convertir une tuple de arrays en tuple)
            
# =============================================================================
#             # 2e méthode de conversion : (x,y) ou (lat,lon) :
#             coords_conv = convert_coord(coords[0], coords[1], 
#                                         inputEPSG = epsg_coords, 
#                                         outputEPSG = epsg_data)
# =============================================================================
            print('Coordinates = {} in epsg:{}'.format(str(coords_conv), 
                                                       str(epsg_data)))
            
        elif 'spatial_ref' in _dataset.coords or 'spatial_ref' in _dataset.data_vars:
            # _motif = re.compile('"EPSG","\d+"')
            # _substr = _motif.findall(_dataset.spatial_ref.crs_wkt)[-1]
            # _epsg_motif = re.compile('\d+')
            # epsg_data = int(_epsg_motif.search(_substr).group())
            epsg_data = int(_dataset.rio.crs.to_epsg())
            
            coords_conv = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(epsg_coords), 
                                                  rasterio.crs.CRS.from_epsg(epsg_data), 
                                                  [coords[0]], [coords[1]])
            coords_conv = (coords_conv[0][0], coords_conv[1][0])

            print('Coordinates = {} in epsg:{}'.format(str(coords_conv), 
                                                       str(epsg_data)))
            
        else:
            print("'spatial_ref' is not indicated in the data file, and the argument *epsg_data* is not used. Be sure to use the same CRS as in the data.")
            coords_conv = coords
        
        #% Extract data:
        _dataset = _dataset[fields]
        if dates is not None:
            _dataset = _dataset.sel(time = slice(dates[0], dates[1]))
            
        if 'longitude' in list(_dataset.dims) or 'latitude' in list(_dataset.dims):
            results = _dataset.sel(longitude = coords_conv[0], 
                                   latitude = coords_conv[1],
                                   method = 'nearest')
        elif 'x' in list(_dataset.dims) or 'y' in list(_dataset.dims):
            results = _dataset.sel(x = coords_conv[0], 
                                   y = coords_conv[1],
                                   method = 'nearest')
        
        del _dataset # memory cleaning

                 
    else: # elif isinstance(coords, str): 
    # Dans ce cas, 'coords' indique un masque
        if coords.casefold() == 'all':
            print('All cells are considered')
                 
        else: # coords is a file_path
            #% Get CRS from the data:
            if 'spatial_ref' in _dataset.coords or 'spatial_ref' in _dataset.data_vars:
                # _motif = re.compile('"EPSG","\d+"')
                # _substr = _motif.findall(_dataset.spatial_ref.crs_wkt)[-1]
                # _epsg_motif = re.compile('\d+')
                # epsg_data = int(_epsg_motif.search(_substr).group())
                epsg_data = int(_dataset.rio.crs.to_epsg())
            elif epsg_data is None:
                print('Data file has no associated CRS.')
                return
            
            _mask_extension = os.path.splitext(coords)[-1]
            
            if _mask_extension in ['.tif', '.tiff', '.nc']: # If the mask is a geotiff or a netcdf
                if _mask_extension in ['.tif', '.tiff']:
                    with xr.open_dataset(coords) as mask_ds:
                        mask_ds.load()
                        mask_ds = mask_ds.squeeze('band').drop('band')
                        # NB: mask_ds.y.values are decreasing
                elif  _mask_extension in ['.nc']:
                    with xr.open_dataset(coords, decode_coords = 'all') as mask_ds:
                        mask_ds.load()
                        mask_ds = mask_ds.rename({list(mask_ds.data_vars)[0]: 'band_data'})

                if 'spatial_ref' in mask_ds.coords or 'spatial_ref' in mask_ds.data_vars:
                    # _motif = re.compile('"EPSG","\d+"')
                    # _substr = _motif.findall(mask_ds.spatial_ref.crs_wkt)[-1]
                    # _epsg_motif = re.compile('\d+')
                    # epsg_coords = int(_epsg_motif.search(_substr).group())
                    epsg_coords = int(mask_ds.rio.crs.to_epsg())
                else:
                    if epsg_coords is not None:
                        mask_ds.rio.write_crs('epsg:' + str(epsg_coords), inplace = True)
                        print('For clipping/masking, epsg:' + str(epsg_coords) + ' will be used.')
                    else:
                        print('For clipping/masking, mask needs to have a CRS associated.')
                        return
                    
                
                # Reprojection of the mask in the CRS of the data:
                res_x = float(_dataset.x[1] - _dataset.x[0])
                res_y = float(_dataset.y[1] - _dataset.y[0])
                
                # mask_ds['x'] = np.sort(mask_ds.x)
                # mask_ds['y'] = np.sort(mask_ds.y)
                
                mask_coords_conv = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(epsg_coords), 
                                                      rasterio.crs.CRS.from_epsg(epsg_data), 
                                                      [mask_ds.x.values.min()], [mask_ds.y.values.max()])
                
                idx_x = (np.abs(_dataset.x.values - mask_coords_conv[0][0])).argmin()
                # if idx_x > 0: idx_x = idx_x - 1
                x_min = float(_dataset.x[idx_x]) - res_x/2
                
                idx_y = (np.abs(_dataset.y.values - mask_coords_conv[1][0])).argmin()
                # if idx_y > 0: idx_y = idx_y - 1
                y_max = float(_dataset.y[idx_y]) + res_y/2
                
                mask_proj = mask_ds.rio.reproject('epsg:' + str(epsg_data),
                                                  transform = Affine(res_x, 0.0, x_min,  
                                                                      0.0, -res_y, y_max),
                                                  resampling = rasterio.enums.Resampling(5))
                
                _dataset = _dataset.where(mask_proj.band_data == 1, drop = True)
                _dataset.rio.write_crs("epsg:"+str(epsg_data), inplace = True)
                
            elif _mask_extension in ['.shp']: # If the mask is a shapefile
                mask_df = gpd.read_file(coords)
                
                if epsg_coords is not None:
                    mask_df.set_crs('epsg:' + str(epsg_coords), inplace = True, allow_override = True)
                else:
                    try: 
                        epsg_coords = mask_df.crs.to_epsg()
                    except AttributeError:
                        print('For clipping/masking, mask needs to have a CRS associated.')
                        return
                
                print('For clipping/masking, epsg:' + str(epsg_coords) + ' will be used.')
            
                _dataset = _dataset.rio.clip(mask_df.geometry.apply(mapping),
                                             mask_df.crs,
                                             all_touched = True)
        
            print('Data CRS is {}. Mask CRS is {}.'.format(epsg_data, epsg_coords))
        
        #% Extract data:
        if mode == 'mean':
            # results = _dataset.mean(dim = list(_dataset.dims)[-2:], 
            #                         skipna = True, keep_attrs = True)
            results = _dataset.mean(dim = ['x', 'y'], 
                                    skipna = True, keep_attrs = True)
        elif mode == 'sum':
            results = _dataset.sum(dim = ['x', 'y'], 
                                   skipna = True, keep_attrs = True)
        elif mode == 'max':
            results = _dataset.max(dim = ['x', 'y'], 
                                   skipna = True, keep_attrs = True)
        elif mode == 'min':
            results = _dataset.min(dim = ['x', 'y'], 
                                   skipna = True, keep_attrs = True)
            
        # memory cleaning
        del _dataset 
        gc.collect()
        
        
    if cumul:
        print('\ncumul == True')
        timespan = results['time'
            ].diff(
                dim = 'time', label = 'lower')/np.timedelta64(1, 'D')
        
        _var = main_var(results)
        results[_var][dict(time = slice(0, timespan.size))
                       ] = (results[_var][dict(time = slice(0, timespan.size))
                                           ] * timespan.values).cumsum(axis = 0)

        # Last value:
        results[_var][-1] = np.nan
                
    # Drop spatial_ref
    if 'spatial_ref' in results.coords or 'spatial_ref' in results.data_vars:
        results = results.drop('spatial_ref')
    
    # Convert to pandas.dataframe
    results = results.to_dataframe()
    
    return results


###############################################################################
#%%% * xr.DataSet to DataFrame
def xr_to_pd(xr_data):
    """
    Format xr objects (such as those from gc.time_series) into pandas.DataFrames
    formatted as in gc.tss_to_dataframe.

    Parameters
    ----------
    xr_data : xarray.DataSet or xarray.DataArary
        Initial data to convert into pandas.DataFrame
        NB: xr_data needs to have only one dimension.

    Returns
    -------
    Pandas.DataFrame

    """
    print("\n_Infos...")
    
    if type(xr_data) == xr.core.dataset.Dataset:
        var_list = main_var(xr_data)
        print(f"    Data is a xr.Dataset, with {', '.join(var_list)} as the main variables")
        xr_data = xr_data[var_list]
    elif type(xr_data) == xr.core.dataarray.DataArray:
        print("    Data is a xr.Dataarray")
    
    res = xr_data.to_dataframe(name = 'val')
    res = res[['val']]
    res['time'] = pd.to_datetime(res.index)
    if not res.time.dt.tz:
        print("    The timezone is not defined")
        # res['time'] = res.time.dt.tz_localize('UTC')
    res.index = range(0, res.shape[0])
# =============================================================================
#     res['id'] = res.index
# =============================================================================
    
    print('') # newline
    return res
    

###############################################################################
#%%% ° tss_to_dataframe
def tss_to_dataframe(*, input_file, skip_rows, start_date, cumul = False):
    """
    Example
    -------
    base = gc.tss_to_dataframe(input_file = r"D:\2- Postdoc\2- Travaux\3_CWatM_EBR\results\raw_results\001_prelim_cotech\2022-03-19_base\discharge_daily.tss",
                         skip_rows = 4,
                         start_date = '1991-08-01')
    
    precip = gc.tss_to_dataframe(input_file = r"D:\2- Postdoc\2- Travaux\3_CWatM_EBR\results\raw_results\003_artif\2022-03-25_base\Precipitation_daily.tss",
                         skip_rows = 4,
                         start_date = '2000-01-01')
    precip.val = precip.val*534000000/86400
    # (le BV topographique du Meu fait 471 851 238 m2)
    precip['rolling_mean'] = precip['val'].rolling(10).mean()
    
    Parameters
    ----------
    input_file : str
        Chemin d'accès au fichier d'entrée
    skip_rows : int
        Nombre de lignes à enlever en tête de fichier. /!\ ce nombre n'est '
    start_date : str ou datetime
        Date de la 1re valeur du fichier
        /!\ Si str, il faut qu'elle soit au format "%Y-%m-%d"

    Returns
    -------
    df : pandas.DataFrame

    
    Implémentations futures
    -----------------------
    Récupérer la start_date à partir du fichier de settings indiqué au début
    du fichier *.tss., et regarder ensuite le SpinUp
    """
    
    #%% Récupération des inputs :
    # ---------------------------
    if start_date == 'std':
        print('> Pas encore implémenté...')
        # récupérer la start_date du fichier de settings
    else:
        start_date = pd.to_datetime(start_date)
    # print('> start_date = ' + str(start_date))
    
    
    #%% Création des dataframes :
    # ---------------------------
    # df = pd.read_csv(input_file, sep = r"\s+", header = 0, names = ['id', 'val'], skiprows = skip_rows)
    if skip_rows == 0: # Cas des fichiers de débits *.css, sans lignes d'info,
                       # avec seulement un header
        _fields = ['']
        n_col = 1
        
    else: # Cas des outputs *.tss avec plusieurs lignes d'info, la 2e ligne 
          # indiquant le nombre de colonnes. Dans ce cas, skip_rows doit être
          # égal à 2.
        with open(input_file) as temp_file:
            # temp_file.readline()
            # n_col = int(temp_file.readline()[0])
            content = temp_file.readlines()
            n_col = int(content[skip_rows-1][0])
        _fields = [str(n) for n in range(1, n_col)]
        _fields[0] = ''
        
    df = pd.read_csv(input_file, 
                     sep = r"\s+", 
                     header = 0, 
                     skiprows = skip_rows -1 + n_col, 
                     names = ['id'] +  ['val' + ending for ending in _fields],
                     )
    
    # Si la colonne id contient déjà des dates (au format texte ou datetime) :
    if type(df.id[0]) in [str, 
                          pd.core.indexes.datetimes.DatetimeIndex,
                          pd._libs.tslibs.timestamps.Timestamp]:
        df['time'] = pd.to_datetime(df.id)
    # Sinon (= si la colonne id contient des indices), il faut reconstruire les dates :
    else:
        date_indexes = pd.date_range(start = start_date, 
                                     periods = df.shape[0], freq = '1D')
        df['time'] = date_indexes
    
    if cumul:
        print('\ncumul == True')
        # Values are expected to be expressed in [.../d]
        # Cumsum is applied on all columns with values ('val', 'val2', 'val3', ...)
        
        timespan = df.loc[
            :, df.columns == 'time'
            ].diff().shift(-1, fill_value = 0)/np.timedelta64(1, 'D')
        
        # timespan = df.loc[
        #     :, df.columns == 'time'
        #     ].diff()/np.timedelta64(1, 'D')
        
        df.iloc[
            :].loc[:, (df.columns != 'id') * (df.columns != 'time')
            ] = (df.iloc[
                :].loc[:, (df.columns != 'id') * (df.columns != 'time')
                ] * timespan.values).cumsum(axis = 0)
        
        # Last value
        # df.iloc[-1].loc[:, (df.columns != 'id') * (df.columns != 'time')] = np.nan
        
                # np.diff(df.time)/np.timedelta64(1, 'D')
    return df


#%% MNT & WATERSHEDS OPERATIONS
###############################################################################
def extract_watershed(*, ldd, 
                      outlet, 
                      dirmap = '1-9',
                      engine:str = 'pysheds', 
                      src_crs = None,
                      drop = False):
    """
    

    Parameters
    ----------
    ldd : TYPE
        DESCRIPTION.
    outlets : TYPE
        DESCRIPTION.
    engine : TYPE
        DESCRIPTION.
    drop : bool, default False
        If True, only coordinate labels where the mask is are kept
        (coordinate labels outside from the mask are dropped from the result).

    Returns
    -------
    None.

    """
    
    # ---- Specify directional mapping
    if isinstance(dirmap, str):
        dirmap = dirmap.casefold().replace(' ', '').replace('-', '')
        if dirmap in ['19', '[19]', 'keypad', 'pcraster']:
            dirmap = (8, 9, 6, 3, 2, 1, 4, 7)       # pcraster system
        elif dirmap in ['d8', 'esri']:
            dirmap = (64, 128, 1, 2, 4, 8, 16, 32)  # ESRI system
        elif dirmap in ['d8wbt', 'wbt', 'whiteboxtools']:
            dirmap = (128, 1, 2, 4, 8, 16, 32, 64)  # WhiteBox Tools system
    
    # ---- Loading
    ds = load_any(ldd, decode_coords = 'all') # mask_and_scale = False
    if src_crs is not None:
        ds.rio.write_crs(src_crs, inplace = True)
    else:
        if ds.rio.crs is None:
            print("Err: The Coordinate Reference System is required. It should be embedded in the input DEM or passed with the 'src_crs' argument")
            return
    ds, nodata = standard_fill_value(data_ds = ds)

    var = main_var(ds)[0]
    print(f"Drain direction variable is inferred to be {var}")
    x_var, y_var = main_space_dims(ds)
    encod = ds[var].encoding
    
    # Replacing nan with appropriate nodata value  
    std_nodata = min(dirmap) - 4
    if np.isnan(nodata):
        print(f"Warning: The nodata value {nodata} is not a number and is then corrected to {std_nodata} (int32)")
        nodata = std_nodata
    else:
        if (not np.int32(nodata) == nodata):
            print(f"Warning: The nodata value {nodata} dtype is wrong and is then corrected to {std_nodata} (int32)")
            nodata = std_nodata
        else:
            if nodata in dirmap:
                print(f"Warning: The nodata value {nodata} is part of dirmap and is then corrected to {std_nodata} (int32)")
                nodata = std_nodata
            else:
                nodata = np.int32(nodata)
    ds[var] = ds[var].fillna(nodata)
    
    viewfinder = ViewFinder(affine = ds.rio.transform(), 
                            shape = ds.rio.shape, 
                            crs = ds.rio.crs, 
                            nodata = np.int32(nodata))
    
    ldd = Raster(ds[var].astype(np.int32).data, viewfinder=viewfinder)
    grid = Grid.from_raster(ldd)
    
    # ---- With pysheds
    if engine.casefold() in ["pyshed", "pysheds"]:
        print('Pysheds engine...')
        
        # Compute accumulation
        acc = grid.accumulation(ldd, dirmap = dirmap, nodata_out = np.int32(-1))
        # Snap pour point to high accumulation cell (drained area > 1km²)
# ======== not working as desired (snaps to nearest corner) ===================
#         x_snap, y_snap = grid.snap_to_mask(
#             # acc > (1000 ** 2) / abs(ds.rio.resolution()[0] * ds.rio.resolution()[1]), 
#             acc > 15,
#             (outlet[0], outlet[1]), 
#             nodata_out = np.bool(False),
#             snap = "center",
#             )
#         
#         # Center snapped coords
#         x_snap += math.copysign(abs(ds.rio.resolution()[0]/2), outlet[0]-x_snap)
#         y_snap += math.copysign(abs(ds.rio.resolution()[1]/2), outlet[1]-y_snap)
#         
#         print(f"   . snap: {outlet[0]} -> {x_snap}  |  {outlet[1]} -> {y_snap}}}")
# =============================================================================
        
        col, row = grid.nearest_cell(outlet[0], outlet[1], snap = 'center')
        # if acc[row, col] < (1000 ** 2) / abs(ds.rio.resolution()[0] * ds.rio.resolution()[1]):
        if acc[row, col] < 15:
            print("   _ Warning: outlet seems to be out from mainstream")
        
            x_snap, y_snap = grid.snap_to_mask(
                # acc > (1000 ** 2) / abs(ds.rio.resolution()[0] * ds.rio.resolution()[1]), 
                acc > 15,
                (outlet[0], outlet[1]), 
                # nodata_out = np.bool(False),
                # snap = "center",
                # xytype='coordinate',
                )
            x_snap += ds.rio.resolution()[0]/2
            y_snap += ds.rio.resolution()[-1]/2
            
            print(f"      . consider trying: {x_snap}, {y_snap}")

        shed = grid.catchment(x = outlet[0], y = outlet[1], 
                              fdir = ldd, xytype='coordinate', 
                              nodata_out = np.bool(False),
                              dirmap = dirmap,
                              snap = 'center')
        
        # Output
        ds[var] = ([y_var, x_var], np.array(shed))
        ds = ds.rename({var: 'mask'})
        ds['mask'] = ds['mask'].astype(np.int8)
        ds['mask'].encoding = encod
        ds['mask'].encoding['dtype'] = np.int8
        ds['mask'].encoding['rasterio_dtype'] = np.int8
        ds['mask'].encoding['_FillValue'] = 0

        ds = georef(data = ds)
        
        if drop:
            ds = ds.where(ds.mask > 0, drop = True)
        
        
    # ---- Avec WhiteToolBox
# ======== discontinued =======================================================
#     elif engine.casefold() in ["wtb", "whitetoolbox"]:
#         print('WhiteToolBox engine...')
#     
#     wbt.watershed(
#         d8_path,
#         outlets_file,
#         os.path.join(os.path.split(d8_path)[0], "mask_bassin_xxx_wbt.tif"),
#         esri_pntr = True,
#         )
# =============================================================================
    
    return ds
    
    
###############################################################################
def compute_ldd(dem_path, 
                dirmap = '1-9',
                engine:str = 'pysheds',
                src_crs = None):
    """
    Convert a Digital Elevation Model (DEM) into a Local Drain Direction map (LDD).

    Parameters
    ----------
    dem_path : str, pathlib.Path, xarray.Dataset or xarray.DataArray
        Digital Elevation Model data. Supported file formats are *.tif*, *.asc* and *.nc*. 
        
    dirmap : tuple or str, optional, default '1-9'
        Direction codes convention.
        
        - ``'1-9'`` (or ``'keypad'``, or ``'pcraster'``): from 1 to 9, upward, 
          from bottom-left corner, no-flow is 5 [pcraster convention]
        - ``'D8'`` (or ``'ESRI'``): from 1 to 128 (base-2), clockwise, from 
          middle-right position, no-flow is 0 [esri convention]
        - ``'D8-WBT'`` (or ``'WhiteBoxTools'``): from 1 to 128 (base-2), 
          clockwise, from top-right corner, no-flow is 0 [WhiteBoxTools convention]
          
    engine : {'pysheds', 'whiteboxtools'}, optional, default 'pyshed'
        ``'whiteboxtools'`` has been deactivated to avoid the need to install whiteboxtools.

    Returns
    -------
    LDD raster, xarray.Dataset.

    """
    
    
    # ---- With pysheds
    if engine.casefold() in ["pyshed", "pysheds"]:
        """
        Adapted from Luca Guillaumot's work
        """
        
        print('Pysheds engine...')

        # Load the pysheds elements (grid & data)
# ===== obsolete: load from file ==============================================
        # ext = os.path.splitext(dem_path)[-1]
        # if ext == '.tif':
        #     grid = Grid.from_raster(dem_path, data_name = 'dem')
        #     dem = grid.read_raster(dem_path)
        # elif ext == '.asc':
        #     grid = Grid.from_ascii(dem_path)
        #     dem = grid.read_ascii(dem_path)
# ============================================================================= 
        ds = load_any(dem_path, decode_coords = 'all')
        if src_crs is not None:
            ds.rio.write_crs(src_crs, inplace = True)
        else:
            if ds.rio.crs is None:
                print("Err: The Coordinate Reference System is required. It should be embedded in the input DEM or passed with the 'src_crs' argument")
                return
        ds, nodata = standard_fill_value(data_ds = ds)
        var = main_var(ds)[0]
        print(f"Elevation variable is inferred to be {var}")
        x_var, y_var = main_space_dims(ds)
        encod = ds[var].encoding
        # NaN data are problematic when filling
        # nan_mask = ds[var].isnull().data
        nan_mask = xr.where(~ds[var].isnull(), True, False).data
        ds[var] = ds[var].fillna(-9999)
        ds[var].encoding = encod
        
        viewfinder = ViewFinder(affine = ds.rio.transform(), 
                                shape = ds.rio.shape, 
                                crs = ds.rio.crs, 
                                nodata = nodata)
        dem = Raster(ds[var].data, viewfinder=viewfinder)
        grid = Grid.from_raster(dem)
        
        # Fill depressions in DEM
# =============================================================================
#         print('   . dem no data is ', grid.nodata)
# =============================================================================
        flooded_dem = grid.fill_depressions(dem)
        # Resolve flats in DEM
        inflated_dem = grid.resolve_flats(flooded_dem)
        # Specify directional mapping
        if isinstance(dirmap, str):
            dirmap = dirmap.casefold().replace(' ', '').replace('-', '')
            if dirmap in ['19', '[19]', 'keypad', 'pcraster']:
                dirmap = (8, 9, 6, 3, 2, 1, 4, 7)
            elif dirmap in ['d8', 'esri']:
                dirmap = (64, 128, 1, 2, 4, 8, 16, 32)  # ESRI system
            elif dirmap in ['d8wbt', 'wbt', 'whiteboxtools']:
                dirmap = (128, 1, 2, 4, 8, 16, 32, 64)  # WhiteBox Tools system

        # Compute flow directions
        direc = grid.flowdir(inflated_dem, dirmap=dirmap, 
                             nodata_out = np.int32(-3))
        # Replace flats (-1) with value 5 (no flow)
        direc = xr.where(direc == -1, 5, direc)
        # Replace pits (-2) with value 5 (no flow)
        direc = xr.where(direc == -2, 5, direc)
        
        # Output
        ds[var] = ([y_var, x_var], np.array(direc))
        ds[var] = ds[var].where(nan_mask)
        ds = ds.rename({var: 'LDD'})
# =============================================================================
#         ds['LDD'] = ds['LDD'].astype(float) # astype(int)
# =============================================================================
# =============================================================================
#         ds['LDD'] = ds['LDD'].astype(np.int32)
# =============================================================================
        ds['LDD'].encoding = encod
        ds['LDD'].encoding['dtype'] = np.int32
        ds['LDD'].encoding['rasterio_dtype'] = np.int32
        ds['LDD'].encoding['_FillValue'] = -3
# ========= issue with dtypes when exporting ==================================
#         if 'scale_factor' in ds['LDD'].encoding:
#             ds['LDD'].encoding['scale_factor'] = np.int32(ds['LDD'].encoding['scale_factor'])
#         if 'add_offset' in ds['LDD'].encoding:
#             ds['LDD'].encoding['add_offset'] = np.int32(ds['LDD'].encoding['add_offset'])
#         if '_FillValue' in ds['LDD'].encoding:
#             ds['LDD'].encoding['_FillValue'] = np.int32(-1)
# =============================================================================
        ds = georef(data = ds)
        
    
    # ---- With WhiteToolBox (discontinued)
# =============================================================================
#     elif engine.casefold() in ["wtb", "whitetoolbox"]:
#         print('WhiteToolBox engine...')
#         dist_ = 10
#         
#         # Breach depressions
#         wbt.breach_depressions_least_cost(
#             dem_path,
#             os.path.splitext(dem_path)[0] + f"_breached{dist_}[wtb].tif",
#             dist_)
#         print('    Fichier intermédiaire créé')
#         
# # =============================================================================
# #         # Fill depression (alternative)
# #         wbt.fill_depressions(
# #             dem_path,
# #             os.path.splitext(dem_path)[0] + "_filled[wtb].tif",
# #             10)
# # =============================================================================
#         
#         # Creation du D8
#         suffix = "breached{}[wtb]".format(dist_)
#         wbt.d8_pointer(
#             os.path.splitext(dem_path)[0] + "_" + suffix + ".tif",
#             os.path.join(os.path.split(dem_path)[0], "D8_xxx_" + suffix + "_wtb.tif"), 
#             esri_pntr = True)
#         print('    LDD "D8 ESRI" créé')
# =============================================================================

    return ds    
    

######## DOES NOT WORK ########################################################
# =============================================================================
# for a better solution: https://gis.stackexchange.com/questions/413349/calculating-area-of-lat-lon-polygons-without-transformation-using-geopandas
# =============================================================================
def cell_area(data, src_crs = None, engine = 'pysheds'):
    
    # ---- With pysheds
    if engine.casefold() in ["pyshed", "pysheds"]:
        print('Pysheds engine...')

        # Load the pysheds grid 
        ds = load_any(data, decode_coords = 'all')
        if src_crs is not None:
            ds.rio.write_crs(src_crs, inplace = True)
        else:
            if ds.rio.crs is None:
                print("Err: The Coordinate Reference System is required. It should be embedded in the input DEM or passed with the 'src_crs' argument")
                return
        ds, nodata = standard_fill_value(data_ds = ds)
        var = main_var(ds)[0]
        x_var, y_var = main_space_dims(ds)
        encod = ds[var].encoding
# =============================================================================
#         # NaN data are problematic when filling
#         # nan_mask = ds[var].isnull().data
#         nan_mask = xr.where(~ds[var].isnull(), True, False).data
#         ds[var] = ds[var].fillna(-9999)
# =============================================================================
        ds[var].encoding = encod
        
# ===== useless because pGrid only takes files as inputs ======================
#         viewfinder = ViewFinder(affine = ds.rio.transform(), 
#                                 shape = ds.rio.shape, 
#                                 crs = ds.rio.crs, 
#                                 nodata = nodata)
#         raster = Raster(ds[var].data, viewfinder=viewfinder)
# =============================================================================
        
        export(ds, r"temp_raster.tif")        
        grid = pGrid.from_raster(r"temp_raster.tif", data_name = 'area')
        grid.cell_area()
        os.remove(r"temp_raster.tif")
        print(r"   _ The temporary file 'temp_raster.tif' has been removed")
        
        # Output
        ds[var] = ([y_var, x_var], np.array(grid.area))
        ds = ds.rename({var: 'area'})
        ds['area'].encoding = encod
        
        print("\nWarning: This function does not work as expected yet: area are only computed from the resolution")
        return ds
    

###############################################################################
#%%% ° Convert LDD code
"""
To switch between different direction mappings
"""
def switch_direction_map(input_file, input_mapping, output_mapping):
    
    #%%% Inputs
    mapping = [input_mapping, output_mapping]
    position = ['entrée', 'sortie']
    print("")
    
    for i in [0, 1]:
        if mapping[i].casefold().replace("_", "").replace(" ", "") in ["ldd","localdraindirections"]:
            mapping[i] = "LDD"
        elif mapping[i].casefold().replace("_", "").replace(" ", "") in ["d8", "esri", "d8esri", "esrid8", "d8standard", "standardd8"]:
            mapping[i] = "D8 ESRI"
        elif mapping[i].casefold().replace("_", "").replace(" ", "") in ["wtb", "whitetoolbox", "d8whitetoolbox", "d8wtb", "wtbd8"]:
            mapping[i] = "WTB"
        else:
            mapping[i] = "/!\ non reconnu /!\ "
        print("Direction mapping en {} : {}".format(position[i], mapping[i]))

    if "/!\ non reconnu /!\ " in mapping:
        return "error"
    

    #%%% Conversion    
    # Chargement des données
    data_in = rasterio.open(input_file, 'r')
    data_profile = data_in.profile
    val = data_in.read()
    data_in.close()
    
    # Conversion
    
    # rows: 0:'LDD', 1:'D8', 2:'WTB'
    col = ['LDD', 'D8 ESRI', 'WTB']
    keys_ = np.array(
        [[8, 64,  128,],#N
         [9, 128, 1,],  #NE
         [6, 1,   2,],  #E
         [3, 2,   4,],  #SE
         [2, 4,   8,],  #S
         [1, 8,   16,], #SO
         [4, 16,  32,], #O
         [7, 32,  64,], #NO
         [5, 0,   0,]]) #-
    
    for d in range(0, 9):
        val[val == keys_[d, 
                         col.index(mapping[0])
                         ]
            ] = -keys_[d, 
                      col.index(mapping[1])]
        
    val = -val # On passe par une valeur négative pour éviter les redondances
    # du type : 3 --> 2, 2 --> 4
    
    #%%% Export
    output_file = os.path.splitext(input_file)[0] + "_{}.tif".format(mapping[1])
    
    with rasterio.open(output_file, 'w', **data_profile) as output_f:
        output_f.write(val)
        print("\nFichier créé.")
        

###############################################################################
#%%% ° Alter modflow_river_percentage
def river_pct(input_file, value):
    """
    Creates artificial modflow_river_percentage inputs (in *.nc) to use for
    drainage.

    Parameters
    ----------
    input_file : str
        Original modflow_river_percentage.tif file to duplicate/modify
    value : float
        Value to impose on cells (from [0 to 1], not in percentage!)
        This value is added to original values as a fraction of the remaining
        "non-river" fraction:
            For example, value = 0.3 (30%):
                - cells with 0 are filled with 0.3
                - cells with 1 remain the same
                - cells with 0.8 take the value 0.86, because 30% of what should
                have been capillary rise become baseflow (0.8 + 0.3*(1-0.8))
                - cells with 0.5 take the value 0.65 (0.5 + 0.3*(1-0.5))

    Returns
    -------
    None.

    """
    #%% Loading
    # ---------
    if os.path.splitext(input_file)[-1] == '.tif':
        with xr.open_dataset(input_file, # .tif 
                             decode_times = True, 
                             ) as ds:
            ds.load()
    elif os.path.splitext(input_file)[-1] == '.nc':
        with xr.open_dataset(input_file, 
                             decode_times = True, 
                             decode_coords = 'all',
                             ) as ds:
            ds.load()   
    
    #%% Computing
    # -----------
    # ds['band_data'] = ds['band_data']*0 + value
    ds_ones = ds.copy(deep = True)
    ds_ones['band_data'] = ds_ones['band_data']*0 + 1
    
    #% modflow_river_percentage_{value}.nc:
    ds1 = ds.copy(deep = True)
    ds1['band_data'] = ds1['band_data'] + (ds_ones['band_data'] - ds1['band_data'])*value
    
    #% drainage_river_percentage_{value}.nc :
    ds2 = ds1 - ds
    
    #%% Formatting
    # ------------
    ds1.rio.write_crs(2154, inplace = True)
    ds1.x.attrs = {'standard_name': 'projection_x_coordinate',
                                'long_name': 'x coordinate of projection',
                                'units': 'Meter'}
    ds1.y.attrs = {'standard_name': 'projection_y_coordinate',
                                'long_name': 'y coordinate of projection',
                                'units': 'Meter'}
    # To avoid conflict when exporting to netcdf:
    ds1.x.encoding['_FillValue'] = None
    ds1.y.encoding['_FillValue'] = None
    
    ds2.rio.write_crs(2154, inplace = True)
    ds2.x.attrs = {'standard_name': 'projection_x_coordinate',
                                'long_name': 'x coordinate of projection',
                                'units': 'Meter'}
    ds2.y.attrs = {'standard_name': 'projection_y_coordinate',
                                'long_name': 'y coordinate of projection',
                                'units': 'Meter'}
    # To avoid conflict when exporting to netcdf:
    ds2.x.encoding['_FillValue'] = None
    ds2.y.encoding['_FillValue'] = None
    
    #%% Exporting
    # -----------
    (folder, file) = os.path.split(input_file)
    (file, extension) = os.path.splitext(file)
    
    output_file1 = os.path.join(folder, "_".join([file, str(value)]) + '.nc')
    ds1.to_netcdf(output_file1)
    
    output_file2 = os.path.join(folder, "_".join(['drainage_river_percentage', str(value)]) + '.nc')
    ds2.to_netcdf(output_file2)


#%% QUANTITIES OPERATIONS
###############################################################################
# Calcule ETref et EWref à partir de la "pan evaporation" de ERA5-Land
def compute_Erefs_from_Epan(input_file):
    print("\nDeriving standard grass evapotranspiration and standard water evapotranspiration from pan evaporation...")
    Epan = load_any(input_file, decode_coords = 'all', decode_times = True)
    
    var = main_var(Epan)
    
    print("   _ Computing ETref (ET0) from Epan...")
    ETref = Epan.copy()
    ETref[var] = ETref[var]*0.675
    
    print("   _ Computing EWref from Epan...")
    EWref = Epan.copy()
    EWref[var] = EWref[var]*0.75
    
    print("   _ Transferring encodings...")
    ETref[var].encoding = Epan[var].encoding
    EWref[var].encoding = Epan[var].encoding
    # Case of packing
    if ('scale_factor' in Epan[var].encoding) | ('add_offset' in Epan[var].encoding):
        # Packing (lossy compression) induces a loss of precision of 
        # apprx. 1/1000 of unit, for a quantity with an interval of 150 
        # units. The packing is initially used in some original ERA5-Land data
        ETref[var].encoding['scale_factor'] = ETref[var].encoding['scale_factor']*0.675
        ETref[var].encoding['add_offset'] = ETref[var].encoding['add_offset']*0.675
        EWref[var].encoding['scale_factor'] = EWref[var].encoding['scale_factor']*0.75
        EWref[var].encoding['add_offset'] = EWref[var].encoding['add_offset']*0.75
    
    return ETref, EWref


###############################################################################
def compute_wind_speed(u_wind_data, v_wind_data):
    """
    U-component of wind is parallel to the x-axis
    V-component of wind is parallel to the y-axis
    """
    
# =============================================================================
#     print("\nIdentifying files...")
#     U_motif = re.compile('U-component')
#     U_match = U_motif.findall(input_file)
#     V_motif = re.compile('V-component')
#     V_match = V_motif.findall(input_file)
#     
#     if len(U_match) > 0:
#         U_input_file = '%s' % input_file # to copy the string
#         V_input_file = '%s' % input_file
#         V_input_file = V_input_file[:U_motif.search(input_file).span()[0]] + 'V' + V_input_file[U_motif.search(input_file).span()[0]+1:]
#     elif len(V_match) > 0:
#         V_input_file = '%s' % input_file # to copy the string
#         U_input_file = '%s' % input_file
#         U_input_file = U_input_file[:V_motif.search(input_file).span()[0]] + 'U' + U_input_file[V_motif.search(input_file).span()[0]+1:]
# =============================================================================
    
    print("\nComputing wind speed from U- and V-components...")

    U_ds = load_any(u_wind_data, decode_coords = 'all', decode_times = True)
    V_ds = load_any(v_wind_data, decode_coords = 'all', decode_times = True)
    
    wind_speed_ds = U_ds.copy()
    wind_speed_ds = wind_speed_ds.rename(u10 = 'wind_speed')
    wind_speed_ds['wind_speed'] = np.sqrt(U_ds.u10*U_ds.u10 + V_ds.v10*V_ds.v10)
        # nan remain nan
    
    print("   _ Transferring encodings...")
    wind_speed_ds['wind_speed'].encoding = V_ds.v10.encoding
    wind_speed_ds['wind_speed'].attrs['long_name'] = '10 metre wind speed'
    # Case of packing
    if ('scale_factor' in V_ds.v10.encoding) | ('add_offset' in V_ds.v10.encoding):
        # Packing (lossy compression) induces a loss of precision of 
        # apprx. 1/1000 of unit, for a quantity with an interval of 150 
        # units. The packing is initially used in some original ERA5-Land data
    
        # Theoretical max wind speed: 
        max_speed = 56 # m/s = 201.6 km/h
        (scale_factor, add_offset) = compute_scale_and_offset(-max_speed, max_speed, 16)
            # Out: (0.0017090104524299992, 0.0008545052262149966)
        wind_speed_ds['wind_speed'].encoding['scale_factor'] = scale_factor
        wind_speed_ds['wind_speed'].encoding['add_offset'] = add_offset
        # wind_speed_ds['wind_speed'].encoding['FillValue_'] = -32767
            # To remain the same as originally
            # Corresponds to -55.99829098954757 m/s
    
    return wind_speed_ds
    

###############################################################################
def compute_relative_humidity(*, dewpoint_input_file, 
                              temperature_input_file,
                              pressure_input_file,
                              method = "Penman-Monteith"):
    
    """
    cf formula on https://en.wikipedia.org/wiki/Dew_point
    
    gc.compute_relative_humidity(
        dewpoint_input_file = r"D:\2- Postdoc\2- Travaux\1- Veille\4- Donnees\8- Meteo\ERA5\Brittany\2011-2021 Dewpoint temperature.nc", 
        temperature_input_file = r"D:\2- Postdoc\2- Travaux\1- Veille\4- Donnees\8- Meteo\ERA5\Brittany\2011-2021 Temperature.nc",
        pressure_input_file = r"D:\2- Postdoc\2- Travaux\1- Veille\4- Donnees\8- Meteo\ERA5\Brittany\2011-2021 Surface pressure.nc",
        method = "Sonntag")
    
    """
    
    
    # ---- Loading data
    # --------------
    print("\nLoading data...")
    # Checking that the time period matches:
    years_motif = re.compile('\d{4,4}-\d{4,4}')
    years_dewpoint = years_motif.search(dewpoint_input_file).group()
    years_pressure = years_motif.search(pressure_input_file).group()
    years_temperature = years_motif.search(temperature_input_file).group()
    if (years_dewpoint == years_pressure) and (years_dewpoint == years_temperature):
        print("   Years are matching: {}".format(years_dewpoint))
    else:
        print("   /!\ Years are not matching: {}\n{}\n{}".format(years_dewpoint, years_pressure, years_temperature))
        # return 0
    
    with xr.open_dataset(dewpoint_input_file, decode_coords = 'all') as Dp:
        Dp.load() # to unlock the resource
    with xr.open_dataset(temperature_input_file, decode_coords = 'all') as T:
        T.load() # to unlock the resource
    with xr.open_dataset(pressure_input_file, decode_coords = 'all') as Pa:
        Pa.load() # to unlock the resource
    
    # ---- Sonntag formula
    # -----------------
    if method.casefold() in ['sonntag', 'sonntag1990']:
        print("\nComputing the relative humidity, using the Sonntag 1990 formula...")
        # NB : air pressure Pa is not used in this formula
        
        # Constants:
        alpha_ = 6.112 # [hPa]
        beta_ = 17.62 # [-]
        lambda_ = 243.12 # [°C]
        
        # Temperature in degrees Celsius:
        Tc = T.copy()
        Tc['t2m'] = T['t2m'] - 273.15
        Dpc = Dp.copy()
        Dpc['d2m'] = Dp['d2m'] - 273.15
        
        # Saturation vapour pressure [hPa]:
        Esat = Tc.copy()
        Esat = Esat.rename(t2m = 'vpsat')
        Esat['vpsat'] = alpha_ * np.exp((beta_ * Tc['t2m']) / (lambda_ + Tc['t2m']))
        
        # Vapour pressure [hPa]:
        E = Dp.copy()
        E = E.rename(d2m = 'vp')
        E['vp'] = alpha_ * np.exp((Dpc['d2m'] * beta_) / (lambda_ + Dpc['d2m']))
        
        # Relative humidity [%]:
        RHS = Dp.copy()
        RHS = RHS.rename(d2m = 'rh')
        RHS['rh'] = E['vp']/Esat['vpsat']*100
    
    elif method.casefold() in ['penman', 'monteith', 'penman-monteith']:
        print("\nComputing the relative humidity, using the Penman Monteith formula...")
        # NB : air pressure Pa is not used in this formula
        # Used in evaporationPot.py
        # http://www.fao.org/docrep/X0490E/x0490e07.htm   equation 11/12
        
        # Constants:
        alpha_ = 0.6108 # [kPa]
        beta_ = 17.27 # [-]
        lambda_ = 237.3 # [°C]
        
        # Temperature in degrees Celsius:
        Tc = T.copy()
        Tc['t2m'] = T['t2m'] - 273.15
        Dpc = Dp.copy()
        Dpc['d2m'] = Dp['d2m'] - 273.15
        
        # Saturation vapour pressure [kPa]:
        Esat = Tc.copy()
        Esat = Esat.rename(t2m = 'vpsat')
        Esat['vpsat'] = alpha_ * np.exp((beta_ * Tc['t2m']) / (lambda_ + Tc['t2m']))
        
        # Vapour pressure [kPa]:
        E = Dp.copy()
        E = E.rename(d2m = 'vp')
        E['vp'] = alpha_ * np.exp((beta_ * Dpc['d2m']) / (lambda_ + Dpc['d2m']))
        
        # Relative humidity [%]:
        # https://www.fao.org/3/X0490E/x0490e07.htm Eq. (10)
        RHS = Dp.copy()
        RHS = RHS.rename(d2m = 'rh')
        RHS['rh'] = E['vp']/Esat['vpsat']*100
        
    #% Attributes
    print("\nTransferring encodings...")
    RHS['rh'].attrs['units'] = '%'
    RHS['rh'].attrs['long_name'] = 'Relative humidity (from 2m dewpoint temperature)'
    RHS['rh'].encoding = Dp['d2m'].encoding
    # Case of packing
    if ('scale_factor' in Dp['d2m'].encoding) | ('add_offset' in Dp['d2m'].encoding):
        # Packing (lossy compression) induces a loss of precision of 
        # apprx. 1/1000 of unit, for a quantity with an interval of 150 
        # units. The packing is initially used in some original ERA5-Land data.
        
        # RHS['rh'].encoding['scale_factor'] = 0.0016784924086366065
        # RHS['rh'].encoding['add_offset'] = 55.00083924620432
        # RHS['rh'].encoding['_FillValue'] = 32767
        # RHS['rh'].encoding['missing_value'] = 32767
        (scale_factor, add_offset) = compute_scale_and_offset(-1, 100, 16)
            # Out: (0.0015411612115663385, 49.50077058060578)
        RHS['rh'].encoding['scale_factor'] = scale_factor
        RHS['rh'].encoding['add_offset'] = add_offset
        # RHS['rh'].encoding['_FillValue'] = -32767 
            # To match with original value
            # Corresponds to -0.9984588387884301 %
    
    
    return RHS


###############################################################################
# Convertit les données de radiation (J/m2/h) en W/m2
def convert_downwards_radiation(input_file, is_dailysum = False):   
    print("\nConverting radiation units...")
    rad = load_any(input_file, decode_coords = 'all', decode_times = True)
    
    var = main_var(rad)
    print("   _ Field is: {}".format(var))
    
    print("   _ Computing...")
    rad_W = rad.copy()
    if not is_dailysum:
        conv_factor = 3600 # because 3600s in 1h
    else:
        conv_factor = 86400 # because 86400s in 1d
    rad_W[var] = rad_W[var]/conv_factor 
    
    print("   _ Transferring encodings...")
    rad_W[var].attrs['units'] = 'W m**-2'
    rad_W[var].encoding = rad[var].encoding
    
    # Case of packing
    if ('scale_factor' in rad_W[var].encoding) | ('add_offset' in rad_W[var].encoding):
        # Packing (lossy compression) induces a loss of precision of 
        # apprx. 1/1000 of unit, for a quantity with an interval of 150 
        # units. The packing is initially used in some original ERA5-Land data.
        rad_W[var].encoding['scale_factor'] = rad_W[var].encoding['scale_factor']/conv_factor
        rad_W[var].encoding['add_offset'] = rad_W[var].encoding['add_offset']/conv_factor
        # NB: 
        # rad_W[var].encoding['FillValue_'] = -32767
            # To remain the same as originally
            # Corresponds to -472.11... m/s
            # NB: For few specific times, data are unavailable. Such data are coded 
            # with the value -1, packed into -32766
    
    return rad_W
    


#%% * OBSOLETE ? Shift rasters (GeoTIFF or NetCDF)
###############################################################################
# Pas totalement fini. Code issu de 'datatransform.py'
def transform_tif(*, input_file, x_shift = 0, y_shift = 0, x_size = 1, y_size = 1):
    """
    EXAMPLE:
        import datatransform as dt
        dt.transform_tif(input_file = r"D:\2- Postdoc\2- Travaux\3_CWatM_EBR\data\input_1km_LeMeu\areamaps\mask_cwatm_LeMeu_1km.tif",
                     x_shift = 200,
                     y_shift = 300)
    """
    
    # Ouvrir le fichier : 
    data = rasterio.open(input_file, 'r')
    # Récupérer le profil :
    _prof_base = data.profile
    trans_base = _prof_base['transform']
    # Juste pour visualiser :
    print('\nLe profil affine initial est :')
    print(trans_base)
    # Modifier le profile :  
    trans_modf = Affine(trans_base[0]*x_size, trans_base[1], trans_base[2] + x_shift,
                        trans_base[3], trans_base[4]*y_size, trans_base[5] + y_shift)
    print('\nLe profil modifié est :')
    print(trans_modf)
    _prof_modf = _prof_base
    _prof_modf.update(transform = trans_modf)
    
    # Exporter :
    _basename = os.path.splitext(input_file)[0]
    
    add_name = ''
    if x_shift != 0 or y_shift !=0:
        add_name = '_'.join([add_name, 'shift'])
        if x_shift != 0:
            add_name = '_'.join([add_name, 'x' + str(x_shift)])
        if y_shift != 0:
            add_name = '_'.join([add_name, 'y' + str(y_shift)])
    if x_size != 1 or y_size !=1:
        add_name = '_'.join([add_name, 'size'])
        if x_size != 1:
            add_name = '_'.join([add_name, 'x' + str(x_size)])
        if y_size != 1:
            add_name = '_'.join([add_name, 'y' + str(y_size)])
    output_file = '_'.join([_basename, add_name]) + '.tif'
    with rasterio.open(output_file, 'w', **_prof_modf) as out_f:
        out_f.write_band(1, data.read()[0])
    
    data.close()
    
def transform_nc(*, input_file, x_shift = 0, y_shift = 0, x_size = 1, y_size = 1):
    """
    EXAMPLE:
        import datatransform as dt
        dt.transform_nc(input_file = r"D:\2- Postdoc\2- Travaux\3_CWatM_EBR\data\input_1km_LeMeu\landsurface\topo\demmin.nc",
                     x_shift = 200,
                     y_shift = 400)       
    """
    
    with xr.open_dataset(input_file) as data:
        data.load() # to unlock the resource
        
    # Modifier :
    data['x'] = data.x + x_shift
    data['y'] = data.y + y_shift
    
    # Exporter :
    _basename = os.path.splitext(input_file)[0]
    
    add_name = ''
    if x_shift != 0 or y_shift !=0:
        add_name = '_'.join([add_name, 'shift'])
        if x_shift != 0:
            add_name = '_'.join([add_name, 'x' + str(x_shift)])
        if y_shift != 0:
            add_name = '_'.join([add_name, 'y' + str(y_shift)])
    if x_size != 1 or y_size !=1:
        add_name = '_'.join([add_name, 'size'])
        if x_size != 1:
            add_name = '_'.join([add_name, 'x' + str(x_size)])
        if y_size != 1:
            add_name = '_'.join([add_name, 'y' + str(y_size)])
    output_file = '_'.join([_basename, add_name]) + '.nc'
    
    data.to_netcdf(output_file)
    

#%% * tools for computing coordinates
###############################################################################
def convert_coord(pointXin, pointYin, inputEPSG = 2154, outputEPSG = 4326):	
    """
    Il y a un soucis dans cette fonction. X et Y se retrouvent inversées.
    Il vaut mieux passer par les fonctions rasterio (voir plus haut) :
        
    coords_conv = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(inputEPSG), 
                                          rasterio.crs.CRS.from_epsg(outputEPSG), 
                                          [pointXin], [pointYin])
    pointXout = coords_conv[0][0]
    pointYout = coords_conv[1][0]
    """
    #% Inputs (standards)
    # =============================================================================
    # # Projected coordinates in Lambert-93 
    # pointXin = 350556.92318   #Easthing
    # pointYin = 6791719.72296  #Northing
    # (Rennes coordinates)
    # =============================================================================
    
    # =============================================================================
    # # Geographical coordinates in WGS84 (2D) 
    # pointXin = 48.13222  #Latitude (Northing)
    # pointYin = -1.7      #Longitude (Easting)
    # (Rennes coordinates)
    # =============================================================================
    
    # =============================================================================
    # # Spatial Reference Systems
    # inputEPSG = 2154   #Lambert-93
    # outputEPSG = 4326  #WGS84 (2D)
    # =============================================================================
    
    # # Conversion into EPSG system
    # For easy use, inputEPSG and outputEPSG can be defined with identifiers strings
    switchEPSG = {
        'L93': 2154,   #Lambert-93
        'L-93': 2154,  #Lambert-93
        'WGS84': 4326, #WGS84 (2D)
        'GPS': 4326,   #WGS84 (2D)
        'LAEA': 3035,  #LAEA Europe 
        }
    
    if isinstance(inputEPSG, str):
        inputEPSG = switchEPSG.get(inputEPSG, False)
        # If the string is not a valid identifier:
        if not inputEPSG:
            print('Unknown input coordinates system')
            return
            
    if isinstance(outputEPSG, str):
        outputEPSG = switchEPSG.get(outputEPSG, False)
        # If the string is not a valid identifier:
        if not outputEPSG:
            print('Unknown output coordinates system')
            return

    
    #% Outputs
# =============================================================================
#     # Méthode osr
#     # create a geometry from coordinates
#     point = ogr.Geometry(ogr.wkbPoint)
#     point.AddPoint(pointXin, pointYin)
#     
#     # create coordinate transformation
#     inSpatialRef = osr.SpatialReference()
#     inSpatialRef.ImportFromEPSG(inputEPSG)
#     
#     outSpatialRef = osr.SpatialReference()
#     outSpatialRef.ImportFromEPSG(outputEPSG)
#     
#     coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
#     
#     # transform point
#     point.Transform(coordTransform)
#     pointXout = point.GetX()
#     pointYout = point.GetY()
# =============================================================================
    
    # Méthode rasterio      
    coords_conv = rasterio.warp.transform(rasterio.crs.CRS.from_epsg(inputEPSG), 
                                          rasterio.crs.CRS.from_epsg(outputEPSG), 
                                          [pointXin], [pointYin])
    pointXout = coords_conv[0][0]
    pointYout = coords_conv[1][0]
    
    # Return point coordinates in output format
    return(pointXout, pointYout)


#%% date tools for QGIS
"""
Pour faire facilement la conversion "numéro de bande - date" dans QGIS lorsqu'on
ouvre les fichers NetCDF comme rasters.

/!\ Dans QGIS, le numéro de 'band' est différent du 'time'
(parfois 'band' = 'time' + 1, parfois il y a une grande différence)
C'est le 'time' qui compte.
"""
###############################################################################
def date_to_index(_start_date, _date, _freq):
    time_index = len(pd.date_range(start = _start_date, end = _date, freq = _freq))-1
    print('La date {} correspond au temps {}'.format(_date, str(time_index)))
    return time_index


###############################################################################
def index_to_date(_start_date, _time_index, _freq):
    date_index = pd.date_range(start = _start_date, periods = _time_index+1, freq = _freq)[-1]
    print('Le temps {} correspond à la date {}'.format(_time_index, str(date_index)))
    return date_index


#%% main
if __name__ == "__main__":
    # Format the inputs (assumed to be strings) into floats
    sys.argv[1] = float(sys.argv[1])
    sys.argv[2] = float(sys.argv[2])
    # Print some remarks
    print('Arguments:')
    print(sys.argv[1:])
    # Execute the ConvertCoord function
    (a,b) = convert_coord(*sys.argv[1:])
    print(a,b)