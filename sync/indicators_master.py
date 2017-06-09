import geopandas
from geopandas.tools import sjoin
import pandas as pd
from shapely.geometry import Point
import datetime
import numpy as np
import os
import indicators_tools as tools


#-------------------------I LOAD FILES
#load offer logs file as dataframe
columns                    		=	['id','url','title','source','extrated_on','property_type','offer_type','offer_id',
                                   'currency','price_currency','age','lot_size','size','n_bathrooms','n_bedrooms','n_parking_spaces',
                                   'address','latitud','longitud','delivered_on','publisher_name','publisher_address',
                                   'publisher_phone','nocnok_id','has_elevator','has_security','has_air_conditioning',
                                   'has_heating','has_laundry_room','has_maids_room','has_storage_in_unit','has_grilling_area',
                                   'has_gym','has_playground','has_party_room','has_pool_area','has_garden','has_yard','has_roof_garden',
                                   'has_movie_theater','has_visitors_parking','has_tennis_court']

dtypes_dictionnary				=	{'id':int,'url':str,'title':str,'source':str,'extrated_on':str,
									'property_type':str,'offer_type':str,'offer_id':str,'currency':str,
									'price_currency':str,'age':str,'lot_size':str,'size':str,
									'n_bathrooms':str,'n_bedrooms':str,'n_parking_spaces':str,'address':str,
									'latitud':str,'longitud':str,'delivered_on':str,
									'publisher_name':str,'publisher_address':str,'publisher_phone':str,'nocnok_id':str,
									'has_elevator':bool,'has_security':bool,'has_air_conditioning':bool,'has_heating':bool,
									'has_laundry_room':bool,'has_maids_room':bool,'has_storage_in_unit':bool,'has_grilling_area':bool,
									'has_gym':bool,'has_playground':bool,'has_party_room':bool,'has_pool_area':bool,
									'has_garden':bool,'has_yard':bool,'has_roof_garden':bool,'has_movie_theater':bool,
									'has_visitors_parking':bool,'has_tennis_court':bool}

#fill na values on specific columns
fillna_settings_dictionary 		=	{'latitud':'no_lat_data','longitud':'no_lon_data',
									 'n_bathrooms':'no_baths_notice','n_bedrooms':'no_bedrooms_notice',
									 'n_parking_spaces':'no_parking_notice','age':'no_age_info',
									 'has_elevator':False,'has_security':False,
									 'has_air_conditioning':False,'has_heating':False,
									 'has_laundry_room':False,'has_maids_room':False,
									 'has_storage_in_unit':False,'has_grilling_area':False,
									 'has_gym':False,'has_playground':False,'has_party_room':False,'has_pool_area':False,
									 'has_garden':False,'has_yard':False,'has_roof_garden':False,'has_movie_theater':False,
									 'has_visitors_parking':False,'has_tennis_court':False}
#Exta FEATURES
extra_features 					=	['has_laundry_room','has_storage_in_unit','has_air_conditioning','has_heating','has_maids_room','has_visitors_parking']
#AMENITIES
amenities 						=	['has_gym','has_roof_garden','has_yard','has_party_room','has_grilling_area','has_pool_area','has_tennis_court','has_movie_theater','has_playground','has_garden']

#------for sale
properties_for_sale 			=	tools.load_dataframe_from_csv_tool(path='',filename='properties_25_26_may_2017.csv',columns=columns,encoding='utf-8')
properties_for_sale 			=	tools.fillna_on_specific_columns(properties_for_sale,settings_dictionary=fillna_settings_dictionary)

properties_for_sale	 			=	tools.convert_columns_to_boolean(properties_for_sale,columns_to_convert=extra_features)
properties_for_sale	 			=	tools.convert_columns_to_boolean(properties_for_sale,columns_to_convert=amenities)
properties_for_sale 			=	tools.update_default_dtyped_on_dataframe(properties_for_sale,dtypes_dictionnary)

