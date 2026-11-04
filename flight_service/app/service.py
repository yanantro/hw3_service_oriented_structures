import json
import logging
import re
import uuid
from datetime import timezone

import flight_pb2
import flight_pb2_grpc
import grpc
from google.protobuf import json_format

from app import cache, repository
from app.convert import to_flight, to_reservation
from app.errors import ServiceError

log = logging.getLogger("flight.service")

IATA = re.compile(r"^[A-Z]{3}$")


def parse_booking_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError:
        raise ServiceError(grpc.StatusCode.INVALID_ARGUMENT, "booking_id must be a uuid")


class FlightServicer(flight_pb2_grpc.FlightServiceServicer):
    async def SearchFlights(self, request, context):
        try:
            if not IATA.match(request.origin) or not IATA.match(request.destination):
                raise ServiceError(grpc.StatusCode.INVALID_ARGUMENT, "origin and destination must be iata codes")
            day = request.date.ToDatetime(tzinfo=timezone.utc).date() if request.HasField("date") else None

            key = cache.search_key(request.origin, request.destination, day.isoformat() if day else None)
            cached = await cache.get(key)
            if cached is not None:
                return json_format.ParseDict(json.loads(cached), flight_pb2.SearchFlightsResponse())

            rows = await repository.search_flights(request.origin, request.destination, day)
            response = flight_pb2.SearchFlightsResponse(flights=[to_flight(row) for row in rows])
            await cache.put(key, json.dumps(json_format.MessageToDict(response)))
            return response
        except ServiceError as exc:
            await context.abort(exc.code, exc.message)

    async def GetFlight(self, request, context):
        try:
            if request.flight_id <= 0:
                raise ServiceError(grpc.StatusCode.INVALID_ARGUMENT, "flight_id must be positive")

            key = cache.flight_key(request.flight_id)
            cached = await cache.get(key)
            if cached is not None:
                return json_format.ParseDict(json.loads(cached), flight_pb2.Flight())

            row = await repository.get_flight(request.flight_id)
            if row is None:
                raise ServiceError(grpc.StatusCode.NOT_FOUND, "flight not found")
            response = to_flight(row)
            await cache.put(key, json.dumps(json_format.MessageToDict(response)))
            return response
        except ServiceError as exc:
            await context.abort(exc.code, exc.message)

    async def ReserveSeats(self, request, context):
        try:
            if request.flight_id <= 0 or request.seat_count <= 0:
                raise ServiceError(grpc.StatusCode.INVALID_ARGUMENT, "flight_id and seat_count must be positive")
            booking_id = parse_booking_id(request.booking_id)

            reservation, flight = await repository.reserve_seats(request.flight_id, request.seat_count, booking_id)
            await cache.invalidate_flight(flight["id"], flight["origin"], flight["destination"])
            log.info("seats reserved booking_id=%s flight_id=%s seats=%s", booking_id, flight["id"], request.seat_count)
            return flight_pb2.ReserveSeatsResponse(reservation=to_reservation(reservation))
        except ServiceError as exc:
            await context.abort(exc.code, exc.message)

    async def ReleaseReservation(self, request, context):
        try:
            booking_id = parse_booking_id(request.booking_id)

            reservation, flight = await repository.release_reservation(booking_id)
            await cache.invalidate_flight(flight["id"], flight["origin"], flight["destination"])
            log.info("reservation released booking_id=%s flight_id=%s", booking_id, flight["id"])
            return flight_pb2.ReleaseReservationResponse(reservation=to_reservation(reservation))
        except ServiceError as exc:
            await context.abort(exc.code, exc.message)
