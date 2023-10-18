FROM python:3.11.4-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH='/'

COPY ./poetry.lock /
COPY ./pyproject.toml /
COPY ./scripts /scripts
COPY ./app /app
COPY ./datasync /datasync
COPY ./openssl.cnf /etc/ssl/openssl.cnf

RUN apt-get update -y && apt-get install curl -y \
    && apt-get install wkhtmltopdf -y \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false \
    && poetry install \
    && curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc \
    #Download appropriate package for the OS version
    #Choose only ONE of the following, corresponding to your OS version
    #Debian 11
    && curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # optional: for bcp and sqlcmd
    # && ACCEPT_EULA=Y apt-get install -y mssql-tools17 \
    # optional: for unixODBC development headers
    && apt-get install -y unixodbc \
    && apt-get install -y unixodbc-dev \
    # optional: kerberos library for debian-slim distributions
    && apt-get install -y libgssapi-krb5-2 \
    && apt-get remove curl -y \
    && apt-get install vim -y \
    && chmod -R 755 /var \
    && chmod -R 755 /datasync \
    && chmod -R +x /scripts


WORKDIR /app

ENV PATH="/scripts:$PATH"
ENV PATH="/opt/mssql-tools17/bin:$PATH"

ENV XDG_RUNTIME_DIR="/app"
ENV RUNLEVEL=3

# ENTRYPOINT "config-db.sh"
