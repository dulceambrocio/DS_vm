import geopandas
from geopandas.tools import sjoin
import pandas as pd
from shapely.geometry import Point
import datetime
import numpy as np
import os

#[poly_shp["d_cp"].iloc[item] for item in poly_shp.index]

#-------------------------I LOAD FILES
#load offer logs file
polygons_path					=	'settlements_df_truehome_version/'
data 							= 	pd.read_csv('properties_25_26_may_2017.csv',encoding='latin1')
data.columns                    = ['id','url','title','source','extrated_on','property_type','offer_type','offer_id',
                                   'currency','price','age','lot_size','size','n_bathrooms','n_bedrooms','n_parking_spaces',
                                   'address','latitud','longitud','delivered_on','publisher_name','publisher_address',
                                   'publisher_phone','nocnok_id','has_elevator','has_security','has_air_conditioning',
                                   'has_heating','has_laundry_room','has_maids_room','has_storage_in_unit','has_grilling_area',
                                   'has_gym','has_playground','has_party_room','has_pool_area','has_garden','has_yard','has_roof_garden',
                                   'has_movie_theater','has_visitors_parking','has_tennis_court']


#load settlements shapefile
poly_shp  						= 	geopandas.GeoDataFrame.from_file(polygons_path+'settlements_df_truehome_version.shp')
print("crs: ",poly_shp.crs)


#Reproject to epsg:4326
poly_shp 						=	poly_shp.to_crs({'init': 'epsg:4326'})
print("polygons reprojected")

#reset index on polygons
poly_shp 						=	poly_shp.reset_index()
poly_shp 						=	poly_shp.rename(columns={'index': 'POLYGON_INDEX'})	


#load data as shapefile
data 							=	data[data['longitud'].notnull()]#fue necesario para evitar error
data 							=	data[data['latitud'].notnull()]#fue necesario para evitar error
data['latitud']					=	data['latitud'].astype(float)
data['longitud']				= 	data['longitud'].astype(float)
geometry 				    	=	[Point(xy) for xy in zip(data.longitud, data.latitud)]
data 							=	data.drop(['longitud', 'latitud'], axis=1)


crs 							=	poly_shp.crs

point_shp				    	=	geopandas.GeoDataFrame(data, crs=crs, geometry=geometry)
print("files loaded")

#-------------------------II FILTERS

#remove duplicates

#remove accents in name of 
#poly_shp['MUN_NAME'] 						= poly_shp['MUN_NAME'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

#solo departamentos
point_shp 									=	point_shp[point_shp['property_type']=='departamento']

print("filters done")
#-------------------------IV SPATIAL JOIN
pointInPolys 								= 	sjoin(point_shp, poly_shp, how='left')


#filter
pointInPolys 								=	pointInPolys[pointInPolys['ST_NAME']=='CDMX'] 

print("spatial join done")
#-------------------------III CLEANING DATA

#cleanning age
pointInPolys['age']     	= pointInPolys['age'].str.extract('(\d+)')
pointInPolys['age']     	= pointInPolys['age'].fillna('no_age_info')
pointInPolys['age']			= [int(age) if age!='no_age_info' else age for age in pointInPolys['age']]
now											= datetime.datetime.now()
current_year 								= now.year
#age correction: some fields contains year built instead of age
pointInPolys['age']     	= [int(current_year-age) if age!='no_age_info' and age>1700 else age for age in pointInPolys['age']]

#usd prices
pointInPolys['price'] 	    = pointInPolys['price'].str.replace(',','').str.extract('(\d+)').astype(int)
pointInPolys['price']		= [cantidad*18.7 if moneda=='USD' else cantidad for cantidad,moneda in zip(pointInPolys['price'],pointInPolys['currency'])]

#surface field defined to max(superficie total, superficie construida)
pointInPolys['lot_size']      				= pointInPolys['lot_size'].fillna(0).astype(int)#.str.replace('m2','').str.replace('.','').str.extract('(\d+)').fillna(0).astype(int)
pointInPolys['size'] 						= pointInPolys['size'].fillna(0).astype(int)#.str.replace('m2','').str.replace('.','').str.extract('(\d+)').fillna(0).astype(int)





