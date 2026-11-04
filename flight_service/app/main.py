import asyncio
import logging

import flight_pb2_grpc
import grpc

from app import cache
from app.auth import ApiKeyInterceptor
from app.config import GRPC_PORT
from app.db import pool
from app.service import FlightServicer

log = logging.getLogger("flight")


async def serve() -> None:
    await pool.open()
    server = grpc.aio.server(interceptors=[ApiKeyInterceptor()])
    flight_pb2_grpc.add_FlightServiceServicer_to_server(FlightServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    await server.start()
    log.info("flight service started on port %s", GRPC_PORT)
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(2)
        await cache.close()
        await pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(serve())
