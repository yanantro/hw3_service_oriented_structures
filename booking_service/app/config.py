import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://booking:booking@localhost:5432/booking")
FLIGHT_SERVICE_ADDRESS = os.getenv("FLIGHT_SERVICE_ADDRESS", "localhost:50051")
FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY", "")

GRPC_TIMEOUT_SECONDS = float(os.getenv("GRPC_TIMEOUT_SECONDS", "2"))

RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY_MS = int(os.getenv("RETRY_BASE_DELAY_MS", "100"))

CB_WINDOW_SIZE = int(os.getenv("CB_WINDOW_SIZE", "10"))
CB_FAILURE_THRESHOLD = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
CB_OPEN_SECONDS = float(os.getenv("CB_OPEN_SECONDS", "10"))