pointInPolys['size'] 					= [max(sup_t,sup_c) for sup_t,sup_c in zip(pointInPolys['lot_size'],pointInPolys['size'])]

#filter no nulls
pointInPolys 								=	pointInPolys[pointInPolys['price'].notnull()]
pointInPolys 								=	pointInPolys[(pointInPolys['size']>0) & (pointInPolys['price']>0)]
pointInPolys 								=	pointInPolys[pointInPolys['size'].notnull()]


print("cleanind data done")
#-------------------------VI CALCULATIONS 

#calculations over single points
pointInPolys['price_per_size_unit_currency']						 = pointInPolys['price']/pointInPolys['size']

#Exta FEATURES 
'''
as Exta FEATURES we take into account: 

laundry_room
storage_in_unit
air_conditioning
heating
maids_room
visitors_parking
'''
pointInPolys['has_laundry_room']     		= pointInPolys['has_laundry_room'].fillna(False)
pointInPolys['has_storage_in_unit']     	= pointInPolys['has_storage_in_unit'].fillna(False)
pointInPolys['has_air_conditioning']     	= pointInPolys['has_air_conditioning'].fillna(False)
pointInPolys['has_heating']     			= pointInPolys['has_heating'].fillna(False)
pointInPolys['has_maids_room']     			= pointInPolys['has_maids_room'].fillna(False)
pointInPolys['has_visitors_parking']     	= pointInPolys['has_visitors_parking'].fillna(False)

pointInPolys['has_laundry_room']     		= [True if val=='Si' else val  for val in pointInPolys['has_laundry_room']]
pointInPolys['has_storage_in_unit']     	= [True if val=='Si' else val  for val in pointInPolys['has_storage_in_unit']]
pointInPolys['has_air_conditioning']     	= [True if val=='Si' else val  for val in pointInPolys['has_air_conditioning']]
pointInPolys['has_heating']     			= [True if val=='Si' else val  for val in pointInPolys['has_heating']]
pointInPolys['has_maids_room']     			= [True if val=='Si' else val  for val in pointInPolys['has_maids_room']]
pointInPolys['has_visitors_parking']     	= [True if val=='Si' else val  for val in pointInPolys['has_visitors_parking']]


#AMENITIES
'''
as AMENITIES we take into account: 

gym
roof_garden
yard
party_room
grilling_area
pool_area
tennis_court
movie_theater
playground
garden
'''
pointInPolys['has_gym']     				= pointInPolys['has_gym'].fillna(False)
pointInPolys['has_roof_garden']     		= pointInPolys['has_roof_garden'].fillna(False)
pointInPolys['has_yard']     				= pointInPolys['has_yard'].fillna(False)
pointInPolys['has_party_room']     			= pointInPolys['has_party_room'].fillna(False)
pointInPolys['has_grilling_area']     		= pointInPolys['has_grilling_area'].fillna(False)
pointInPolys['has_pool_area']     			= pointInPolys['has_pool_area'].fillna(False)
pointInPolys['has_tennis_court']     		= pointInPolys['has_tennis_court'].fillna(False)
pointInPolys['has_movie_theater']     		= pointInPolys['has_movie_theater'].fillna(False)
pointInPolys['has_playground']     			= pointInPolys['has_playground'].fillna(False)
pointInPolys['has_garden']     				= pointInPolys['has_garden'].fillna(False)

pointInPolys['has_gym']     				= [True if val=='Si' else val  for val in pointInPolys['has_gym']]
pointInPolys['has_roof_garden']     		= [True if val=='Si' else val  for val in pointInPolys['has_roof_garden']]
pointInPolys['has_yard']     				= [True if val=='Si' else val  for val in pointInPolys['has_yard']]
pointInPolys['has_party_room']     			= [True if val=='Si' else val  for val in pointInPolys['has_party_room']]
pointInPolys['has_grilling_area']     		= [True if val=='Si' else val  for val in pointInPolys['has_grilling_area']]
pointInPolys['has_pool_area']     			= [True if val=='Si' else val  for val in pointInPolys['has_pool_area']]
pointInPolys['has_tennis_court']     		= [True if val=='Si' else val  for val in pointInPolys['has_tennis_court']]
pointInPolys['has_movie_theater']     		= [True if val=='Si' else val  for val in pointInPolys['has_movie_theater']]
pointInPolys['has_playground']     			= [True if val=='Si' else val  for val in pointInPolys['has_playground']]
pointInPolys['has_garden']     				= [True if val=='Si' else val  for val in pointInPolys['has_garden']]


