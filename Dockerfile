FROM python:3.13-slim-bookworm

USER 0

RUN mkdir -p /solutis-agile/
RUN mkdir -p /solutis-agile/src

USER $CONTAINER_USER_ID

ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH='/'
ENV XDG_RUNTIME_DIR="/solutis-agile/src"
ENV RUNLEVEL=3

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./uv.lock /solutis-agile
COPY ./pyproject.toml /solutis-agile
COPY ./README.md /solutis-agile/README.md
COPY ./src /solutis-agile/src
COPY ./alembic /solutis-agile/alembic
COPY ./alembic.ini /solutis-agile
COPY ./tasks.py /solutis-agile
COPY ./templates /solutis-agile/templates
COPY ./requirements.txt /solutis-agile
COPY ./pyproject.toml /solutis-agile

WORKDIR /solutis-agile

RUN uv sync --frozen --no-install-project --no-dev

# Install system packages and configure locale
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update -y \
    && apt-get install -y curl locales \
    && sed -i '/^# pt_BR.UTF-8 UTF-8/s/^# //' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=pt_BR.UTF-8

# Install WeasyPrint and dependencies
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y weasyprint \
    && apt-get install -y python3-dev default-libmysqlclient-dev build-essential \
    && apt-get install -y python3-pip \
    && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 \
    && apt-get install -y libjpeg-dev libopenjp2-7-dev libffi-dev


# Install Microsoft SQL Server tools
RUN export DEBIAN_FRONTEND=noninteractive \
    && curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc \
    && curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -y \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get install -y unixodbc unixodbc-dev libgssapi-krb5-2

# Cleanup
RUN chmod -R 755 /var \
    && apt-get remove curl -y \
    && apt-get auto-remove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/mssql-tools17/bin:$PATH"
