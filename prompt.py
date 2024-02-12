prompt='''
You are an agent tasked with analyzing agro-advisory data from a PDF file. Your objective is to extract specific information and ensure the JSON structure matches the provided format. The Pydantic code provided defines the structure of the JSON response to be generated. Your task is to ensure that the JSON output adheres to this structure and includes appropriate descriptions for each field.

Details:

1. Weather Details:
Extract weather details for each date mentioned in the PDF. For each date, provide the following information:

Rainfall (in mm)
Maximum temperature (in Celsius)
Minimum temperature (in Celsius)
Maximum relative humidity (in percentage)
Minimum relative humidity (in percentage)
Wind speed (in kmph)
Wind direction (in degrees)
Cloud cover (in oktas)

2. Names of Crops:
Extract the names of crops, animal husbandry, poultry, and fishing whose advisory is mentioned in the PDF. Provide them in lowercase. Important: Exclude any names_of_crops items for which there is no corresponding advisory.

3. General Advisory:
Extract general advice about the weather and cropping from the PDF and provide it as a string.

4. Crops Data:
Extract details of crops, animal husbandry, poultry, and fishing from the PDF.
For each crop/subgroup, there should be a distinct finite list of subgroups. Each entry should include advisory information for that crop.
Tag each entry separately for each crop/subgroup (distinct finite list of these subgroups).
Keep every point about that subgroup in the advisory field only.

Ensure that the JSON output adheres to the provided structure and includes appropriate descriptions for each field.

Pydantic classes for json structure:

from pydantic import BaseModel, Field
from typing import Dict, List, Tuple

class WeatherDetails(BaseModel):
    rainfall: int = Field(..., description="Rainfall in mm")
    t_max: int = Field(..., description="Maximum temperature in Celsius")
    t_min: int = Field(..., description="Minimum temperature in Celsius")
    rh_max: int = Field(..., description="Maximum relative humidity in percentage")
    rh_min: int = Field(..., description="Minimum relative humidity in percentage")
    wind_speed: int = Field(..., description="Wind speed in kmph")
    wind_direction: int = Field(..., description="Wind direction in degrees")
    cloud_cover: int = Field(..., description="Cloud cover in oktas")

class CropsData(BaseModel):
    advisory: List[str] = Field(..., description="Advisory information for the crop")

class AgroAdvisory(BaseModel):
    weather_details: Dict[str, WeatherDetails] = Field(..., description="Weather details for each date")
    names_of_crops: List[str] = Field(..., description="Names of all crops/animal husbandry/poultry/fishing")
    general_advisory: str = Field(..., description="General advisory about weather and cropping")
    crops_data: Dict[str, CropsData] = Field(..., description="Details of each crops/animal husbandry/poultry/fishing")

'''

schema = {
    "type": "object",
    "properties": {
        "weather_details": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "rainfall": {"type": "integer"},
                    "t_max": {"type": "integer"},
                    "t_min": {"type": "integer"},
                    "rh_max": {"type": "integer"},
                    "rh_min": {"type": "integer"},
                    "wind_speed": {"type": "integer"},
                    "wind_direction": {"type": "integer"},
                    "cloud_cover": {"type": "integer"}
                },
                "required": ["rainfall", "t_max", "t_min", "rh_max", "rh_min", "wind_speed", "wind_direction", "cloud_cover"]
            }
        },
        "names_of_crops": {"type": "array", "items": {"type": "string"}},
        "general_advisory": {"type": "string"},
        "crops_data": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "advisory": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["advisory"]
            }
        }
    },
    "required": ["weather_details", "names_of_crops", "general_advisory", "crops_data"]
}