#baths/bedrooms ratio
pointInPolys['n_bathrooms']                 = pointInPolys['n_bathrooms'].fillna('no_baths_notice')
pointInPolys['n_bedrooms']                  = pointInPolys['n_bedrooms'].fillna('no_bedrooms_notice')



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
poly_shp['median_bedrooms_bathrooms_ratio']=[bed_bath[bed_bath['POLYGON_INDEX']== polygon_id]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

bed_bath_age_info= bed_bath[bed_bath['age']!='no_age_info']
poly_shp['median_bedrooms_bathrooms_ratio_new']=[bed_bath_age_info[(bed_bath_age_info['POLYGON_INDEX']== polygon_id)&(bed_bath_age_info['age']<=5)]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_bedrooms_bathrooms_ratio_existing']=[bed_bath_age_info[(bed_bath_age_info['POLYGON_INDEX']== polygon_id)&(bed_bath_age_info['age']>5)]['median_bedrooms_bathrooms_ratio'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

print("bed_bath done")


#calculatiosns over polygons
poly_shp['sample_size']				 						 = [int(pointInPolys[pointInPolys['POLYGON_INDEX']== polygon_id]['price_per_size_unit_currency'].count()) for polygon_id in poly_shp['POLYGON_INDEX']]


#median home value
poly_shp['median_price_currency']			 				 = [pointInPolys[pointInPolys['POLYGON_INDEX']== polygon_id]['price'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
print("median price calculated")

#size
poly_shp['median_size']			 							= [pointInPolys[pointInPolys['POLYGON_INDEX']== polygon_id]['size'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

#price
poly_shp['average_price_per_size_unit_currency']			= [pointInPolys[pointInPolys['POLYGON_INDEX']== polygon_id]['price_per_size_unit_currency'].mean() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency']				= [pointInPolys[pointInPolys['POLYGON_INDEX']== polygon_id]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

#poly_shp_data 						 = poly_shp_data[poly_shp_data.notnull()]

print("median price per size unit calculated")
#precio de m2 nuevo/usado
pointInPolys_age_info										 		=	   pointInPolys[pointInPolys['age']!='no_age_info']					
poly_shp['median_price_per_size_unit_currency_new']			 		=	  [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]	
poly_shp['median_price_per_size_unit_currency_existing']	 		=	  [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]	

#parking
pointInPolys['n_parking_spaces'] 							  =	pointInPolys['n_parking_spaces'].fillna('no_parking_notice')
pointInPolys_age_info['n_parking_spaces'] 				    =	pointInPolys_age_info['n_parking_spaces'].fillna('no_parking_notice')
poly_shp['median_price_per_size_unit_currency_without_parking'] 	=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['n_parking_spaces']=='no_parking_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_parking']    	=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['n_parking_spaces']!='no_parking_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_without_parking_new'] 			= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['n_parking_spaces']=='no_parking_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_parking_existing']    	= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['n_parking_spaces']=='no_parking_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_parking_new'] 				= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['n_parking_spaces']!='no_parking_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_parking_existing']    		= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['n_parking_spaces']!='no_parking_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]


#age
poly_shp['median_age']			 							= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)]['age'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

# to get categories name: pd.cut(pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['age']!='no_age_info')]['age'],np.arange(0,100,10),retbins=True)[0].values.describe()
#or: pd.cut(pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['age']!='no_age_info')]['age'],np.arange(0,100,10),retbins=True)[0].values.categories

age_groups 							=  np.array([-5,0,5,10,15,20,25,30,40,50,60,100])#np.arange(0,100,10)
poly_shp['age_histogram_values']    = [pd.cut(pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['age']>-5)&(pointInPolys_age_info['age']<100)]['age'],age_groups,retbins=True)[0].values.describe()['counts'].ravel() for polygon_id in poly_shp['POLYGON_INDEX']]
#checar que todos  los values set tienen mismo tamano
poly_shp['age_histogram']     		= [{'-5 to 0 years':values_set[0],
										'0 to 5 years':values_set[1],
										'5 to 10 years':values_set[2],
										'10 to 15 years':values_set[3],
										'15 to 20 years':values_set[4],
										'20 to 25 years':values_set[5],
										'25 to 30 years':values_set[6],
										'30 to 40 years':values_set[7],
										'40 to 50 years':values_set[8],
										'50 to 60 years':values_set[9],
										'60 to 100 years':values_set[10]} for values_set in poly_shp['age_histogram_values']]

