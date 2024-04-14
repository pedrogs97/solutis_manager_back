"""Task"""

import base64
import os
from datetime import date
from os.path import dirname

import jinja2
import pdfkit
from invoke import task
from sqlalchemy import Table

from src.config import CONTRACT_UPLOAD_TEST_DIR, DEFAULT_DATE_FORMAT, TEMPLATE_DIR
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
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
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
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "contract_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


def __termination():
    """
    Termination
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "distrato_comodato.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
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
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "termination_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


def __termination_pj():
    """
    Termination PJ
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "distrato_comodato_pj.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
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
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "termination_pj_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


def __contract_pj():
    """
    Contract
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "comodato_pj.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
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
        contract_date=date.today().strftime(DEFAULT_DATE_FORMAT),
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
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_pj_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_pj_test.html"),
        encoding="utf-8",
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "contract_pj_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_pj_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


def __term():
    """
    Term
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "termo.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
    output_text = template.render(
        number="35161343241",
        glpi_number="GLPI 41325",
        full_name="Abmael da Silva",
        taxpayer_identification="222.222.222-22",
        national_identification="22222222-22",
        address="Rua da esquina, 31, Alpha Vile, Salvador",
        nationality="BRASILEIRO",
        role="Desenvolvedor",
        cc="23412-1",
        manager="Hericles Bitencurt",
        project="Solutis",
        description="Camisa",
        size="N/A",
        quantity=1,
        value="46.000,00",
        date=date.today().strftime(DEFAULT_DATE_FORMAT),
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "term_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


def __termination_term():
    """
    Termination term
    """
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "distrato_termo.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    signed_file = open("./src/static/images/signed.png", "rb")
    signed_encoded_string = (
        str(base64.b64encode(signed_file.read())).replace("b'", "").replace("'", "")
    )
    date_image = open("./src/static/images/date.jpeg", "rb")
    date_image_encoded_string = (
        str(base64.b64encode(date_image.read())).replace("b'", "").replace("'", "")
    )
    n_glpi_file = open("./src/static/images/n_glpi.png", "rb")
    n_glpi_encoded_string = (
        str(base64.b64encode(n_glpi_file.read())).replace("b'", "").replace("'", "")
    )
    n_termo_file = open("./src/static/images/n_termo.png", "rb")
    n_termo_encoded_string = (
        str(base64.b64encode(n_termo_file.read())).replace("b'", "").replace("'", "")
    )
    output_text = template.render(
        number="35161343241",
        glpi_number="GLPI 41325",
        full_name="Abmael da Silva",
        taxpayer_identification="222.222.222-22",
        national_identification="22222222-22",
        address="Rua da esquina, 31, Alpha Vile, Salvador",
        nationality="BRASILEIRO",
        role="Desenvolvedor",
        cc="23412-1",
        manager="Hericles Bitencurt",
        project="Solutis",
        description="Camisa",
        size="N/A",
        quantity=1,
        value="46.000,00",
        date=date.today().strftime(DEFAULT_DATE_FORMAT),
        signed=f"data:image/png;base64,{signed_encoded_string}",
        date_image=f"data:image/png;base64,{date_image_encoded_string}",
        n_glpi=f"data:image/png;base64,{n_glpi_encoded_string}",
        n_termo=f"data:image/png;base64,{n_termo_encoded_string}",
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        location="Salvador - BA",
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "termination_term_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    signed_file.close()
    date_image.close()
    n_glpi_file.close()
    n_termo_file.close()


@task
def test(cmd):
    """
    Convert html to pdf using pdfkit which is a wrapper of wkhtmltopdf
    """
    cmd.run("echo conversion started")
    __term()
    __termination_term()
    __contract()
    __termination()
    __contract_pj()
    __termination_pj()
    cmd.run("echo conversion finished")


@task
def testverification(cmd):
    """
    Convert html to pdf using pdfkit which is a wrapper of wkhtmltopdf
    """
    cmd.run("echo conversion started")
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "verification.html"
    template = template_env.get_template(template_file)
    logo_file = open("./src/static/images/ri_1.png", "rb")
    logo_encoded_string = (
        str(base64.b64encode(logo_file.read())).replace("b'", "").replace("'", "")
    )
    output_text = template.render(
        ri_1=f"data:image/png;base64,{logo_encoded_string}",
        verifications=[
            {
                "question": "Carregador - Estado do conector",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 42,
                    },
                    {
                        "checked": False,
                        "option": "Danificado",
                        "id": 43,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 44,
                    },
                ],
            },
            {
                "question": "Serial do carregador",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 45,
                    },
                    {
                        "checked": False,
                        "option": "Danificado",
                        "id": 46,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 47,
                    },
                ],
            },
            {
                "question": "Carregador - Estado do cabo de energia",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 48,
                    },
                    {
                        "checked": False,
                        "option": "Danificado",
                        "id": 49,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 50,
                    },
                ],
            },
            {
                "question": "Borrachas de proteção",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 1,
                    },
                    {
                        "checked": False,
                        "option": "Danificado",
                        "id": 2,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 3,
                    },
                ],
            },
            {
                "question": "Estado do LCD",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 4,
                    },
                    {
                        "checked": False,
                        "option": "Riscado",
                        "id": 5,
                    },
                    {
                        "checked": False,
                        "option": "Quebrado",
                        "id": 6,
                    },
                    {
                        "checked": False,
                        "option": "Não liga",
                        "id": 7,
                    },
                ],
            },
            {
                "question": "Estado do touchpad",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 8,
                    },
                    {
                        "checked": False,
                        "option": "Riscado",
                        "id": 9,
                    },
                    {
                        "checked": False,
                        "option": "Não funciona",
                        "id": 10,
                    },
                    {
                        "checked": False,
                        "option": "Impossível verificar pois não liga",
                        "id": 11,
                    },
                ],
            },
            {
                "question": "Estado da carcaça",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 12,
                    },
                    {
                        "checked": False,
                        "option": "Riscado",
                        "id": 13,
                    },
                    {
                        "checked": False,
                        "option": "Quebrado",
                        "id": 14,
                    },
                ],
            },
            {
                "question": "Estado do Teclado",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 15,
                    },
                    {
                        "checked": False,
                        "option": "Faltando tecla",
                        "id": 16,
                    },
                    {
                        "checked": False,
                        "option": "Não funciona",
                        "id": 17,
                    },
                ],
            },
            {
                "question": "Carregador Bateria (entrada)",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 18,
                    },
                    {
                        "checked": False,
                        "option": "Danificado",
                        "id": 19,
                    },
                ],
            },
            {
                "question": "Conectores USB/Ethernet/Modem",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 20,
                    },
                    {
                        "checked": False,
                        "option": "Danificados",
                        "id": 21,
                    },
                ],
            },
            {
                "question": "Drive de Disco CD - DVD - DVDRW",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 22,
                    },
                    {
                        "checked": False,
                        "option": "Não funciona",
                        "id": 23,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 24,
                    },
                ],
            },
            {
                "question": "Estado da carcaça (atrás da tela)",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 25,
                    },
                    {
                        "checked": False,
                        "option": "Riscado",
                        "id": 26,
                    },
                    {
                        "checked": False,
                        "option": "Quebrado",
                        "id": 27,
                    },
                ],
            },
            {
                "question": "Bateria - Verificar serial (no notebook)",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 28,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 29,
                    },
                ],
            },
            {
                "question": "Borracha de apoio",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 30,
                    },
                    {
                        "checked": False,
                        "option": "Faltam",
                        "id": 31,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 32,
                    },
                ],
            },
            {
                "question": "Serial da máquina",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 33,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 34,
                    },
                ],
            },
            {
                "question": "Parafusos da carcaça",
                "options": [
                    {
                        "checked": True,
                        "option": "Ok",
                        "id": 35,
                    },
                    {
                        "checked": False,
                        "option": "Faltam",
                        "id": 36,
                    },
                    {
                        "checked": False,
                        "option": "Não tem",
                        "id": 37,
                    },
                ],
            },
        ],
    )

    if not os.path.exists(CONTRACT_UPLOAD_TEST_DIR):
        os.mkdir(CONTRACT_UPLOAD_TEST_DIR)

    html_path = os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html")
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {
        "page-size": "A4",
        "enable-local-file-access": None,
    }

    with open(
        os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"), encoding="utf-8"
    ) as f:
        pdfkit.from_file(
            f,
            os.path.join(CONTRACT_UPLOAD_TEST_DIR, "verification_test.pdf"),
            options=options,
        )
    os.remove(os.path.join(CONTRACT_UPLOAD_TEST_DIR, "template_test.html"))
    logo_file.close()
    cmd.run("echo conversion finished")
