import logging
from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import FastAPI, Query

from app import bookings, flight_client
from app.db import pool
from app.errors import register_error_handlers
from app.schemas import BookingCreate, BookingResponse, FlightResponse, to_flight_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await pool.open()
    flight_client.open()
    yield
    await flight_client.close()
    await pool.close()


app = FastAPI(title="Booking Service", lifespan=lifespan)
register_error_handlers(app)


@app.get("/flights", response_model=list[FlightResponse])
async def search_flights(
    origin: str = Query(pattern=r"^[A-Z]{3}$"),
    destination: str = Query(pattern=r"^[A-Z]{3}$"),
    date: date | None = None,
):
    response = await flight_client.search_flights(origin, destination, date)
    return [to_flight_response(flight) for flight in response.flights]


@app.get("/flights/{flight_id}", response_model=FlightResponse)
async def get_flight(flight_id: int):
    return to_flight_response(await flight_client.get_flight(flight_id))


@app.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate):
    return await bookings.create(data)


@app.get("/bookings", response_model=list[BookingResponse])
async def list_bookings(user_id: int = Query(gt=0)):
    return await bookings.list_for_user(user_id)


@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID):
    return await bookings.get(booking_id)


@app.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: UUID):
    return await bookings.cancel(booking_id)
