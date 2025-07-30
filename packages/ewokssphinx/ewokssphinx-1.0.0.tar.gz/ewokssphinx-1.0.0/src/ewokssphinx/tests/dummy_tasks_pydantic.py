from ewokscore import Task
from ewokscore.model import BaseInputModel
from pydantic import Field


class Inputs(BaseInputModel):
    planet: str = "Earth"
    latitude: int = Field(examples=[-90, 0, 90])
    longitude: float = Field(
        description="Longitude of the GPS point. **In degrees.**", examples=[-90, 0, 90]
    )


class FindLocation(
    Task,
    input_model=Inputs,
    output_names=["location", "error"],
):
    """Finds a location given the GPS coordinates"""

    def run(self):
        pass
