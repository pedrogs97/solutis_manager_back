import json
import logging
from typing import List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from src.config import CLICKSIGN_TOKEN, CLICKSIGN_URL
from src.lending.service import LendingService
from src.utils import base64_str, mask_taxpayer_id


class ClickSignService:
    DEFAULT_HEADERS = {
        "Authorization": CLICKSIGN_TOKEN,
        "Content-Type": "application/vnd.api+json",
    }
    DEFAULT_ERROR = "Unknown error"

    MAPPING_PRINCIPAL_SIGNERS = {
        "beatriz.cunha@solutis.com.br": {
            "full_name": "BEATRIZ CUNHA DA SILVA",
            "taxpayer_id": "823.294.515-04",
            "birthday": "1983-10-17",
            "email": "beatriz.cunha@solutis.com.br",
        },
        "thomas.lichtenberger@solutis.com.br": {
            "full_name": "THOMAS MEDEIROS LICHTENBERGER",
            "taxpayer_id": "379.709.978-99",
            "birthday": "1989-04-04",
            "email": "thomas.lichtenberger@solutis.com.br",
        },
        "carla.anunciacao@solutis.com.br": {
            "full_name": "CARLA VIRGINIA MILHAS DA ANUNCIACAO",
            "taxpayer_id": "957.628.335-34",
            "birthday": "1976-11-04",
            "email": "carla.anunciacao@solutis.com.br",
        },
    }

    logger = logging.getLogger(__name__)

    def __create_envelop(self) -> Optional[str]:
        """
        Create a new envelope

        :Returns:
            envelope_id (str): The ID of the envelope
        """
        envelope_obj = {
            "data": {
                "type": "envelopes",
                "attributes": {
                    "name": "Meu Primeiro Envelope",
                    "locale": "pt-BR",
                    "auto_close": True,
                    "remind_interval": 3,
                    "block_after_refusal": True,
                },
            }
        }
        payload = json.dumps(envelope_obj)

        response = requests.request(
            "POST", CLICKSIGN_URL, headers=self.DEFAULT_HEADERS, data=payload
        )

        response_json = response.json()
        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error creating envelope: {error}",
            )
            return None
        return response_json["data"]["id"]

    def __create_document(
        self, envelope_id: str, filename: str, content: str
    ) -> Optional[str]:
        """
        Create a new document

        This document will be added to the envelope

        :Args:
            envelope_id (str): The ID of the envelope
            filename (str): The name of the file
            content (str): The content of the file in base64 format

        :Returns:
            document_id (str): The ID of the document
        """
        document_obj = {
            "data": {
                "type": "documents",
                "attributes": {
                    "filename": filename,
                    "content_base64": content,
                },
            }
        }
        payload = json.dumps(document_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/documents"

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)

        response_json = response.json()
        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error creating document: {error}",
            )
            return None
        return response_json["data"]["id"]

    def __cancel_document(self, envelope_id: str, document_id: str) -> bool:
        """
        Cancel a document

        This will cancel the document

        :Args:
            envelope_id (str): The ID of the envelope
            document_id (str): The ID of the document

        :Returns:
            document_canceled (bool): True if the document was canceled, False otherwise
        """
        cancel_obj = {
            "data": {
                "type": "documents",
                "attributes": {
                    "status": "canceled",
                },
                "id": document_id,
            }
        }
        payload = json.dumps(cancel_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/documents/{document_id}"

        response = requests.patch(url, data=payload, headers=self.DEFAULT_HEADERS)
        not_found = response.status_code == 404
        if not_found:
            return True
        response_json = response.json()

        if response.status_code == 422 and "errors" in response_json:
            error = response_json.get("errors")[0]
            if "code" in error:
                return error.get("code") == "100"
        document_canceled = response.status_code == 204
        if not document_canceled:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error canceling document: {error}",
            )

        return document_canceled

    def __create_signer(
        self, envelope_id: str, email: str, name: str, birthday: str, taxpayer_id: str
    ) -> Optional[str]:
        """
        Create a new signer

        This signer will be added to the envelope

        :Args:
            envelope_id (str): The ID of the envelope
            email (str): The email of the signer
            name (str): The name of the signer
            birthday (str): The birthday of the signer
            taxpayer_id (str): The taxpayer ID of the signer
        :Returns:
            signer_id (str): The ID of the signer
        """
        signer_obj = {
            "data": {
                "type": "signers",
                "attributes": {
                    "has_documentation": True,
                    "group": 1,
                    "location_required_enabled": True,
                    "communicate_events": {
                        "signature_request": "email",
                        "signature_reminder": "email",
                        "document_signed": "email",
                    },
                    "name": name,
                    "email": email,
                    "birthday": birthday,
                    "documentation": mask_taxpayer_id(taxpayer_id),
                },
            }
        }
        payload = json.dumps(signer_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/signers"

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)

        response_json = response.json()
        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error creating signer: {error}",
            )
            return None
        return response_json["data"]["id"]

    def __get_signers(self, envelope_id: str) -> Optional[List[dict]]:
        """
        Get all signers in the envelope

        This will return a list of signers in the envelope

        :Args:
            envelope_id (str): The ID of the envelope

        :Returns:
            signers (list): A list of signers
        """
        url = f"{CLICKSIGN_URL}/{envelope_id}/signers"
        response = requests.get(url, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 200:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.error(
                f"Error listing signers: {error}",
            )
            return None

        return [
            {
                "id": signer["id"],
                "email": signer["attributes"]["email"],
            }
            for signer in response_json["data"]
        ]

    def __delete_signer(self, envelope_id: str, signer_id: str) -> None:
        """
        Delete a signer from the envelope

        This will delete the signer from the envelope

        :Args:
            envelope_id (str): The ID of the envelope
            signer_id (str): The ID of the signer
        """
        url = f"{CLICKSIGN_URL}/{envelope_id}/signers/{signer_id}"
        response = requests.delete(url, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 204:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.error(
                f"Error deleting signer: {error}",
            )

    def __add_requirements(self, envelope_id: str, doc_id: str, signer_id: str) -> None:
        """
        Add requirements to the signer

        This will add the requirements to the signer

        :Args:
            envelope_id (str): The ID of the envelope
            doc_id (str): The ID of the document
            signer_id (str): The ID of the signer
        """
        requirements_obj = {
            "data": {
                "type": "requirements",
                "attributes": {
                    "action": "agree",
                    "role": "sign",
                },
                "relationships": {
                    "document": {
                        "data": {
                            "type": "documents",
                            "id": doc_id,
                        }
                    },
                    "signer": {
                        "data": {
                            "type": "signers",
                            "id": signer_id,
                        }
                    },
                },
            }
        }
        payload = json.dumps(requirements_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/requirements"

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error add requirements: {error}",
            )

    def __add_authorization(
        self, envelope_id: str, doc_id: str, signer_id: str
    ) -> None:
        """
        Add authorization to the signer

        This will add the authorization to the signer

        :Args:
            envelope_id (str): The ID of the envelope
            doc_id (str): The ID of the document
            signer_id (str): The ID of the signer
        """
        authorization_obj = {
            "data": {
                "type": "requirements",
                "attributes": {
                    "action": "provide_evidence",
                    "auth": "email",
                },
                "relationships": {
                    "document": {
                        "data": {
                            "type": "documents",
                            "id": doc_id,
                        }
                    },
                    "signer": {
                        "data": {
                            "type": "signers",
                            "id": signer_id,
                        }
                    },
                },
            }
        }
        payload = json.dumps(authorization_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/requirements"

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error add authorization: {error}",
            )

    def __add_observers(self, envelop_id: str) -> None:
        """
        Add observers to the envelope
        This will add the observers to the envelope

        :Args:
            envelope_id (str): The ID of the envelope

        :Returns:
            None
        """
        observers_to_add = [
            "brenner.pereira@solutis.com.br",
            "beatriz.cunha@solutis.com.br",
            "thomas.lichtenberger@solutis.com.br",
            "carla.anunciacao@solutis.com.br",
            "tais.santos@solutis.com.br",
            "tailon.souza@solutis.com.br",
            "kecia.sousa@solutis.com.br",
        ]

        for observer in observers_to_add:
            observers_obj = {
                "data": {
                    "type": "signature_watchers",
                    "attributes": {
                        "email": observer,
                        "kind": "on_finished",
                    },
                }
            }
            payload = json.dumps(observers_obj)
            url = f"{CLICKSIGN_URL}/{envelop_id}/signature_watchers"
            response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)
            response_json = response.json()
            if response.status_code != 201:
                error = response_json.get("errors", self.DEFAULT_ERROR)
                self.logger.log(
                    logging.ERROR,
                    f"Error add observers: {error}",
                )

    def __activate_envelope(self, envelope_id: str) -> None:
        """
        Activate the envelope

        This will activate the envelope

        :Args:
            envelope_id (str): The ID of the envelope
        """
        activate_obj = {
            "data": {
                "id": envelope_id,
                "type": "envelopes",
                "attributes": {
                    "status": "running",
                },
            }
        }
        payload = json.dumps(activate_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}"

        response = requests.patch(url, data=payload, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 200:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error add requirements: {error}",
            )

    def __send_notification(self, envelope_id: str, signer_id: str) -> None:
        """
        Send notification to the signer

        This will send the notification to the signer

        :Args:
            envelope_id (str): The ID of the envelope
            signer_id (str): The ID of the signer
        """
        notification_obj = {
            "data": {
                "type": "notifications",
                "attributes": {},
            }
        }
        payload = json.dumps(notification_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/signers/{signer_id}/notifications"

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        if response.status_code != 201:
            error = response_json.get("errors", self.DEFAULT_ERROR)
            self.logger.log(
                logging.ERROR,
                f"Error add requirements: {error}",
            )

    def send_document_to_sign(
        self,
        filename: str,
        file_path: str,
        signer_email: str,
        principal_signer: str,
        full_name: str,
        taxpayer_id: str,
        birthday: str,
        witnesses: List[dict] = [],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Send a document to be signed

        This will create an envelope, add a document, add a signer,
        add requirements, add authorization, activate the envelope
        and send notification to the signer

        :Args:
            filename (str): The name of the file
            file_path (str): The path to the file
            signer_email (str): The email of the signer
            principal_signer (str): The email of the principal signer
            full_name (str): The full name of the signer
            taxpayer_id (str): The taxpayer ID of the signer
            birthday (str): The birthday of the signer
            witnesses (List[dict]): A list of witnesses with their information
        :Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the envelope ID and document ID
        """
        envelope_id = self.__create_envelop()
        if not envelope_id:
            return None, None

        with open(file_path, "rb") as file:
            content = f"data:application/pdf;base64,{base64_str(file.read())}"
            document_id = self.__create_document(envelope_id, filename, content)

        if not document_id:
            return None, None

        signer_id = self.__create_signer(
            envelope_id, signer_email, full_name, birthday, taxpayer_id
        )
        # comodante
        principal_signer_id = self.__create_signer(
            envelope_id, principal_signer, full_name, birthday, taxpayer_id
        )

        if not signer_id:
            return None, None

        if not principal_signer_id:
            return None, None

        signers_to_notify = [signer_id]

        if len(witnesses) > 0:
            for witness in witnesses:
                witness_email = witness.get("email")
                witness_name = witness.get("full_name")
                witness_birthday = witness.get("birthday")
                witness_taxpayer_id = witness.get("taxpayer_id")

                if not any(
                    [witness_email, witness_name, witness_birthday, witness_taxpayer_id]
                ):
                    self.logger.log(
                        logging.ERROR,
                        "Missing witness information. Skipping witness.",
                    )
                    continue
                witness_id = self.__create_signer(
                    envelope_id,
                    witness_email,
                    witness_name,
                    witness_birthday,
                    witness_taxpayer_id,
                )
                if not witness_id:
                    continue
                self.__add_authorization(envelope_id, document_id, witness_id)
                self.__add_requirements(envelope_id, document_id, witness_id)
                signers_to_notify.append(witness_id)

        self.__add_requirements(envelope_id, document_id, signer_id)
        self.__add_authorization(envelope_id, document_id, signer_id)
        self.__activate_envelope(envelope_id)
        self.__add_observers(envelope_id)
        for id in signers_to_notify:
            self.__send_notification(envelope_id, id)

        return envelope_id, document_id

    def send_recreated_document_to_sign(
        self,
        document_id: str,
        envelope_id: str,
        filename: str,
        file_path: str,
        signer_email: str,
        principal_signer: str,
        lending_id: int,
        db_session: Session,
    ) -> Optional[str]:
        """
        Send a recreated document to be signed

        This will create an envelope, add a document, add a signer,
        add requirements, add authorization, activate the envelope
        and send notification to the signer

        :Args:
            document_id (str): The ID of the document to be recreated
            envelope_id (str): The ID of the envelope
            filename (str): The name of the file
            file_path (str): The path to the file
            signer_email (str): The email of the signer
            principal_signer (str): The email of the principal signer

        :Returns:
            Optional[str]: The ID of the new document
        """
        if not self.__cancel_document(envelope_id, document_id):
            return None

        with open(file_path, "rb") as file:
            content = f"data:application/pdf;base64,{base64_str(file.read())}"
            new_document_id = self.__create_document(envelope_id, filename, content)

        all_signer_to_resend = self.__get_signers(envelope_id)
        if not all_signer_to_resend:
            return None

        lending = LendingService().get_lending(lending_id, db_session)
        if not lending:
            self.logger.error(
                f"Lending with ID {lending_id} not found. Cannot recreate document.",
            )
            return None

        is_diff_signer = lending.employee_signer != signer_email
        is_diff_principal_signer = lending.principal_signer != principal_signer

        for signer in all_signer_to_resend:
            principal_signer_dict = self.MAPPING_PRINCIPAL_SIGNERS.get(
                signer["email"], None
            )
            signer_id = signer.get("id")
            if not signer_id or not new_document_id:
                self.logger.error(
                    "Missing signer information. Skipping signer.",
                )
                continue
            if is_diff_signer and signer["email"] == lending.employee_signer:
                lending = LendingService().get_lending(lending_id, db_session)
                self.__delete_signer(envelope_id, signer_id)
                signer_id = self.__create_signer(
                    envelope_id,
                    signer_email,
                    lending.employee.full_name,
                    lending.employee.birthday.isoformat(),
                    lending.employee.taxpayer_identification,
                )
                if not signer_id:
                    self.logger.error(
                        "Failed to create principal signer. Skipping signer.",
                    )
                    continue
            elif (
                principal_signer_dict
                and is_diff_principal_signer
                and signer["email"] == principal_signer_dict.get("email")
            ):
                lending = LendingService().get_lending(lending_id, db_session)
                self.__delete_signer(envelope_id, signer_id)
                signer_id = self.__create_signer(
                    envelope_id,
                    principal_signer,
                    principal_signer_dict.get("full_name", ""),
                    principal_signer_dict.get("birthday", ""),
                    principal_signer_dict.get("taxpayer_id", ""),
                )
                if not signer_id:
                    self.logger.error(
                        "Failed to create principal signer. Skipping signer.",
                    )
                    continue
            self.__add_authorization(envelope_id, new_document_id, signer_id)
            self.__add_requirements(envelope_id, new_document_id, signer_id)
            self.__send_notification(envelope_id, signer_id)

        return new_document_id
