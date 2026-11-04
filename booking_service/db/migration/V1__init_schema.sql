create type booking_status as enum ('CONFIRMED', 'CANCELLED');

create table bookings (
    id uuid primary key,
    user_id bigint not null,
    flight_id bigint not null,
    passenger_name varchar(255) not null,
    passenger_email varchar(255) not null,
    seat_count integer not null check (seat_count > 0),
    total_price numeric(12, 2) not null check (total_price > 0),
    status booking_status not null default 'CONFIRMED',
    created_at timestamptz not null default now()
);
create index idx_bookings_user on bookings (user_id, created_at desc);