poly_shp['age_histogram_untill_0_years'] 	= [int(values['-5 to 0 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_0_to_5_years']  	= [int(values['0 to 5 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_5_to_10_years'] 	= [int(values['5 to 10 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_10_to_15_years'] 	= [int(values['10 to 15 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_15_to_20_years'] 	= [int(values['15 to 20 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_20_to_25_years'] 	= [int(values['20 to 25 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_25_to_30_years'] 	= [int(values['25 to 30 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_30_to_40_years'] 	= [int(values['30 to 40 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_40_to_50_years'] 	= [int(values['40 to 50 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_50_to_60_years'] 	= [int(values['50 to 60 years']) for values in poly_shp['age_histogram']]
poly_shp['age_histogram_60_to_100_years'] 	= [int(values['60 to 100 years']) for values in poly_shp['age_histogram']]



# elevator
pointInPolys['has_elevator'] 							             =	pointInPolys['has_elevator'].fillna('no_elevator_notice')
pointInPolys_age_info['has_elevator'] 				                 =	pointInPolys_age_info['has_elevator'].fillna('no_elevator_notice')
poly_shp['median_price_per_size_unit_currency_without_elevator'] =	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_elevator']=='no_elevator_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_elevator']    =	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_elevator']!='no_elevator_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_elevator_new'] 			= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']=='no_elevator_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_elevator_existing']    	= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']=='no_elevator_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_without_elevator_new'] 				= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']!='no_elevator_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_elevator_existing']    		= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']!='no_elevator_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

print("elevator done")

#parking&elevator
poly_shp['median_price_per_size_unit_currency_with_elevator_and_parking']    		  =	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_elevator']!='no_elevator_notice')&(pointInPolys['n_parking_spaces']!='no_parking_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_elevator_and_parking_new']    	  =	[pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']!='no_elevator_notice')&(pointInPolys_age_info['n_parking_spaces']!='no_parking_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_elevator_and_parking_existing']    =	[pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_elevator']!='no_elevator_notice')&(pointInPolys_age_info['n_parking_spaces']!='no_parking_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
print("elevator&parking done")

#seguridad

pointInPolys['has_security'] 							             				  =	pointInPolys['has_security'].fillna('no_security_notice')


pointInPolys_age_info['has_security'] 				                 					=	pointInPolys_age_info['has_security'].fillna('no_security_notice')
poly_shp['median_price_per_size_unit_currency_without_security'] 						=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_security']=='no_security_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_security']    						=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_security']!='no_security_notice')]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_security_new'] 						= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_security']=='no_security_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_with_security_existing']    				= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_security']=='no_security_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_without_security_new'] 					= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_security']!='no_security_notice')&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_security_existing']    			= [pointInPolys_age_info[(pointInPolys_age_info['POLYGON_INDEX']== polygon_id)&(pointInPolys_age_info['has_security']!='no_security_notice')&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]



print("security done")

#Extra_features
pointInPolys['has_extra_features']										= [True if (has_laundry_room*has_storage_in_unit*has_air_conditioning*has_heating*has_maids_room*has_visitors_parking) else False for has_laundry_room,has_storage_in_unit,has_air_conditioning,has_heating,has_maids_room,has_visitors_parking  in zip(pointInPolys['has_laundry_room'],pointInPolys['has_storage_in_unit'],pointInPolys['has_air_conditioning'],pointInPolys['has_heating'],pointInPolys['has_maids_room'],pointInPolys['has_visitors_parking'])]

poly_shp['median_price_per_size_unit_currency_with_extra_features'] 	= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==True)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_extra_features'] 	= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==False)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_extra_features_new'] 			= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==True)&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_extra_features_new'] 			= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==False)&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_extra_features_existing'] 		= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==True)&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_extra_features_existing'] 	= [pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_extra_features']==False)&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

