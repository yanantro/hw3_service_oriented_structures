import grpc

from app.db import pool
from app.errors import ServiceError

FLIGHT_SELECT = """
    select f.id, f.flight_number, a.name as airline, f.origin, f.destination,
           f.departure_time, f.arrival_time, f.total_seats, f.available_seats,
           f.price, f.status
    from flights f
    join airlines a on a.id = f.airline_id
"""

RESERVATION_COLUMNS = "booking_id, flight_id, seat_count, status, created_at"


async def search_flights(origin: str, destination: str, day) -> list[dict]:
    sql = FLIGHT_SELECT + " where f.origin = %s and f.destination = %s and f.status = 'SCHEDULED'"
    params = [origin, destination]
    if day is not None:
        sql += " and (f.departure_time at time zone 'UTC')::date = %s"
        params.append(day)
    sql += " order by f.departure_time, f.id"
    async with pool.connection() as conn:
        cur = await conn.execute(sql, params)
        return await cur.fetchall()


async def get_flight(flight_id: int) -> dict | None:
    async with pool.connection() as conn:
        cur = await conn.execute(FLIGHT_SELECT + " where f.id = %s", (flight_id,))
        return await cur.fetchone()


async def reserve_seats(flight_id: int, seat_count: int, booking_id: str) -> tuple[dict, dict]:
    async with pool.connection() as conn, conn.transaction():
        cur = await conn.execute(
            "select id, origin, destination, available_seats, status from flights where id = %s for update",
            (flight_id,),
        )
        flight = await cur.fetchone()
        if flight is None:
            raise ServiceError(grpc.StatusCode.NOT_FOUND, "flight not found")

        cur = await conn.execute(
            f"select {RESERVATION_COLUMNS} from seat_reservations where booking_id = %s",
            (booking_id,),
        )
        existing = await cur.fetchone()
        if existing is not None:
            same = (
                existing["flight_id"] == flight_id
                and existing["seat_count"] == seat_count
                and existing["status"] == "ACTIVE"
            )
            if not same:
                raise ServiceError(grpc.StatusCode.ALREADY_EXISTS, "reservation for this booking already exists")
            return existing, flight

        if flight["status"] != "SCHEDULED":
            raise ServiceError(grpc.StatusCode.FAILED_PRECONDITION, "flight is not open for booking")
        if flight["available_seats"] < seat_count:
            raise ServiceError(grpc.StatusCode.RESOURCE_EXHAUSTED, "not enough available seats")

        await conn.execute(
            "update flights set available_seats = available_seats - %s where id = %s",
            (seat_count, flight_id),
        )
        cur = await conn.execute(
            f"""
            insert into seat_reservations (flight_id, booking_id, seat_count)
            values (%s, %s, %s)
            returning {RESERVATION_COLUMNS}
            """,
            (flight_id, booking_id, seat_count),
        )
        reservation = await cur.fetchone()
        return reservation, flight


async def release_reservation(booking_id: str) -> tuple[dict, dict]:
    async with pool.connection() as conn, conn.transaction():
        cur = await conn.execute(
            "select flight_id from seat_reservations where booking_id = %s",
            (booking_id,),
        )
        found = await cur.fetchone()
        if found is None:
            raise ServiceError(grpc.StatusCode.NOT_FOUND, "reservation not found")

        cur = await conn.execute(
            "select id, origin, destination from flights where id = %s for update",
            (found["flight_id"],),
        )
        flight = await cur.fetchone()

        cur = await conn.execute(
            f"select {RESERVATION_COLUMNS} from seat_reservations where booking_id = %s for update",
            (booking_id,),
        )
        reservation = await cur.fetchone()

        if reservation["status"] == "RELEASED":
            return reservation, flight
        if reservation["status"] != "ACTIVE":
            raise ServiceError(grpc.StatusCode.FAILED_PRECONDITION, "reservation is not active")

        await conn.execute(
            "update flights set available_seats = available_seats + %s where id = %s",
            (reservation["seat_count"], flight["id"]),
        )
        cur = await conn.execute(
            f"update seat_reservations set status = 'RELEASED' where booking_id = %s returning {RESERVATION_COLUMNS}",
            (booking_id,),
        )
        return await cur.fetchone(), flight
