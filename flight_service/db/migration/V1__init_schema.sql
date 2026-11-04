create type flight_status as enum ('SCHEDULED', 'DEPARTED', 'CANCELLED', 'COMPLETED');
create type reservation_status as enum ('ACTIVE', 'RELEASED', 'EXPIRED');

create table airlines (
    id bigint generated always as identity primary key,
    name varchar(100) not null unique,
    iata_code char(2) not null unique
);

create table flights (
    id bigint generated always as identity primary key,
    flight_number varchar(10) not null,
    airline_id bigint not null references airlines (id),
    origin char(3) not null check (origin ~ '^[A-Z]{3}$'),
    destination char(3) not null check (destination ~ '^[A-Z]{3}$'),
    departure_time timestamptz not null,
    arrival_time timestamptz not null,
    total_seats integer not null check (total_seats > 0),
    available_seats integer not null check (available_seats >= 0),
    price numeric(12, 2) not null check (price > 0),
    status flight_status not null default 'SCHEDULED',
    check (origin <> destination),
    check (arrival_time > departure_time),
    check (available_seats <= total_seats)
);
create unique index uq_flights_number_date on flights (flight_number, ((departure_time at time zone 'UTC')::date));
create index idx_flights_route on flights (origin, destination, departure_time);

create table seat_reservations (
    id bigint generated always as identity primary key,
    flight_id bigint not null references flights (id),
    booking_id uuid not null unique,
    seat_count integer not null check (seat_count > 0),
    status reservation_status not null default 'ACTIVE',
    created_at timestamptz not null default now()
);
create index idx_seat_reservations_flight on seat_reservations (flight_id);