properties_for_sale 			=	tools.extract_address_elements(properties_for_sale,'address')
print('sale loaded')
#------for rent
properties_for_rent 			=	tools.load_dataframe_from_csv_tool(path='',filename='properties_th_metroscubicos_lease_2017-05-29.csv',columns=columns,encoding='utf-8')
properties_for_rent 			=	tools.fillna_on_specific_columns(properties_for_rent,settings_dictionary=fillna_settings_dictionary)

properties_for_rent 			=	tools.convert_columns_to_boolean(properties_for_rent,columns_to_convert=extra_features)
properties_for_rent 			=	tools.convert_columns_to_boolean(properties_for_rent,columns_to_convert=amenities)
properties_for_rent				=	tools.update_default_dtyped_on_dataframe(properties_for_rent,dtypes_dictionnary)

properties_for_rent 			=	tools.extract_address_elements(properties_for_rent,'address')

print('properties loaded')
print('initial len: sales ',len(properties_for_sale))
print('initial len: leasing',len(properties_for_rent))

print('initial len dep:',len(properties_for_sale[properties_for_sale['property_type']=='departamento']))
print('initial len dep:',len(properties_for_rent[properties_for_rent['property_type']=='departamento']))
#load settlements shapefile
#path 							=	'settlements_df_truehome_version/'
#filename 						=	'settlements_df_truehome_version.shp'
path 							=	'/SETTLEMENTS/'
filename 						=	'settlements_CDMX.shp'
polygons 						=	tools.load_geodataframe_from_shapefile_tool(path=path,shfilename=filename)
 
#Reproject to epsg:4326, if necessary
if (polygons.crs 				!=	{'init': 'epsg:4326'}):
	#repriject
	polygons 					=	tools.reproject_dataframe_tool(final_crs={'init': 'epsg:4326'},geodataframe=polygons)
	print("polygons reprojected")

#reset index on polygons
polygons 						=	polygons.reset_index()
polygons 						=	polygons.rename(columns={'index': 'POLYGON_INDEX'})	


#load data points as shapefile
points_for_sale					=	tools.single_points_geodataframe_from_dataframe(lon_column_name='longitud',lat_column_name='latitud',crs={'init': 'epsg:4326'},old_dataframe=properties_for_sale)
points_for_rent 				=	tools.single_points_geodataframe_from_dataframe(lon_column_name='longitud',lat_column_name='latitud',crs={'init': 'epsg:4326'},old_dataframe=properties_for_rent)

print("polygons loaded")
#-------------------------II FILTERING POINTS
#remove duplicates

#remove accents in name of 
#polygons['MUN_NAME'] 						= polygons['MUN_NAME'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

#solo departamentos
print('before departamento',len(points_for_sale))
points_for_sale 				=	points_for_sale[points_for_sale['property_type']=='departamento']
points_for_rent 				=	points_for_rent[points_for_rent['property_type']=='departamento']
print('departamento for sale',len(points_for_sale))
print('departamento for rent',len(points_for_rent))

print("filters done")
#-------------------------IV SPATIAL JOIN
points_for_sale_in_polygons 	= 	sjoin(points_for_sale, polygons, how='left')
points_for_rent_in_polygons 	= 	sjoin(points_for_rent, polygons, how='left')
print("spatial join done")

#filter
print('before CVE_ENT',len(points_for_sale_in_polygons))
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[points_for_sale_in_polygons['CVE_ENT']=='09'] 
points_for_rent_in_polygons 	=	points_for_rent_in_polygons[points_for_rent_in_polygons['CVE_ENT']=='09']

print("depas en cdmx a la venta con ambs coord:",len(points_for_sale_in_polygons))
print("depas en cdmx a la renta con ambs coord:",len(points_for_rent_in_polygons))

#rescue points without coordinates

#rescue only points with at least one coordinate is empty
data_sale 						=	properties_for_sale[(properties_for_sale['address_state']=='DISTRITO_FEDERAL')]
data_sale 						=	data_sale[(data_sale['longitud']=='no_lon_data')|(data_sale['latitud']=='no_lat_data')]
points_for_sale_in_polygons  	=	points_for_sale_in_polygons.append(pd.merge(data_sale,polygons,left_on='address_settlement',right_on='Name'))

