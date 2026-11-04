insert into airlines (name, iata_code) values
    ('Aeroflot', 'SU'),
    ('S7 Airlines', 'S7'),
    ('Pobeda', 'DP');

insert into flights (flight_number, airline_id, origin, destination, departure_time, arrival_time, total_seats, available_seats, price, status) values
    ('SU1234', 1, 'SVO', 'LED', '2026-12-01 07:00:00+00', '2026-12-01 08:30:00+00', 100, 100, 5500.00, 'SCHEDULED'),
    ('SU1236', 1, 'SVO', 'LED', '2026-12-01 18:00:00+00', '2026-12-01 19:30:00+00', 120, 120, 6200.50, 'SCHEDULED'),
    ('S7101', 2, 'DME', 'KZN', '2026-12-02 10:00:00+00', '2026-12-02 11:40:00+00', 80, 80, 4300.00, 'SCHEDULED'),
    ('DP401', 3, 'VKO', 'LED', '2026-12-03 06:30:00+00', '2026-12-03 08:00:00+00', 5, 5, 2500.00, 'SCHEDULED'),
    ('SU9000', 1, 'SVO', 'LED', '2026-12-04 09:00:00+00', '2026-12-04 10:30:00+00', 100, 100, 5000.00, 'CANCELLED');
