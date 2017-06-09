import geopandas
from geopandas.tools import sjoin
import pandas as pd
from shapely.geometry import Point
import datetime
import numpy as np
import os


#tools


#load shapefile function
def load_dataframe_from_csv_tool(path,filename,columns,encoding):
	try:
		dataframe 				=		pd.read_csv(path+filename,sep=',',encoding=encoding)
		#renaming columns
		dataframe.columns 		=	 	columns		
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst)

#update column dtypes on dataframe
def update_default_dtyped_on_dataframe(dataframe,settings_dictionnary):
	try:
		for key in settings_dictionnary.keys():
			dataframe[key]		=		dataframe[key].fillna(np.nan)
			#updating dtypes
			dataframe[key]		=		dataframe[key].astype(settings_dictionnary[key])
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst)

def extract_address_elements(dataframe,address_column_name):
	try:
		address_elements 				=		dataframe[address_column_name].str.split(',', expand=True).astype(str)
		dataframe['address_street']		=		address_elements[0].str.upper().str.strip().str.replace(' ','_')
		dataframe['address_settlement']	=		address_elements[1].str.upper().str.strip().str.replace(' ','_')
		dataframe['address_town']		=		address_elements[2].str.upper().str.strip().str.replace(' ','_')
		dataframe['address_state']		=		address_elements[3].str.upper().str.strip().str.replace(' ','_')
		
		#encoding corrections
		dataframe['address_street']		=		dataframe['address_street'].str.upper().str.replace(' ','_').str.replace('ÕÔË±','N').str.replace('ÕÔË©','E').str.replace('ÕÔË_','U').str.replace('ÕÔË','A').str.replace('ÕÔÕ','A').str.replace('IÕÔ_','IO').str.replace('OË±','N').str.replace('ÕÔ_','I').str.replace('ÕÔ','O')
		dataframe['address_settlement']	=		dataframe['address_settlement'].str.upper().str.replace(' ','_').str.replace('ÕÔË±','N').str.replace('ÕÔË©','E').str.replace('ÕÔË_','U').str.replace('ÕÔË','A').str.replace('ÕÔÕ','A').str.replace('IÕÔ_','IO').str.replace('OË±','N').str.replace('ÕÔ_','I').str.replace('ÕÔ','O')
		dataframe['address_town']		=		dataframe['address_town'].str.upper().str.replace(' ','_').str.replace('ÕÔË±','N').str.replace('ÕÔË©','E').str.replace('ÕÔË_','U').str.replace('ÕÔË','A').str.replace('ÕÔÕ','A').str.replace('IÕÔ_','IO').str.replace('OË±','N').str.replace('ÕÔ_','I').str.replace('ÕÔ','O')
		dataframe['address_state']		=		dataframe['address_state'].str.upper().str.replace(' ','_').str.replace('ÕÔË±','N').str.replace('ÕÔË©','E').str.replace('ÕÔË_','U').str.replace('ÕÔË','A').str.replace('ÕÔÕ','A').str.replace('IÕÔ_','IO').str.replace('OË±','N').str.replace('ÕÔ_','I').str.replace('ÕÔ','O')
		
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst)


#load geodataframe from shapefiles
def load_geodataframe_from_shapefile_tool(path,shfilename):
	try:
		geodataframe 					=		geopandas.GeoDataFrame.from_file(path+shfilename)
		return geodataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 

#reproject geo-dataframe
def reproject_dataframe_tool(final_crs,geodataframe):
	try:
		return geodataframe.to_crs(final_crs)
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 

#built single points geodaframe from dataframe
def single_points_geodataframe_from_dataframe(lon_column_name,lat_column_name,crs,old_dataframe):
	try:		
		dataframe 						=	old_dataframe.copy()
		#conversion to numeric, with option 'coerce', such that all non-numeric entries are converted to NaN
		dataframe[lat_column_name]		=	dataframe[lat_column_name].apply(pd.to_numeric, errors='coerce')
		dataframe[lon_column_name]		=	dataframe[lon_column_name].apply(pd.to_numeric, errors='coerce')

		#cleaning null values 
		dataframe 						=	dataframe[dataframe[lon_column_name].notnull()]#fue necesario para evitar error
		dataframe 						=	dataframe[dataframe[lat_column_name].notnull()]#fue necesario para evitar error

		geometry 				    	=	[Point(xy) for xy in zip(dataframe.longitud, dataframe.latitud)]
		#dataframe 						=	dataframe.drop([lon_column_name,lat_column_name], axis=1)
		single_points_gdf				=	geopandas.GeoDataFrame(dataframe, crs=crs, geometry=geometry)
		return single_points_gdf
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 

def cleaning_property_age_values(dataframe,age_column_name):
	try:
		dataframe[age_column_name]     	=	dataframe[age_column_name].str.extract('(\d+)')
		dataframe[age_column_name]     	=	dataframe[age_column_name].fillna('no_age_info')
		dataframe[age_column_name]		=	[int(age) if age!='no_age_info' else age for age in dataframe[age_column_name]]
		now								= 	datetime.datetime.now()
		current_year 					=	now.year
		#age correction: some fields contains year built instead of age
		dataframe[age_column_name]    	=	[int(current_year-age) if age!='no_age_info' and age>1700 else age for age in dataframe[age_column_name]]
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 



#price conversion 
def price_conversion_tool(dataframe,price_column_name,currency_column_name):
	try:
		dataframe[price_column_name]	=	dataframe[price_column_name].str.replace(',','').str.extract('(\d+)').astype(int)
		dataframe['price']	=	[value*18.7 if currency=='USD' else value for currency,value in zip(dataframe[currency_column_name],dataframe[price_column_name])]
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 

#cleaning surface from 'm2'
def surface_field_cleaning_tool(dataframe,lotsize_column_name,size_column_name):
	try:
		#conversion to numeric, with option 'coerce', such that all non-numeric entries are converted to NaN
		dataframe[lotsize_column_name]	=	dataframe[lotsize_column_name].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)#.astype(int)#.str.replace('m2','').str.replace('.','').str.extract('(\d+)').fillna(0).astype(int)
		dataframe[size_column_name]		=	dataframe[size_column_name].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)#.astype(int)#.str.replace('m2','').str.replace('.','').str.extract('(\d+)').fillna(0).astype(int)
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 

def convert_columns_to_boolean(dataframe,columns_to_convert):
	try:
		for columnname in columns_to_convert:
			dataframe[columnname]     		=	dataframe[columnname].fillna(False)
			dataframe[columnname]     		=	[True if val=='Si' else val  for val in dataframe[columnname]]
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 
#fill na values with default values
def fillna_on_specific_columns(dataframe,settings_dictionary):
	try:
		for columnname in settings_dictionary.keys():
			#import code; code.interact(local=locals())
			dataframe[columnname]     		=	dataframe[columnname].fillna(settings_dictionary[columnname])
		return dataframe
	except Exception as inst:
		print(type(inst))    # the exception instance
		print(inst.args)     # arguments stored in .args
		print(inst) 