data_rent 						=	properties_for_rent[(properties_for_rent['address_state']=='DISTRITO_FEDERAL')]
data_rent 						=	data_rent[(data_rent['longitud']=='no_lon_data')|(data_rent['latitud']=='no_lat_data')]
points_for_rent_in_polygons		=	points_for_rent_in_polygons.append(pd.merge(data_rent,polygons,left_on='address_settlement',right_on='Name'))
print("len before:",len(points_for_sale_in_polygons))
print("len before:",len(points_for_rent_in_polygons))

#drop duplicates
points_for_sale_in_polygons 	= 	points_for_sale_in_polygons.drop_duplicates('url')
points_for_rent_in_polygons 	= 	points_for_rent_in_polygons.drop_duplicates('url')

print("len after drop duplicates",len(points_for_sale_in_polygons))
print("len after drop duplicates",len(points_for_rent_in_polygons))
import code; code.interact(local=locals())
#-------------------------III CLEANING & CONDITIONNING DATA


#cleanning age
points_for_sale_in_polygons 	=	tools.cleaning_property_age_values(points_for_sale_in_polygons,age_column_name='age')
points_for_rent_in_polygons 	=	tools.cleaning_property_age_values(points_for_rent_in_polygons,age_column_name='age')


#price conversion
points_for_sale_in_polygons 	=	tools.price_conversion_tool(points_for_sale_in_polygons,price_column_name='price_currency',currency_column_name='currency')
points_for_rent_in_polygons 	=	tools.price_conversion_tool(points_for_rent_in_polygons,price_column_name='price_currency',currency_column_name='currency')


#surface field defined to max(superficie total, superficie construida)
points_for_sale_in_polygons	 	=	tools.surface_field_cleaning_tool(points_for_sale_in_polygons,lotsize_column_name='lot_size',size_column_name='size')
points_for_rent_in_polygons		=	tools.surface_field_cleaning_tool(points_for_rent_in_polygons,lotsize_column_name='lot_size',size_column_name='size')

#pointInPolys['size'] 			=	[max(sup_t,sup_c) for sup_t,sup_c in zip(pointInPolys['lot_size'],pointInPolys['size'])]

print('before price&surface not nulls',len(points_for_sale_in_polygons))
#filter no nulls
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[points_for_sale_in_polygons['price'].notnull()]
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[(points_for_sale_in_polygons['size']>0) & (points_for_sale_in_polygons['price']>0)]
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[points_for_sale_in_polygons['size'].notnull()]

points_for_rent_in_polygons 	=	points_for_rent_in_polygons[points_for_rent_in_polygons['price'].notnull()]
points_for_rent_in_polygons 	=	points_for_rent_in_polygons[(points_for_rent_in_polygons['size']>0) & (points_for_rent_in_polygons['price']>0)]
points_for_rent_in_polygons 	=	points_for_rent_in_polygons[points_for_rent_in_polygons['size'].notnull()]



#----------------------------------
# calculations over single points
#----------------------------------
points_for_sale_in_polygons['price_per_size_unit']		= points_for_sale_in_polygons['price']/points_for_sale_in_polygons['size']
points_for_rent_in_polygons['price_per_size_unit']		= points_for_rent_in_polygons['price']/points_for_rent_in_polygons['size']

points_for_sale_in_polygons['price_per_lot_size_unit']	= points_for_sale_in_polygons['price']/points_for_sale_in_polygons['lot_size']
points_for_rent_in_polygons['price_per_lot_size_unit']	= points_for_rent_in_polygons['price']/points_for_rent_in_polygons['lot_size']


