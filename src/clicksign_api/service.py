import json
import logging
from typing import List, Optional, Tuple

import requests

from src.config import CLICKSIGN_TOKEN, CLICKSIGN_URL
from src.utils import base64_str, mask_taxpayer_id


class ClickSignService:
    DEFAULT_HEADERS = {
        "Authorization": CLICKSIGN_TOKEN,
        "Content-Type": "application/vnd.api+json",
    }
    DEFAULT_ERROR = "Unknown error"

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
            }
        }
        payload = json.dumps(cancel_obj)
        url = f"{CLICKSIGN_URL}/{envelope_id}/documents/{document_id}"

        response = requests.patch(url, data=payload, headers=self.DEFAULT_HEADERS)
        response_json = response.json()

        document_canceled = response.status_code != 200
        if document_canceled:
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
            self.logger.log(
                logging.ERROR,
                f"Error listing signers: {error}",
            )
            return None

        return [
            {
                "id": signer["id"],
            }
            for signer in response_json["data"]
        ]

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
        if not signer_id:
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
    ) -> Optional[str]:
        """
        Send a recreated document to be signed

        This will create an envelope, add a document, add a signer,
        add requirements, add authorization, activate the envelope
        and send notification to the signer
        """
        if not self.__cancel_document(envelope_id, document_id):
            return None

        with open(file_path, "rb") as file:
            content = f"data:application/pdf;base64,{base64_str(file.read())}"
            new_document_id = self.__create_document(envelope_id, filename, content)

        all_signer_to_resend = self.__get_signers(envelope_id)
        if not all_signer_to_resend:
            return None
        for signer in all_signer_to_resend:
            signer_id = signer.get("id")
            if not signer_id:
                self.logger.log(
                    logging.ERROR,
                    "Missing signer information. Skipping signer.",
                )
                continue
            self.__add_authorization(envelope_id, new_document_id, signer_id)
            self.__add_requirements(envelope_id, new_document_id, signer_id)
            self.__send_notification(envelope_id, signer_id)

        return new_document_id