#Amenities
pointInPolys['has_amenities']								   				=	[True if (has_gym*has_yard*has_party_room*has_grilling_area*has_pool_area*has_tennis_court*has_movie_theater*has_playground*has_garden) else False for has_gym,has_yard,has_party_room,has_grilling_area,has_pool_area,has_tennis_court,has_movie_theater,has_playground,has_garden  in zip(pointInPolys['has_gym'],pointInPolys['has_yard'],pointInPolys['has_party_room'],pointInPolys['has_grilling_area'],pointInPolys['has_pool_area'],pointInPolys['has_tennis_court'],pointInPolys['has_movie_theater'],pointInPolys['has_playground'],pointInPolys['has_garden'])]

poly_shp['median_price_per_size_unit_currency_with_amenities']				=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==True)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_amenities'] 			=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==False)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_amenities_new']			=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==True)&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_amenities_new'] 		=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==False)&(pointInPolys_age_info['age']<=5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]

poly_shp['median_price_per_size_unit_currency_with_amenities_existing']		=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==True)&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]
poly_shp['median_price_per_size_unit_currency_without_amenities_existing'] 	=	[pointInPolys[(pointInPolys['POLYGON_INDEX']== polygon_id)&(pointInPolys['has_amenities']==False)&(pointInPolys_age_info['age']>5)]['price_per_size_unit_currency'].median() for polygon_id in poly_shp['POLYGON_INDEX']]




#-------------------------VII SAVE FILES
#-----dashbord data
#truehome POLYGON_INDEXs
POLYGON_INDEXs = ['11510','11530','11540','11550','11560','11800','11550','11560','11580','11590','11300','11590','11520','11529','11200','11200','11000','11850','11570','11590','11320','11500','11000','11560','11510','11510','11540','11530','11580','11370','11650','11600','11600','03103','03104','03100','03810','03840','03100','03000','03900','03720','03020','03023','03600','03710','03800','03730','03920','03740','03200','03023','01020']
poly_shp_th = poly_shp[poly_shp['POLYGON_INDEX'].isin(POLYGON_INDEXs)]
poly_shp_th.to_csv('real_state_indicators_th_zone.csv')

print("csv for dashbord done")	


