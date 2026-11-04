import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://flight:flight@localhost:5432/flight")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY", "")

REDIS_SENTINELS = [
    (host, int(port))
    for host, port in (item.split(":") for item in os.getenv("REDIS_SENTINELS", "localhost:26379").split(","))
]
REDIS_MASTER_NAME = os.getenv("REDIS_MASTER_NAME", "mymaster")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
