"""Base utils"""

import base64
import os
from datetime import datetime
from json import loads
from os import listdir
from pathlib import Path
from typing import Tuple

import aiofiles
import jinja2
from loguru import logger

from src.config import CONTRACT_UPLOAD_DIR, TEMPLATE_DIR, TERM_UPLOAD_DIR, TMP_DIR
from src.document.schemas import (
    NewLendingContextSchema,
    NewLendingPjContextSchema,
    NewTermContextSchema,
    VerificationContextSchema,
)

try:
    from weasyprint import HTML

    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint não está disponível: {e}")
    print("Por favor, instale as dependências do WeasyPrint para Windows.")
    raise e


def generate_pdf_from_html(
    html_file_path: str,
    pdf_output_path: str,
) -> None:
    """Generate PDF from HTML file using WeasyPrint"""
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint não está disponível. "
            "Instale as dependências necessárias para gerar PDFs."
        )
    HTML(filename=html_file_path).write_pdf(pdf_output_path)


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


def read_file_as_bytes(file_path: str) -> bytes:
    """Return the content of a file as bytes"""
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(path_obj, "rb") as file:
        return file.read()


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
    logger.info(f"Getting base64 for image: {file_name}")
    with open(file_name, "rb") as image:
        file_bytes = image.read()
        logger.info(f"Read {len(file_bytes)} bytes from image file.")
        str_base64 = (
            str(base64.b64encode(file_bytes)).replace("b'", "").replace("'", "")
        )
    logger.info(f"Generated base64 string of length: {len(str_base64)}")
    return str_base64


def get_image_to_pdf(file_name: str) -> str:
    """Get image base64 string"""
    str_base64 = ""
    file_extension = file_name.split(".")[-1]
    with open(file_name, "rb") as image:
        str_base64 = (
            str(base64.b64encode(image.read())).replace("b'", "").replace("'", "")
        )
    return f"data:image/{file_extension};base64,{str_base64}"


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
        verifications=context.verifications,
        attachments=context.attachments_files,
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    template_path = os.path.join(lending_path, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    generate_pdf_from_html(template_path, contract_path)

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

    generate_pdf_from_html(template_path, contract_path)

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

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    template_path = os.path.join(TMP_DIR, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    generate_pdf_from_html(template_path, contract_path)

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
        marital_status=context.marital_status,
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

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    template_path = os.path.join(TMP_DIR, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    generate_pdf_from_html(template_path, contract_path)

    os.remove(template_path)
    return contract_path


def create_term(context: NewTermContextSchema, template_file="termo.html") -> str:
    """Creates new lending term"""
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    ).get_template(template_file)
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

    is_revoke = "distrato" in template_file

    if not os.path.exists(TERM_UPLOAD_DIR):
        os.mkdir(TERM_UPLOAD_DIR)

    lending_path = os.path.join(TERM_UPLOAD_DIR, is_revoke and "revoke" or "term")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    template_path = os.path.join(TMP_DIR, f"template_{context.number}.html")
    contract_path = os.path.join(lending_path, f"{context.number}.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    generate_pdf_from_html(template_path, contract_path)

    os.remove(template_path)
    return contract_path


def create_verification_document(context: VerificationContextSchema) -> str:
    """Creates new verification document"""
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    )
    template_file = "verification.html"
    template = template_env.get_template(template_file)
    logo_file = get_str_base64_image(LOGO_IMAGE)
    output_text = template.render(
        verifications=context.verifications,
        logo=f"data:image/png;base64,{logo_file}",
    )

    lending_path = os.path.join(CONTRACT_UPLOAD_DIR, "lending")

    if not os.path.exists(lending_path):
        os.mkdir(lending_path)

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    template_path = os.path.join(
        TMP_DIR, f"template_{context.number}_verification.html"
    )
    contract_path = os.path.join(lending_path, f"{context.number} - verificação.pdf")

    with open(template_path, "w", encoding="utf-8") as html_file:
        html_file.write(output_text)

    generate_pdf_from_html(template_path, contract_path)

    os.remove(template_path)
    return contract_path


def get_start_and_end_datetime(
    start_date: str, end_date: str
) -> Tuple[datetime, datetime]:
    """Get start and end datetime"""
    start_datetime = datetime.strptime(f"{start_date} 23:59", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")
    return (start_datetime, end_datetime)


def base64_str(data: bytes) -> str:
    """Convert bytes to base64 string"""
    return str(base64.b64encode(data)).replace("b'", "").replace("'", "")


def mask_taxpayer_id(taxpayer: str) -> str:
    """Mask taxpayer id"""
    if "." in taxpayer:
        return taxpayer
    if len(taxpayer) == 11:
        return f"{taxpayer[:3]}.{taxpayer[3:6]}.{taxpayer[6:9]}-{taxpayer[9:]}"
    if len(taxpayer) == 14:
        return f"{taxpayer[:2]}.{taxpayer[2:5]}.{taxpayer[5:8]}/{taxpayer[8:12]}-{taxpayer[12:]}"
    return taxpayer
