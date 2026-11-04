import flight_pb2
import flight_pb2_grpc
import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from app.config import FLIGHT_API_KEY, FLIGHT_SERVICE_ADDRESS, GRPC_TIMEOUT_SECONDS
from app.errors import ApiError
from app.resilience import CircuitBreakerInterceptor, CircuitOpenError, RetryInterceptor

channel = None
stub = None
METADATA = (("x-api-key", FLIGHT_API_KEY),)

ERRORS = {
    grpc.StatusCode.INVALID_ARGUMENT: (400, "INVALID_REQUEST", None),
    grpc.StatusCode.ALREADY_EXISTS: (409, "RESERVATION_CONFLICT", None),
    grpc.StatusCode.RESOURCE_EXHAUSTED: (409, "NOT_ENOUGH_SEATS", None),
    grpc.StatusCode.FAILED_PRECONDITION: (409, "FLIGHT_NOT_AVAILABLE", None),
    grpc.StatusCode.UNAUTHENTICATED: (502, "FLIGHT_SERVICE_AUTH_FAILED", "flight service rejected credentials"),
    grpc.StatusCode.UNAVAILABLE: (503, "FLIGHT_SERVICE_UNAVAILABLE", "flight service is temporarily unavailable"),
    grpc.StatusCode.DEADLINE_EXCEEDED: (504, "FLIGHT_SERVICE_TIMEOUT", "flight service did not respond in time"),
}


async def call(method, request, not_found_code: str = "FLIGHT_NOT_FOUND"):
    try:
        return await method(request, timeout=GRPC_TIMEOUT_SECONDS, metadata=METADATA)
    except CircuitOpenError:
        raise ApiError(503, "FLIGHT_SERVICE_UNAVAILABLE", "flight service is temporarily unavailable")
    except grpc.aio.AioRpcError as exc:
        code = exc.code()
        if code == grpc.StatusCode.NOT_FOUND:
            raise ApiError(404, not_found_code, exc.details() or "not found")
        status, error_code, message = ERRORS.get(code, (502, "FLIGHT_SERVICE_ERROR", "flight service error"))
        raise ApiError(status, error_code, message or exc.details() or "flight service error")


async def search_flights(origin: str, destination: str, day) -> flight_pb2.SearchFlightsResponse:
    request = flight_pb2.SearchFlightsRequest(origin=origin, destination=destination)
    if day is not None:
        timestamp = Timestamp()
        timestamp.FromJsonString(f"{day.isoformat()}T00:00:00Z")
        request.date.CopyFrom(timestamp)
    return await call(stub.SearchFlights, request)


async def get_flight(flight_id: int) -> flight_pb2.Flight:
    return await call(stub.GetFlight, flight_pb2.GetFlightRequest(flight_id=flight_id))


async def reserve_seats(flight_id: int, seat_count: int, booking_id: str) -> flight_pb2.ReserveSeatsResponse:
    request = flight_pb2.ReserveSeatsRequest(flight_id=flight_id, seat_count=seat_count, booking_id=booking_id)
    return await call(stub.ReserveSeats, request)


async def release_reservation(booking_id: str) -> flight_pb2.ReleaseReservationResponse:
    request = flight_pb2.ReleaseReservationRequest(booking_id=booking_id)
    return await call(stub.ReleaseReservation, request, not_found_code="RESERVATION_NOT_FOUND")


def open() -> None:
    global channel, stub
    channel = grpc.aio.insecure_channel(
        FLIGHT_SERVICE_ADDRESS,
        interceptors=[RetryInterceptor(), CircuitBreakerInterceptor()],
    )
    stub = flight_pb2_grpc.FlightServiceStub(channel)


async def close() -> None:
    await channel.close()