#------offers for sourcing
#median price per size unit currency
pointInPolys['median_price_per_size_unit_currency_settlement'] 	        = [poly_shp[poly_shp['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit_currency'].unique()[0] for POLYGON_INDEX in pointInPolys['POLYGON_INDEX']]
#median price per size unit currency NEW
pointInPolys['median_price_per_size_unit_currency_settlement_new']      = [poly_shp[poly_shp['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit_currency_new'].unique()[0] for POLYGON_INDEX in pointInPolys['POLYGON_INDEX']]
#median price per size unit currency EXISTING
pointInPolys['median_price_per_size_unit_currency_settlement_existing'] = [poly_shp[poly_shp['POLYGON_INDEX']==POLYGON_INDEX]['median_price_per_size_unit_currency_existing'].unique()[0] for POLYGON_INDEX in pointInPolys['POLYGON_INDEX']]


#(smart)price delta
pointInPolys['delta_price'] 									= [(((price-price_settlement)*100.0)/price_settlement) if age=='no_age_info' else 'calculate' for price_settlement,price,age in zip(pointInPolys['median_price_per_size_unit_currency_settlement'],pointInPolys['price_per_size_unit_currency'],pointInPolys['age'])]
pointInPolys['delta_price'] 									= [(((price-price_settlement_new)*100)/price_settlement_new) if delta_price=='calculate' and age<=5 else delta_price for delta_price,price_settlement_new,price,age  in zip(pointInPolys['delta_price'],pointInPolys['median_price_per_size_unit_currency_settlement_new'],pointInPolys['price_per_size_unit_currency'],pointInPolys['age'])]
pointInPolys['delta_price'] 									= [(((price-price_settlement_existing)*100)/price_settlement_existing) if delta_price=='calculate' and age>5 else delta_price for delta_price,price_settlement_existing,price,age  in zip(pointInPolys['delta_price'],pointInPolys['median_price_per_size_unit_currency_settlement_existing'],pointInPolys['price_per_size_unit_currency'],pointInPolys['age'])]


#redlight
pointInPolys['semaforo']										= ['amarillo' if delta_price <=10.0 and delta_price>=-10.0 else 'undefined' for delta_price in pointInPolys['delta_price']]
pointInPolys['semaforo']										= ['naranja' if delta_price>=-20.0 and delta_price<-10.0 else semaforo for delta_price,semaforo in zip(pointInPolys['delta_price'],pointInPolys['semaforo'])]
pointInPolys['semaforo']										= ['verde' if delta_price >=-50.0 and delta_price<-20.0 else semaforo for delta_price,semaforo in zip(pointInPolys['delta_price'],pointInPolys['semaforo'])]
pointInPolys['semaforo']										= ['subvaluado' if delta_price <-50.0  else semaforo for delta_price,semaforo in zip(pointInPolys['delta_price'],pointInPolys['semaforo'])]
pointInPolys['semaforo']										= ['sobrevaluado' if delta_price >10.0  else semaforo for delta_price,semaforo in zip(pointInPolys['delta_price'],pointInPolys['semaforo'])]


#filters
pointInPolys_sourcing 			= pointInPolys
pointInPolys_sourcing 			= pointInPolys_sourcing[pointInPolys_sourcing['price_per_size_unit_currency']>10000]
pointInPolys_sourcing 			= pointInPolys_sourcing[(pointInPolys_sourcing['size']<1000)&(pointInPolys_sourcing['lot_size']<1000)]
pointInPolys_sourcing 			= pointInPolys_sourcing[(pointInPolys_sourcing['price']>800000)]
pointInPolys_sourcing['is_old'] = ['add' if((type(age_value)==int and age_value>5)or(type(age_value)==str and age_value=='no_age_info')) else 'no_add' for age_value in pointInPolys_sourcing['age']]
pointInPolys_sourcing 			= pointInPolys_sourcing[pointInPolys_sourcing['is_old']=='add']
#select columns to save on csv

columns_selection 												= ['url','NOM_MUN','Name',
																	'age','size','price',
																	'price_per_size_unit_currency',
																	'median_price_per_size_unit_currency_settlement',
																	'median_price_per_size_unit_currency_settlement_new',
																	'median_price_per_size_unit_currency_settlement_existing',
																	'delta_price','semaforo']
pointInPolys_sourcing = pointInPolys_sourcing[columns_selection]
#update names of columns
pointInPolys_sourcing.columns 									= ['url','delegacion','colonia',
																	'antiguedad','superficie construida en m2','precio total en pesos',
																	'precio de m2',
																	'precio mediano de m2 de la colonia',
																	'precio mediano de m2 de la colonia (nuevos)',
																	'precio mediano de m2 de la colonia (usados)',
																	'delta','semaforo']


pointInPolys_sourcing.to_csv('sourcing.csv')
#pointInPolys.to_csv('sourcing.csv')
pointInPolys.to_csv('sourcing_full.csv')

print("csv for sourcing done")

#------ indicators csv
poly_shp.to_csv('real_state_indicators.csv')

print("indicators done")


#import code; code.interact(local=locals())
#-----polygons

#str conversions to save histogram values correctly on shp
poly_shp['age_histogram'] = poly_shp['age_histogram'].astype(str)
poly_shp['age_histogram_values'] = poly_shp['age_histogram_values'].astype(str)

#to 
poly_shp = poly_shp.set_index('POLYGON_INDEX')
poly_shp.to_file('real_state_calculations_by_settlement.shp')



#geopandas geojson driver does not support update filename
try: 
    os.remove('real_state_calculations_by_settlement.geojson')
except OSError:
    pass
poly_shp.to_file('real_state_calculations_by_settlement.geojson', driver='GeoJSON')
import code; code.interact(local=locals())


