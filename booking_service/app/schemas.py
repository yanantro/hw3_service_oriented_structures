from datetime import datetime, timezone
from uuid import UUID

import flight_pb2
from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class BookingCreate(BaseModel):
    user_id: int = Field(gt=0)
    flight_id: int = Field(gt=0)
    passenger_name: str = Field(min_length=1, max_length=255)
    passenger_email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    seat_count: int = Field(ge=1, le=999)


class BookingResponse(BaseModel):
    id: UUID
    user_id: int
    flight_id: int
    passenger_name: str
    passenger_email: str
    seat_count: int
    total_price: float
    status: str
    created_at: datetime


class FlightResponse(BaseModel):
    id: int
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    total_seats: int
    available_seats: int
    price: float
    status: str


def to_flight_response(message: flight_pb2.Flight) -> FlightResponse:
    return FlightResponse(
        id=message.id,
        flight_number=message.flight_number,
        airline=message.airline,
        origin=message.origin,
        destination=message.destination,
        departure_time=message.departure_time.ToDatetime(tzinfo=timezone.utc),
        arrival_time=message.arrival_time.ToDatetime(tzinfo=timezone.utc),
        total_seats=message.total_seats,
        available_seats=message.available_seats,
        price=float(message.price),
        status=flight_pb2.FlightStatus.Name(message.status).removeprefix("FLIGHT_STATUS_"),
    )


def to_booking_response(row: dict) -> BookingResponse:
    return BookingResponse(**{**row, "total_price": float(row["total_price"])})