#Extra features & amenities
#points_for_sale_in_polygons['has_extra_features']	=	[True if (has_laundry_room*has_storage_in_unit*has_air_conditioning*has_heating*has_maids_room*has_visitors_parking) else False for has_laundry_room,has_storage_in_unit,has_air_conditioning,has_heating,has_maids_room,has_visitors_parking  in zip(points_for_sale_in_polygons['has_laundry_room'],points_for_sale_in_polygons['has_storage_in_unit'],points_for_sale_in_polygons['has_air_conditioning'],points_for_sale_in_polygons['has_heating'],points_for_sale_in_polygons['has_maids_room'],points_for_sale_in_polygons['has_visitors_parking'])]
points_for_sale_in_polygons['has_extra_features']	=	[True if sum([has_laundry_room,has_storage_in_unit,has_air_conditioning,has_heating,has_maids_room,has_visitors_parking])>=2 else False for has_laundry_room,has_storage_in_unit,has_air_conditioning,has_heating,has_maids_room,has_visitors_parking  in zip(points_for_sale_in_polygons['has_laundry_room'],points_for_sale_in_polygons['has_storage_in_unit'],points_for_sale_in_polygons['has_air_conditioning'],points_for_sale_in_polygons['has_heating'],points_for_sale_in_polygons['has_maids_room'],points_for_sale_in_polygons['has_visitors_parking'])]
#points_for_sale_in_polygons['has_amenities']		=	[True if (has_gym*has_yard*has_party_room*has_grilling_area*has_pool_area*has_tennis_court*has_movie_theater*has_playground*has_garden) else False for has_gym,has_yard,has_party_room,has_grilling_area,has_pool_area,has_tennis_court,has_movie_theater,has_playground,has_garden  in zip(points_for_sale_in_polygons['has_gym'],points_for_sale_in_polygons['has_yard'],points_for_sale_in_polygons['has_party_room'],points_for_sale_in_polygons['has_grilling_area'],points_for_sale_in_polygons['has_pool_area'],points_for_sale_in_polygons['has_tennis_court'],points_for_sale_in_polygons['has_movie_theater'],points_for_sale_in_polygons['has_playground'],points_for_sale_in_polygons['has_garden'])]
points_for_sale_in_polygons['has_amenities']		=	[True if sum([has_gym,has_yard,has_party_room,has_grilling_area,has_pool_area,has_tennis_court,has_movie_theater,has_playground,has_garden])>=2 else False for has_gym,has_yard,has_party_room,has_grilling_area,has_pool_area,has_tennis_court,has_movie_theater,has_playground,has_garden  in zip(points_for_sale_in_polygons['has_gym'],points_for_sale_in_polygons['has_yard'],points_for_sale_in_polygons['has_party_room'],points_for_sale_in_polygons['has_grilling_area'],points_for_sale_in_polygons['has_pool_area'],points_for_sale_in_polygons['has_tennis_court'],points_for_sale_in_polygons['has_movie_theater'],points_for_sale_in_polygons['has_playground'],points_for_sale_in_polygons['has_garden'])]


#-------------------------V SPECIAL FILTERS
#----------------------------------
# Auctions
#----------------------------------
#from url
print('before auctions',len(points_for_sale_in_polygons))
points_for_sale_in_polygons		=	points_for_sale_in_polygons[~points_for_sale_in_polygons['url'].str.contains("remate")]
points_for_rent_in_polygons		=	points_for_rent_in_polygons[~points_for_rent_in_polygons['url'].str.contains("remate")]

#from description @TODO

#----------------------------------
# remove otrher property types
#----------------------------------
#from url
print('before casas',len(points_for_sale_in_polygons))
points_for_sale_in_polygons		=	points_for_sale_in_polygons[~points_for_sale_in_polygons['url'].str.contains("casa")]
points_for_rent_in_polygons		=	points_for_rent_in_polygons[~points_for_rent_in_polygons['url'].str.contains("casa")]


#from description @TODO

#----------------------------------
# only surface in [30,800]
#----------------------------------
print('before surface',len(points_for_sale_in_polygons))
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[(points_for_sale_in_polygons['size']>=30)&(points_for_sale_in_polygons['size']<=800)]

#----------------------------------
# only price in [1M,100M]
#----------------------------------
print('before price',len(points_for_sale_in_polygons))
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[(points_for_sale_in_polygons['price']>=1000000)&(points_for_sale_in_polygons['price']<=100000000)]

