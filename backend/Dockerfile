# ---- build stage ----
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip install --no-cache-dir uvicorn[standard]
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

# ---- runtime stage ----
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /app/app ./app
COPY --from=build /app/alembic.ini ./
COPY --from=build /app/alembic ./alembic
USER appuser
EXPOSE 8000
# §12: migrations run on container start
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
