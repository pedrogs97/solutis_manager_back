FROM python:3.11.4-slim-bullseye

USER 0

RUN mkdir -p /solutis-agile/
RUN mkdir -p /solutis-agile/src

USER $CONTAINER_USER_ID

ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH='/'
ENV XDG_RUNTIME_DIR="/solutis-agile/src"
ENV RUNLEVEL=3

COPY ./poetry.lock /solutis-agile
COPY ./pyproject.toml /solutis-agile
COPY ./nginx/config.json /docker-entrypoint.d/config.json
COPY ./README.md /solutis-agile/README.md
COPY ./src /solutis-agile/src
COPY ./logs /solutis-agile/logs
COPY ./alembic /solutis-agile/alembic
COPY ./alembic.ini /solutis-agile
COPY ./tasks.py /solutis-agile

WORKDIR /solutis-agile

RUN apt-get update -y && apt-get install curl -y \
    && apt-get install wkhtmltopdf -y \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install --no-cache-dir --upgrade -r requirements.txt \
    && apt-get remove curl -y \
    && pip uninstall poetry \
    && rm requirements.txt

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
