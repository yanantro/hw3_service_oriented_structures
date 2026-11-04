FROM python:3.12-slim AS proto
WORKDIR /build
RUN pip install --no-cache-dir grpcio-tools==1.85.1
COPY proto ./proto
RUN mkdir generated && python -m grpc_tools.protoc -I proto --python_out=generated --grpc_python_out=generated proto/flight.proto

FROM python:3.12-slim
WORKDIR /app
COPY flight_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY flight_service/app ./app
COPY --from=proto /build/generated ./generated
ENV PYTHONPATH=/app/generated:/app \
    PYTHONUNBUFFERED=1
CMD ["python", "-m", "app.main"]
