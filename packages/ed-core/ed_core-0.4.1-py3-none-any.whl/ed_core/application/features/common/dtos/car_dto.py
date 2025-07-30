from typing import TypedDict


class CarDto(TypedDict):
    make: str
    model: str
    year: int
    color: str
    seats: int
    license_plate_number: str
    registration_number: str