#----------------------------------
# only price per m2 in [10K,200K]
#----------------------------------
print('before price per size unit',len(points_for_sale_in_polygons))
points_for_sale_in_polygons 	=	points_for_sale_in_polygons[(points_for_sale_in_polygons['price_per_size_unit']>=10000)&(points_for_sale_in_polygons['price_per_size_unit']<=200000)]

#----------------------------------
# 
#----------------------------------


#points_for_sale_in_polygons subset with age info
points_for_sale_in_polygons_with_age = points_for_sale_in_polygons[points_for_sale_in_polygons['age']!='no_age_info']
print("cleaning data done")
#-------------------------VI CALCULATIONS 


#----------------------------------
#calculations over polygons
#----------------------------------
#sample size
polygons['sample_size']				=	[int(points_for_sale_in_polygons[points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id]['price_per_size_unit'].count()) for polygon_id in polygons['POLYGON_INDEX']]

#median home value
polygons['median_price_currency']	=	[points_for_sale_in_polygons[points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id]['price'].median() for polygon_id in polygons['POLYGON_INDEX']]


#size
polygons['median_size']				=	[points_for_sale_in_polygons[points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id]['size'].median() for polygon_id in polygons['POLYGON_INDEX']]

#price
polygons['average_price_per_size_unit']			= [points_for_sale_in_polygons[points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id]['price_per_size_unit'].mean() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit']			= [points_for_sale_in_polygons[points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_new']		=	  [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]	
polygons['median_price_per_size_unit_existing']	=	  [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]	


#seguridad
polygons['median_price_per_size_unit_without_security'] 		=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_security']==False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_security']    		=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_security']!=False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_security_new'] 		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_security']==False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_security_existing']   =	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_security']==False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_without_security_new'] 	=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_security']!=False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_security_existing']=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_security']!=False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]


#parking
polygons['median_price_per_size_unit_without_parking'] 			=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['n_parking_spaces']=='no_parking_notice')]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_parking']    			=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['n_parking_spaces']!='no_parking_notice')]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_without_parking_new'] 		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['n_parking_spaces']=='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_parking_existing'] =	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['n_parking_spaces']=='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_parking_new'] 		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['n_parking_spaces']!='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_parking_existing']    =	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['n_parking_spaces']!='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

#elevator
polygons['median_price_per_size_unit_without_elevator'] 		=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_elevator']==False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_elevator']    		=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_elevator']!=False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_elevator_new'] 		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']==False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_elevator_existing']   =	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']==False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_without_elevator_new'] 	=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']!=False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_elevator_existing']=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']!=False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

#parking&elevator
polygons['median_price_per_size_unit_with_elevator_and_parking']    		=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_elevator']!=False)&(points_for_sale_in_polygons['n_parking_spaces']!='no_parking_notice')]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_elevator_and_parking_new']		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']!=False)&(points_for_sale_in_polygons_with_age['n_parking_spaces']!='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_with_elevator_and_parking_existing']	=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_elevator']!=False)&(points_for_sale_in_polygons_with_age['n_parking_spaces']!='no_parking_notice')&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

#Extra_features
polygons['median_price_per_size_unit_with_extra_features'] 		= [points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_extra_features']==True)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_extra_features'] 	= [points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_extra_features']==False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_extra_features_new'] 		= [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_extra_features']==True)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_extra_features_new'] 	= [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_extra_features']==False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_extra_features_existing'] 	= [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_extra_features']==True)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_extra_features_existing'] 	= [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_extra_features']==False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

#Amenities
polygons['median_price_per_size_unit_with_amenities']				=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_amenities']==True)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_amenities'] 			=	[points_for_sale_in_polygons[(points_for_sale_in_polygons['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons['has_amenities']==False)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_amenities_new']			=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_amenities']==True)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_amenities_new'] 		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_amenities']==False)&(points_for_sale_in_polygons_with_age['age']<=5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]

polygons['median_price_per_size_unit_with_amenities_existing']		=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_amenities']==True)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_price_per_size_unit_without_amenities_existing'] 	=	[points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['has_amenities']==False)&(points_for_sale_in_polygons_with_age['age']>5)]['price_per_size_unit'].median() for polygon_id in polygons['POLYGON_INDEX']]


