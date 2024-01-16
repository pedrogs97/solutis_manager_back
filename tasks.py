"""Task"""
import os
from datetime import date
from os.path import dirname

import jinja2
import pdfkit
from invoke import task
from sqlalchemy import Table

from src.config import CONTRACT_UPLOAD_DIR, DEFAULT_DATE_FORMAT, TEMPLATE_DIR
from src.database import Base, Engine, Session_db
from src.utils import get_file_paths, read_file


@task
def makemigrations(cmd, message):
    """Generate alembic migrations"""
    cmd.run(f'alembic revision --autogenerate -m "{message}"')


@task
def migrate(cmd):
    """Execute alembic migrations"""
    cmd.run("alembic upgrade head")


@task
def revertmigration(cmd):
    """Revert last alembic migration"""
    cmd.run("alembic downgrade -1")


@task
def run(cmd):
    """Run application"""
    cmd.run("uvicorn src.main:appAPI --port 8000 --reload")


@task
def loaddata(cmd, module: str, fixture: str = None):
    """Load fixtures to database"""
    fixtures_directory: str = dirname(__file__) + f"/src/{module}/fixtures/"
    try:
        if fixture:
            file_path: str = fixtures_directory + fixture + ".json"
            fixtures: list = read_file(file_path=file_path)
            for item in fixtures:
                table_name = item.pop("table", "")
                if table_name == "":
                    cmd.run("echo table not found")
                    return
                table = Table(table_name, Base.metadata, autoload_with=Engine)
                with Session_db() as session:
                    if not session.execute(
                        table.select().where(table.c.id == item["id"])
                    ).first():
                        session.execute(table.insert().values(item))
                        session.commit()
            cmd.run(f"echo {len(fixtures)} fixtures applied on {table_name}")
        else:
            file_paths: list = get_file_paths(fixtures_directory)
            for file_path in file_paths:
                fixtures: list = read_file(file_path=fixtures_directory + file_path)
                for item in fixtures:
                    table_name = item.pop("table", "")
                    if table_name == "":
                        cmd.run("echo table not found")
                        return
                    table = Table(table_name, Base.metadata, autoload_with=Engine)
                    with Session_db() as session:
                        if not session.execute(
                            table.select().where(table.c.id == item["id"])
                        ).first():
                            session.execute(table.insert().values(item))
                            session.commit()
                cmd.run(f"echo {len(fixtures)} fixtures applied on {table_name}")
    except FileNotFoundError:
        cmd.run(f"echo fixture {fixture} not found")


def __contract():
    """
    Contract
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "comodato.html"
    template = template_env.get_template(template_file)
    output_text = template.render(
        number="35161343241",
        glpi_number="GLPI 41325",
        full_name="Abmael da Silva",
        taxpayer_identification="222.222.222-22",
        national_identification="22222222-22",
        address="Rua da esquina, 31, Alpha Vile, Salvador",
        nationality="BRASILEIRO",
        role="Desenvolvedor",
        marital_status="CASADO",
        cc="23412-1",
        manager="Hericles Bitencurt",
        business_executive="Janaina Bitencurt",
        project="Solutis",
        workload="Home Office",
        register_number="sa321431",
        serial_number="2151232",
        description="Macbook Air",
        accessories="N/A",
        ms_office="Sim",
        pattern="Studio",
        operational_system="MacOS",
        value="46.000,00",
        date=date.today().strftime(DEFAULT_DATE_FORMAT),
        witnesses=[
            {
                "full_name": "Testemunha 1 teste",
                "taxpayer_identification": "000.000.000-00",
            },
            {
                "full_name": "Testemunha 2 teste",
                "taxpayer_identification": "111.111.111-11",
            },
        ],
    )

    if not os.path.exists(CONTRACT_UPLOAD_DIR):
        os.mkdir(CONTRACT_UPLOAD_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(
        os.path.join(CONTRACT_UPLOAD_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_DIR, "contract_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_DIR, "template_test.html"))


def __contract_pj():
    """
    Contract
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "comodato_pj.html"
    template = template_env.get_template(template_file)
    output_text = template.render(
        number="35161343241",
        glpi_number="GLPI 41325",
        full_name="Abmael da Silva",
        taxpayer_identification="222.222.222-22",
        national_identification="22222222-22",
        company="MEI teste",
        cnpj="13.185.790/0001-79",
        company_address="Rua da esquina, 31, Pituba, Salvador",
        address="Rua da esquina, 31, Alpha Vile, Salvador",
        nationality="BRASILEIRO",
        role="Desenvolvedor",
        marital_status="CASADO",
        cc="23412-1",
        manager="Hericles Bitencurt",
        business_executive="Janaina Bitencurt",
        project="Solutis",
        workload="Home Office",
        date_confirm=date.today().strftime(DEFAULT_DATE_FORMAT),
        goal="objetivo teste",
        register_number="sa321431",
        serial_number="2151232",
        description="Macbook Air",
        accessories="N/A",
        ms_office="Sim",
        pattern="Studio",
        operational_system="MacOS",
        value="46.000,00",
        date=date.today().strftime(DEFAULT_DATE_FORMAT),
        witnesses=[
            {
                "full_name": "Testemunha 1 teste",
                "taxpayer_identification": "000.000.000-00",
            },
            {
                "full_name": "Testemunha 2 teste",
                "taxpayer_identification": "111.111.111-11",
            },
        ],
    )

    if not os.path.exists(CONTRACT_UPLOAD_DIR):
        os.mkdir(CONTRACT_UPLOAD_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_DIR, "template_pj_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(
        os.path.join(CONTRACT_UPLOAD_DIR, "template_pj_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_DIR, "contract_pj_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_DIR, "template_pj_test.html"))


@task
def test(cmd):
    """
    Convert html to pdf using pdfkit which is a wrapper of wkhtmltopdf
    """
    cmd.run("echo conversion started")
    __contract()
    __contract_pj()
    cmd.run("echo conversion finished")
