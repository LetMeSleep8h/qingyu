FROM python:3.12-slim

# Silence pip and keep the image small; build tools are not needed (pure-Python deps).
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv/qingyu

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install .

# Non-root runtime user; /data holds nothing by default (ARCHIVE_ROOT is env-driven)
RUN useradd --system --create-home --home-dir /home/qingyu qingyu
USER qingyu

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