'''
#price_to_rent
polygons['price_to_rent'] = [(rent_price*12.0)/(sale_price) for sale_price,rent_price in zip()]

#baths/bedrooms ratio
#nozerorooms

nozerorooms= pointInPolys[(pointInPolys['n_bedrooms']!='no_bedrooms_notice')]
nozerorooms['n_bedrooms'] = [int(n) if(type(n)==float) else n for n in nozerorooms['n_bedrooms']]
nozerorooms['n_bedrooms'] = [int(n.replace('.0','')) if(type(n)==str) else n for n in nozerorooms['n_bedrooms']]
nozerorooms['n_bedrooms']= nozerorooms['n_bedrooms'].astype(int)
nozerorooms= nozerorooms[(nozerorooms['n_bedrooms']>=0)]

bed_bath= nozerorooms[nozerorooms['n_bathrooms']!='no_baths_notice']
bed_bath['n_bathrooms'] = [int(n) if(type(n)==float) else n for n in bed_bath['n_bathrooms']]
bed_bath['n_bathrooms'] = [int(n.replace('.0','')) if(type(n)==str) else n for n in bed_bath['n_bathrooms']]
bed_bath['n_bathrooms']=bed_bath['n_bathrooms'].astype(int)
bed_bath=bed_bath[(bed_bath['n_bathrooms']>=0)]

#baths/bedrooms ratio
bed_bath['median_bedrooms_bathrooms_ratio']= bed_bath['n_bathrooms']/bed_bath['n_bedrooms'] 
polygons['median_bedrooms_bathrooms_ratio']=[bed_bath[bed_bath['POLYGON_INDEX']== polygon_id]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in polygons['POLYGON_INDEX']]

bed_bath_age_info= bed_bath[bed_bath['age']!='no_age_info']
polygons['median_bedrooms_bathrooms_ratio_new']=[bed_bath_age_info[(bed_bath_age_info['POLYGON_INDEX']== polygon_id)&(bed_bath_age_info['age']<=5)]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in polygons['POLYGON_INDEX']]
polygons['median_bedrooms_bathrooms_ratio_existing']=[bed_bath_age_info[(bed_bath_age_info['POLYGON_INDEX']== polygon_id)&(bed_bath_age_info['age']>5)]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in polygons['POLYGON_INDEX']]

print("bed_bath done")



#polygons_data 						 = polygons_data[polygons_data.notnull()]


#age
polygons['median_age']			 							= [points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)]['age'].median() for polygon_id in polygons['POLYGON_INDEX']]

# to get categories name: pd.cut(pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['age']!='no_age_info')]['age'],np.arange(0,100,10),retbins=True)[0].values.describe()
#or: pd.cut(pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['age']!='no_age_info')]['age'],np.arange(0,100,10),retbins=True)[0].values.categories

age_groups 							=  np.array([-5,0,5,10,15,20,25,30,40,50,60,100])#np.arange(0,100,10)
polygons['age_histogram_values']    = [pd.cut(points_for_sale_in_polygons_with_age[(points_for_sale_in_polygons_with_age['POLYGON_INDEX']== polygon_id)&(points_for_sale_in_polygons_with_age['age']>-5)&(points_for_sale_in_polygons_with_age['age']<100)]['age'],age_groups,retbins=True)[0].values.describe()['counts'].ravel() for polygon_id in polygons['POLYGON_INDEX']]
#checar que todos  los values set tienen mismo tamano
polygons['age_histogram']     		= [{'-5 to 0 years':values_set[0],
										'0 to 5 years':values_set[1],
										'5 to 10 years':values_set[2],
										'10 to 15 years':values_set[3],
										'15 to 20 years':values_set[4],
										'20 to 25 years':values_set[5],
										'25 to 30 years':values_set[6],
										'30 to 40 years':values_set[7],
										'40 to 50 years':values_set[8],
										'50 to 60 years':values_set[9],
										'60 to 100 years':values_set[10]} for values_set in polygons['age_histogram_values']]

polygons['age_histogram_untill_0_years'] 	= [int(values['-5 to 0 years']) for values in polygons['age_histogram']]
polygons['age_histogram_0_to_5_years']  	= [int(values['0 to 5 years']) for values in polygons['age_histogram']]
polygons['age_histogram_5_to_10_years'] 	= [int(values['5 to 10 years']) for values in polygons['age_histogram']]
polygons['age_histogram_10_to_15_years'] 	= [int(values['10 to 15 years']) for values in polygons['age_histogram']]
polygons['age_histogram_15_to_20_years'] 	= [int(values['15 to 20 years']) for values in polygons['age_histogram']]
polygons['age_histogram_20_to_25_years'] 	= [int(values['20 to 25 years']) for values in polygons['age_histogram']]
polygons['age_histogram_25_to_30_years'] 	= [int(values['25 to 30 years']) for values in polygons['age_histogram']]
polygons['age_histogram_30_to_40_years'] 	= [int(values['30 to 40 years']) for values in polygons['age_histogram']]
polygons['age_histogram_40_to_50_years'] 	= [int(values['40 to 50 years']) for values in polygons['age_histogram']]
polygons['age_histogram_50_to_60_years'] 	= [int(values['50 to 60 years']) for values in polygons['age_histogram']]
polygons['age_histogram_60_to_100_years'] 	= [int(values['60 to 100 years']) for values in polygons['age_histogram']]

'''
#import code; code.interact(local=locals())




