# hw3_service_oriented_structures

Ошибки Flight Service

| метод | код | когда происходит |
|---|---|---|
| все | UNAUTHENTICATED | нет ключа x-api-key или он неверный |
| SearchFlights | INVALID_ARGUMENT | origin или destination не IATA-код |
| GetFlight | INVALID_ARGUMENT | flight_id не положительный |
| GetFlight | NOT_FOUND | рейс не найден |
| ReserveSeats | INVALID_ARGUMENT | неверные flight_id, seat_count или booking_id |
| ReserveSeats | NOT_FOUND | рейс не найден |
| ReserveSeats | FAILED_PRECONDITION | рейс не в статусе SCHEDULED |
| ReserveSeats | RESOURCE_EXHAUSTED | не хватает мест |
| ReserveSeats | ALREADY_EXISTS | для booking_id уже есть резервация с другими параметрами |
| ReleaseReservation | INVALID_ARGUMENT | booking_id не uuid |
| ReleaseReservation | NOT_FOUND | резервация не найдена |
| ReleaseReservation | FAILED_PRECONDITION | резервация не активна |
