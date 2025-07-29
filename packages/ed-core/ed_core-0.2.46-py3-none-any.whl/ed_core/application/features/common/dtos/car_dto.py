from pydantic import BaseModel


class CarDto(BaseModel):
    make: str
    model: str
    year: int
    color: str
    seats: int
    license_plate_number: str
    registration_number: str
