prompt = """
Create a JSON from the Text that conforms to the following pydantic class.

from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Union

class WeatherData(BaseModel):
    Date: str
    Rainfall_mm: float
    Max_Temp_C: float
    Min_Temp_C: float
    Cloud_Cover: Union[int, None]
    Max_RH_Percent: int
    Min_RH_Percent: int
    Wind_Speed_kmph: int
    Wind_Direction_deg: int

class AgrometAdvisory(BaseModel):
    Crop: str
    Advisory: str

class OfficialContact(BaseModel):
    Name: str
    Position: str

class BulletinDetails(BaseModel):
    Week_Number: str
    District: str
    Bulletin_Number: str
    Date: str

class WeatherConditionLastWeek(BaseModel):
    Period: str
    Rainfall_mm: float
    Max_Temperature_C: str
    Min_Temperature_C: str

class ForecastUpTo(BaseModel):
    Date: str
    Description: str

class AdditionalResources(BaseModel):
    OUAT_KALINGA_Products: str
    Meghdoot_Mobile_App: Dict[str, HttpUrl]

class AgrometBulletin(BaseModel):
    Institution: Dict[str, str]
    Bulletin_Details: BulletinDetails
    Weather_Condition_Last_Week: WeatherConditionLastWeek
    Forecast_Up_To: ForecastUpTo
    Daily_Weather_Data: List[WeatherData]
    Agromet_Advisory: Dict[str, Union[str, List[AgrometAdvisory]]]
    Contact_Information: Dict[str, Union[str, List[OfficialContact]]]
    Additional_Resources: AdditionalResources

DONT SKIP ANY WORD. I want complete JSON. Don't write Similar structure for other dates, Additional crop advisories.

TEXT: 
"""
