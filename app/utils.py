"""Base utils"""
import os
from os import listdir
from json import loads
import jinja2
import aiofiles
import pdfkit
from app.config import UPLOAD_DIR, TEMPLATE_DIR
from app.lending.schemas import NewLendingContextSchema, NewLendingPjContextSchema


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


async def upload_file(file_name: str, type_file: str, data: bytes) -> str:
    """Upload a file and returns file path"""
    folder_file = os.path.join(UPLOAD_DIR, type_file)

    if not os.path.isdir(folder_file):
        os.mkdir(folder_file)

    file_path = os.path.join(folder_file, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(data)  # async write chunk

    return file_path


def create_lending_contract(context: NewLendingContextSchema) -> str:
    """Creates new lending contract"""
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "comodato.html"
    template = template_env.get_template(template_file)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        nacional_identification=context.nacional_identification,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        matrimonial_status=context.manager,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        register_number=context.register_number,
        serial_number=context.serial_number,
        description=context.description,
        accessories=context.accessories,
        ms_office=context.ms_office,
        pattern=context.pattern,
        operational_system=context.operational_system,
        value=context.value,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
    )

    lending_path = os.path.join(UPLOAD_DIR, "lending")

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
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "comodato.html"
    template = template_env.get_template(template_file)
    output_text = template.render(
        number=context.number,
        glpi_number=context.glpi_number,
        full_name=context.full_name,
        taxpayer_identification=context.taxpayer_identification,
        nacional_identification=context.nacional_identification,
        company=context.company,
        cnpj=context.cnpj,
        company_address=context.company_address,
        address=context.address,
        nationality=context.nationality,
        role=context.role,
        matrimonial_status=context.manager,
        cc=context.cc,
        manager=context.manager,
        business_executive=context.business_executive,
        project=context.project,
        workload=context.workload,
        date_confirm=context.date_confirm,
        goal=context.goal,
        register_number=context.register_number,
        serial_number=context.serial_number,
        description=context.description,
        accessories=context.accessories,
        ms_office=context.ms_office,
        pattern=context.pattern,
        operational_system=context.operational_system,
        value=context.value,
        date=context.date,
        witnesses=[witness.model_dump() for witness in context.witnesses],
    )

    lending_path = os.path.join(UPLOAD_DIR, "lending")

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
