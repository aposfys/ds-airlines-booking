# Python 3.9 reached end-of-life in October 2025 and receives no security
# patches. Pinned deps are resolved against 3.13.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

# Run as a non-root user: a container breakout from a root process gets root
# on the host namespace.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# No --reload: the auto-reloader watches the filesystem, runs a supervisor
# process, and is not intended for anything but local development. The dev
# override lives in docker-compose.override.yml.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
