prompt="""
You are an agent which analyze text of a pdf file content and return only json for the information required.
This is an agro-advisory data PDF. You need to extract the following things mentioned in pydantic classes. Name of classes are keys. And values are described in class.

from pydantic import BaseModel, Field
from typing import Dict, List, Tuple

class weather_details(BaseModel):
    rainfall: int
    t_max: int              # maximum temperature
    t_min: int              # minimum temperature
    rh_max: int             # relative humidity max
    rh_min: int             # relative humidity min
    wind_speed: int         # wind speed in kmph
    wind_direction: int     # wind direction in degrees
    cloud_cover: int        # cloud cover

    # extract these details from the weather table and keep these values for each tuple of date as key:value pair (keys are date and values are tuples with above value)
    # every tuple have above variables as keys and values from tables
    # leave values empty if not available

class names_of_crops(BaseModel):
    List[str]   # return Name of crops/animal husbandry/poultry/fishing for which further info is present (lower case)

class general_advidory(BaseModel):
    str
    # Extracting general advice about the weather and cropping from the pdf tagged as 'general advice' 

class crops_data(BaseModeal):
    crops: dict
    # dictionary having info of extracting the crops/animal husbandry/poultry/fishing details from it and extracting information for each crops/animal husbandry/poultry/fishing from it, 
    # each tagged separately for each crop/subgroup (There should be a distinct finite list of these subgroups)
    # (Keys: each crop name, Value: Should be a dict with only key 'advisory')
    # Keep every point about that subgroup in advisory only
    # keep names of crops in keys same to how you wrote in in names_of_crops 

"""