#-------------------------VII SAVE FILES
#-----dashbord data
'''
#truehome POLYGON_INDEXs
POLYGON_INDEXs = ['11510','11530','11540','11550','11560','11800','11550','11560','11580','11590','11300','11590','11520','11529','11200','11200','11000','11850','11570','11590','11320','11500','11000','11560','11510','11510','11540','11530','11580','11370','11650','11600','11600','03103','03104','03100','03810','03840','03100','03000','03900','03720','03020','03023','03600','03710','03800','03730','03920','03740','03200','03023','01020']
polygons_th = polygons[polygons['POLYGON_INDEX'].isin(POLYGON_INDEXs)]
polygons_th.to_csv('real_state_indicators_th_zone.csv')

print("csv for dashbord done")	
'''

#------offers for sourcing
#median price per size unit currency
points_for_sale_in_polygons['median_price_per_size_unit_settlement'] 	        = [polygons[polygons['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit'].unique()[0] for POLYGON_INDEX in points_for_sale_in_polygons['POLYGON_INDEX']]
#median price per size unit currency NEW
points_for_sale_in_polygons['median_price_per_size_unit_settlement_new']      = [polygons[polygons['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit_new'].unique()[0] for POLYGON_INDEX in points_for_sale_in_polygons['POLYGON_INDEX']]
#median price per size unit currency EXISTING
points_for_sale_in_polygons['median_price_per_size_unit_settlement_existing'] = [polygons[polygons['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit_existing'].unique()[0] for POLYGON_INDEX in points_for_sale_in_polygons['POLYGON_INDEX']]


#(smart)price delta
points_for_sale_in_polygons['delta_price'] 									= [(((price-price_settlement)*100.0)/price_settlement) if age=='no_age_info' else 'calculate' for price_settlement,price,age in zip(points_for_sale_in_polygons['median_price_per_size_unit_settlement'],points_for_sale_in_polygons['price_per_size_unit'],points_for_sale_in_polygons['age'])]
points_for_sale_in_polygons['delta_price'] 									= [(((price-price_settlement_new)*100)/price_settlement_new) if delta_price=='calculate' and age<=5 else delta_price for delta_price,price_settlement_new,price,age  in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['median_price_per_size_unit_settlement_new'],points_for_sale_in_polygons['price_per_size_unit'],points_for_sale_in_polygons['age'])]
points_for_sale_in_polygons['delta_price'] 									= [(((price-price_settlement_existing)*100)/price_settlement_existing) if delta_price=='calculate' and age>5 else delta_price for delta_price,price_settlement_existing,price,age  in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['median_price_per_size_unit_settlement_existing'],points_for_sale_in_polygons['price_per_size_unit'],points_for_sale_in_polygons['age'])]


#redlight
points_for_sale_in_polygons['semaforo']										= ['amarillo' if delta_price <=10.0 and delta_price>=-10.0 else 'undefined' for delta_price in points_for_sale_in_polygons['delta_price']]
points_for_sale_in_polygons['semaforo']										= ['naranja' if delta_price>=-20.0 and delta_price<-10.0 else semaforo for delta_price,semaforo in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['semaforo'])]
points_for_sale_in_polygons['semaforo']										= ['verde' if delta_price >=-50.0 and delta_price<-20.0 else semaforo for delta_price,semaforo in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['semaforo'])]
points_for_sale_in_polygons['semaforo']										= ['subvaluado' if delta_price <-50.0  else semaforo for delta_price,semaforo in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['semaforo'])]
points_for_sale_in_polygons['semaforo']										= ['sobrevaluado' if delta_price >10.0  else semaforo for delta_price,semaforo in zip(points_for_sale_in_polygons['delta_price'],points_for_sale_in_polygons['semaforo'])]

