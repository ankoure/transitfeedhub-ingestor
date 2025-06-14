# syntax=docker/dockerfile:1

FROM python:3.12.10-slim-bookworm

ENV POETRY_VERSION=2.1.2 \
    POETRY_VIRTUALENVS_CREATE=false

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry install --no-interaction --no-ansi --no-root --no-dev

# Copy Python code to the Docker image
COPY transitfeedhub_ingestor /code/transitfeedhub_ingestor/

CMD [ "python", "transitfeedhub_ingestor/main.py"]
