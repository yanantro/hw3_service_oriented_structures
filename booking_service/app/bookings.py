import logging
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID, uuid4

import flight_pb2

from app import flight_client
from app.db import pool
from app.errors import ApiError
from app.schemas import BookingCreate, BookingResponse, to_booking_response

log = logging.getLogger("booking")

COLUMNS = "id, user_id, flight_id, passenger_name, passenger_email, seat_count, total_price, status, created_at"


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def release_quietly(booking_id: str) -> None:
    try:
        await flight_client.release_reservation(booking_id)
    except ApiError as exc:
        log.warning("compensation release failed booking_id=%s error=%s", booking_id, exc.error_code)


async def create(data: BookingCreate) -> BookingResponse:
    booking_id = uuid4()

    flight = await flight_client.get_flight(data.flight_id)
    if flight.status != flight_pb2.FLIGHT_STATUS_SCHEDULED:
        raise ApiError(409, "FLIGHT_NOT_AVAILABLE", "flight is not open for booking")

    try:
        await flight_client.reserve_seats(data.flight_id, data.seat_count, str(booking_id))
    except ApiError as exc:
        if exc.status in (503, 504):
            await release_quietly(str(booking_id))
        raise

    total_price = money(Decimal(flight.price) * data.seat_count)
    try:
        async with pool.connection() as conn:
            cur = await conn.execute(
                f"""
                insert into bookings (id, user_id, flight_id, passenger_name, passenger_email, seat_count, total_price)
                values (%s, %s, %s, %s, %s, %s, %s)
                returning {COLUMNS}
                """,
                (booking_id, data.user_id, data.flight_id, data.passenger_name, data.passenger_email, data.seat_count, total_price),
            )
            row = await cur.fetchone()
    except Exception:
        await release_quietly(str(booking_id))
        raise
    return to_booking_response(row)


async def get(booking_id: UUID) -> BookingResponse:
    async with pool.connection() as conn:
        cur = await conn.execute(f"select {COLUMNS} from bookings where id = %s", (booking_id,))
        row = await cur.fetchone()
    if row is None:
        raise ApiError(404, "BOOKING_NOT_FOUND", "booking not found", {"booking_id": str(booking_id)})
    return to_booking_response(row)


async def list_for_user(user_id: int) -> list[BookingResponse]:
    async with pool.connection() as conn:
        cur = await conn.execute(
            f"select {COLUMNS} from bookings where user_id = %s order by created_at desc, id",
            (user_id,),
        )
        rows = await cur.fetchall()
    return [to_booking_response(row) for row in rows]


async def cancel(booking_id: UUID) -> BookingResponse:
    async with pool.connection() as conn, conn.transaction():
        cur = await conn.execute(f"select {COLUMNS} from bookings where id = %s for update", (booking_id,))
        row = await cur.fetchone()
        if row is None:
            raise ApiError(404, "BOOKING_NOT_FOUND", "booking not found", {"booking_id": str(booking_id)})
        if row["status"] != "CONFIRMED":
            raise ApiError(409, "BOOKING_NOT_CONFIRMED", "only confirmed bookings can be cancelled", {"status": row["status"]})

        await flight_client.release_reservation(str(booking_id))

        cur = await conn.execute(
            f"update bookings set status = 'CANCELLED' where id = %s returning {COLUMNS}",
            (booking_id,),
        )
        row = await cur.fetchone()
    return to_booking_response(row)
