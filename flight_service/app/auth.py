import hmac

import grpc

from app.config import FLIGHT_API_KEY


async def deny(request, context):
    await context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid or missing api key")


class ApiKeyInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        key = metadata.get("x-api-key", "")
        if not FLIGHT_API_KEY or not hmac.compare_digest(str(key), FLIGHT_API_KEY):
            return grpc.unary_unary_rpc_method_handler(deny)
        return await continuation(handler_call_details)