'''
#filters
pointInPolys_sourcing 			= pointInPolys
pointInPolys_sourcing 			= pointInPolys_sourcing[pointInPolys_sourcing['price_per_size_unit']>10000]
pointInPolys_sourcing 			= pointInPolys_sourcing[(pointInPolys_sourcing['size']<1000)&(pointInPolys_sourcing['lot_size']<1000)]
pointInPolys_sourcing 			= pointInPolys_sourcing[(pointInPolys_sourcing['price']>800000)]
pointInPolys_sourcing['is_old'] = ['add' if((type(age_value)==int and age_value>5)or(type(age_value)==str and age_value=='no_age_info')) else 'no_add' for age_value in pointInPolys_sourcing['age']]
pointInPolys_sourcing 			= pointInPolys_sourcing[pointInPolys_sourcing['is_old']=='add']
#select columns to save on csv
'''
import code; code.interact(local=locals())
columns_selection 												=	['url','NOM_MUN','Name',
																	'age','size','price',
																	'price_per_size_unit',
																	'median_price_per_size_unit_settlement',
																	'median_price_per_size_unit_settlement_new',
																	'median_price_per_size_unit_settlement_existing',
																	'delta_price','semaforo']
points_for_sale_in_polygons_sourcing							=	points_for_sale_in_polygons[columns_selection]
#update names of columns
points_for_sale_in_polygons_sourcing.columns 					=	['url','delegacion','colonia',
																	'antiguedad','superficie construida en m2','precio total en pesos',
																	'precio de m2',
																	'precio mediano de m2 de la colonia',
																	'precio mediano de m2 de la colonia (nuevos)',
																	'precio mediano de m2 de la colonia (usados)',
																	'delta','semaforo']


points_for_sale_in_polygons_sourcing.to_csv('sourcing.csv')
#pointInPolys.to_csv('sourcing.csv')
points_for_sale_in_polygons.to_csv('sourcing_full.csv')

print("csv for sourcing done")

#------ indicators csv
polygons.to_csv('real_state_indicators.csv')

print("indicators done")


#import code; code.interact(local=locals())
#-----polygons

#str conversions to save histogram values correctly on shp
polygons['age_histogram'] = polygons['age_histogram'].astype(str)
polygons['age_histogram_values'] = polygons['age_histogram_values'].astype(str)

#to 
polygons = polygons.set_index('POLYGON_INDEX')
polygons.to_file('real_state_calculations_by_settlement.shp')



#geopandas geojson driver does not support update filename
try: 
    os.remove('real_state_calculations_by_settlement.geojson')
except OSError:
    pass
polygons.to_file('real_state_calculations_by_settlement.geojson', driver='GeoJSON')
import code; code.interact(local=locals())


