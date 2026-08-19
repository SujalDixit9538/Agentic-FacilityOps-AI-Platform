from pydantic import BaseModel

class ManualPredictRequest(BaseModel):
    type: str
    air_temp: float
    process_temp: float
    speed: float
    torque: float
    wear: float