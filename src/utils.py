"""Base utils"""

import base64
import os
from json import loads
from os import listdir

import aiofiles
import jinja2
import pdfkit

from src.config import CONTRACT_UPLOAD_DIR, TEMPLATE_DIR
from src.document.schemas import (
    NewLendingContextSchema,
    NewLendingPjContextSchema,
    NewTermContextSchema,
)


def get_file_paths(directory: str):
    """Returns file path of directory"""
    list_dir = []
    for file in listdir(directory):
        if not file.endswith(".py"):
            list_dir.append(file)
    return list_dir


def read_file(file_path: str):
    """Return a dict from json file"""
    return loads(open(file_path, "r", encoding="utf-8").read())


async def upload_file(
    file_name: str, type_file: str, data: bytes, base_dir: str
) -> str:
    """Upload a file and returns file path"""
    folder_file = os.path.join(base_dir, type_file)

    if not os.path.isdir(folder_file):
        os.makedirs(folder_file, exist_ok=True)

    file_path = os.path.join(folder_file, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(data)  # async write chunk

    return file_path


def get_str_base64_image(file_name: str) -> str:
    """Get image base64 string"""
    str_base64 = ""
    with open(file_name, "rb") as image:
        str_base64 = (
            str(base64.b64encode(image.read())).replace("b'", "").replace("'", "")
        )
    return str_base64


SIGNED_DATE_IMAGE = "src/static/images/signed.png"
DATE_IMAGE = "src/static/images/date.jpeg"
GLPI_IMAGE = "src/static/images/n_glpi.png"
N_TERM_IMAGE = "src/static/images/n_termo.png"
LOGO_IMAGE = "src/static/images/ri_1.png"


def create_lending_contract(context: NewLendingContextSchema) -> str:
    """Creates new lending contract"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template_file = "comodato.html"
    template = template_env.get_template(template_file)
    signed_image = get_str_base64_image(SIGNED_DATE_IMAGE)
    date_image = get_str_base64_image(DATE_IMAGE)
    n_glpi_file = get_str_base64_image(GLPI_IMAGE)
    n_termo_file = get_str_base64_image(N_TERM_IMAGE)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        national_identification=context.national_identification,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        marital_status=context.marital_status,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        detail=context.detail,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
        signed=f"data:image/png;base64,{signed_image}",
        date_image=f"data:image/png;base64,{date_image}",
        n_glpi=f"data:image/png;base64,{n_glpi_file}",
        n_termo=f"data:image/png;base64,{n_termo_file}",
        ri_1=f"data:image/png;base64,{logo_file}",
        location=context.location,
        bu=context.bu,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(template_path, encoding="utf-8") as template_file:
        pdfkit.from_file(
            template_file,
            contract_path,
            options=options,
        )

    os.remove(template_path)
    return contract_path


def create_revoke_lending_contract(context: NewLendingContextSchema) -> str:
    """Creates new revoke lending contract"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template_file = "distrato_comodato.html"
    template = template_env.get_template(template_file)
    signed_image = get_str_base64_image(SIGNED_DATE_IMAGE)
    date_image = get_str_base64_image(DATE_IMAGE)
    n_glpi_file = get_str_base64_image(GLPI_IMAGE)
    n_termo_file = get_str_base64_image(N_TERM_IMAGE)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        national_identification=context.national_identification,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        marital_status=context.manager,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        detail=context.detail,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
        signed=f"data:image/png;base64,{signed_image}",
        date_image=f"data:image/png;base64,{date_image}",
        n_glpi=f"data:image/png;base64,{n_glpi_file}",
        n_termo=f"data:image/png;base64,{n_termo_file}",
        ri_1=f"data:image/png;base64,{logo_file}",
        location=context.location,
        bu=context.bu,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(template_path, encoding="utf-8") as template_file:
        pdfkit.from_file(
            template_file,
            contract_path,
            options=options,
        )

    os.remove(template_path)
    return contract_path


def create_lending_contract_pj(context: NewLendingPjContextSchema) -> str:
    """Creates new lending contract"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template_file = "comodato_pj.html"
    template = template_env.get_template(template_file)
    signed_image = get_str_base64_image(SIGNED_DATE_IMAGE)
    date_image = get_str_base64_image(DATE_IMAGE)
    n_glpi_file = get_str_base64_image(GLPI_IMAGE)
    n_termo_file = get_str_base64_image(N_TERM_IMAGE)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        national_identification=context.national_identification,
        company=context.company,
        cnpj=context.cnpj,
        company_address=context.company_address,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        marital_status=context.marital_status,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        contract_date=context.contract_date,
        detail=context.detail,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
        signed=f"data:image/png;base64,{signed_image}",
        date_image=f"data:image/png;base64,{date_image}",
        n_glpi=f"data:image/png;base64,{n_glpi_file}",
        n_termo=f"data:image/png;base64,{n_termo_file}",
        ri_1=f"data:image/png;base64,{logo_file}",
        location=context.location,
        bu=context.bu,
        object=context.object,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(template_path, encoding="utf-8") as template_file:
        pdfkit.from_file(
            template_file,
            contract_path,
            options=options,
        )

    os.remove(template_path)
    return contract_path


def create_revoke_lending_contract_pj(context: NewLendingPjContextSchema) -> str:
    """Creates new lending contract"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template_file = "distrato_comodato_pj.html"
    template = template_env.get_template(template_file)
    signed_image = get_str_base64_image(SIGNED_DATE_IMAGE)
    date_image = get_str_base64_image(DATE_IMAGE)
    n_glpi_file = get_str_base64_image(GLPI_IMAGE)
    n_termo_file = get_str_base64_image(N_TERM_IMAGE)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        national_identification=context.national_identification,
        company=context.company,
        cnpj=context.cnpj,
        company_address=context.company_address,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        marital_status=context.manager,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        contract_date=context.contract_date,
        object=context.object,
        detail=context.detail,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
        signed=f"data:image/png;base64,{signed_image}",
        date_image=f"data:image/png;base64,{date_image}",
        n_glpi=f"data:image/png;base64,{n_glpi_file}",
        n_termo=f"data:image/png;base64,{n_termo_file}",
        ri_1=f"data:image/png;base64,{logo_file}",
        location=context.location,
        bu=context.bu,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(template_path, encoding="utf-8") as template_file:
        pdfkit.from_file(
            template_file,
            contract_path,
            options=options,
        )

    os.remove(template_path)
    return contract_path


def create_term(context: NewTermContextSchema, template_file="termo.html") -> str:
    """Creates new lending term"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template = template_env.get_template(template_file)
    signed_image = get_str_base64_image(SIGNED_DATE_IMAGE)
    date_image = get_str_base64_image(DATE_IMAGE)
    n_glpi_file = get_str_base64_image(GLPI_IMAGE)
    n_termo_file = get_str_base64_image(N_TERM_IMAGE)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        number=context.number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        national_identification=context.national_identification,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        cc=context.cc,
        manager=context.manager,
        project=context.project,
        detail=context.detail,
        date=context.date,
        signed=f"data:image/png;base64,{signed_image}",
        date_image=f"data:image/png;base64,{date_image}",
        n_glpi=f"data:image/png;base64,{n_glpi_file}",
        n_termo=f"data:image/png;base64,{n_termo_file}",
        ri_1=f"data:image/png;base64,{logo_file}",
        location=context.location,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    options = {"page-size": "A4", "enable-local-file-access": None, "encoding": "utf-8"}

    with open(template_path, encoding="utf-8") as file:
        pdfkit.from_file(
            file,
            contract_path,
            options=options,
        )

    os.remove(template_path)
    return contract_path
