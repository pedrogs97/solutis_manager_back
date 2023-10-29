FROM python:3.11.4-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH='/'

COPY ./poetry.lock /
COPY ./pyproject.toml /
COPY ./scripts /scripts
COPY ./app /app
COPY ./openssl.cnf /etc/ssl/openssl.cnf

RUN apt-get update -y && apt-get install curl -y \
    && apt-get install wkhtmltopdf -y \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false \
    && poetry install \
    # optional: kerberos library for debian-slim distributions
    && apt-get install -y libgssapi-krb5-2 \
    && apt-get remove curl -y \
    && chmod -R 755 /var \
    && chmod -R +x /scripts


WORKDIR /app

ENV PATH="/scripts:$PATH"

ENV XDG_RUNTIME_DIR="/app"
ENV RUNLEVEL=3

# ENTRYPOINT "config-db.sh"
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
