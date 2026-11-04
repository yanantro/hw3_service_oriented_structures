import flight_pb2


def to_flight(row: dict) -> flight_pb2.Flight:
    message = flight_pb2.Flight(
        id=row["id"],
        flight_number=row["flight_number"],
        airline=row["airline"],
        origin=row["origin"],
        destination=row["destination"],
        total_seats=row["total_seats"],
        available_seats=row["available_seats"],
        price=str(row["price"]),
        status=flight_pb2.FlightStatus.Value("FLIGHT_STATUS_" + row["status"]),
    )
    message.departure_time.FromDatetime(row["departure_time"])
    message.arrival_time.FromDatetime(row["arrival_time"])
    return message


def to_reservation(row: dict) -> flight_pb2.SeatReservation:
    message = flight_pb2.SeatReservation(
        booking_id=str(row["booking_id"]),
        flight_id=row["flight_id"],
        seat_count=row["seat_count"],
        status=flight_pb2.ReservationStatus.Value("RESERVATION_STATUS_" + row["status"]),
    )
    message.created_at.FromDatetime(row["created_at"])
    return message
