import logging
from typing import Callable

from certbot.plugins.dns_common import DNSAuthenticator

import loopia_api as loopia

logger = logging.getLogger(__name__)


class LoopiaDnsAuthenticator(DNSAuthenticator):

    description = (
        "Obtain certificates using a DNS TXT record (if you are using Loopia DNS)."
    )

    @classmethod
    def add_parser_arguments(
        cls,
        add: Callable[..., None],
        default_propagation_seconds: int = 300,
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="Loopia API credentials file", default=None)

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "Loopia API credentials file",
            {
                "username": "Loopia API username",
                "password": "Loopia API password",
            },
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        username = self.credentials.conf("username") or ""
        password = self.credentials.conf("password") or ""

        loopia.add_zone_record(
            username=username,
            password=password,
            domain=domain,
            subdomain=self._get_subdomain(validation_name),
            record=loopia.LoopiaApiRecordObj(
                record_type="TXT",
                ttl=300,
                priority=0,
                data=validation,
            ),
        )

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        subdomain = self._get_subdomain(validation_name)
        username = self.credentials.conf("username") or ""
        password = self.credentials.conf("password") or ""
        record_id = loopia.find_zone_record_id(
            username=username,
            password=password,
            domain=domain,
            subdomain=subdomain,
            record_type="TXT",
            value=validation,
        )

        if record_id is None:
            logger.warning(
                f"Could not find record ID for {validation_name} in domain {domain}. Skipping cleanup."
            )
            return

        loopia.remove_zone_record(
            username=username,
            password=password,
            domain=domain,
            subdomain=subdomain,
            record_id=record_id,
        )

    def _get_subdomain(self, domain: str) -> str:
        return domain.split(".")[0] if "." in domain else domain
