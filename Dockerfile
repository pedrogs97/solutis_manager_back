FROM python:3.9.18-slim-bullseye

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
COPY ./README.md /solutis-agile/README.md
COPY ./src /solutis-agile/src
COPY ./alembic /solutis-agile/alembic
COPY ./alembic.ini /solutis-agile
COPY ./tasks.py /solutis-agile
COPY ./templates /solutis-agile/templates

WORKDIR /solutis-agile

RUN apt-get update -y && apt-get install curl -y \
    && apt-get install -y locales \
    && dpkg-reconfigure -f noninteractive locales \
    && locale-gen pt_BR \
    && update-locale \
    && apt-get install wkhtmltopdf -y \
    && apt-get install python3-dev python3.9-dev default-libmysqlclient-dev build-essential -y \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install --upgrade pip \
    && pip install --no-cache-dir --upgrade -r requirements.txt \
    && curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc \
    && curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -y \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get install -y unixodbc \
    && apt-get install -y unixodbc-dev \
    && apt-get install -y libgssapi-krb5-2 \
    && chmod -R 755 /var \
    && apt-get auto-remove -y \
    && apt-get remove curl -y \
    && pip uninstall poetry \
    && rm requirements.txt

ENV PATH="/opt/mssql-tools17/bin:$PATH"
