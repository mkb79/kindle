import logging
from typing import Dict, Optional


logger = logging.getLogger("kindle.localization")

LOCALE_TEMPLATES = {
    "germany": {
        "country_code": "de",
        "domain": "de",
        "language": "de-DE"
    },
    "united_states": {
        "country_code": "us",
        "domain": "com",
        "language": "en-US"
    },
    "united_kingdom": {
        "country_code": "uk",
        "domain": "co.uk",
        "language": "en-GB"
    },
    "france": {
        "country_code": "fr",
        "domain": "fr",
        "language": "fr-fr"
    },
    "canada": {
        "country_code": "ca",
        "domain": "ca",
        "language": "en-CA"
    },
    "italy": {
        "country_code": "it",
        "domain": "it",
        "language": "it"
    },
    "australia": {
        "country_code": "au",
        "domain": "com.au",
        "language": "en-AU"
    },
    "india": {
        "country_code": "in",
        "domain": "in",
        "language": ""
    },
    "japan": {
        "country_code": "jp",
        "domain": "co.jp",
        "language": "ja"
    },
    "spain": {
        "country_code": "es",
        "domain": "es",
        "language": "es-ES"
    }
}


def search_template(key: str, value: str) -> Optional[Dict[str, str]]:
    for country in LOCALE_TEMPLATES:
        locale = LOCALE_TEMPLATES[country]
        if locale[key] == value:
            logger.debug(f"found locale for {country}")
            return locale

    logger.info(f"don\'t found {value} in {key}")
    return None


class Locale:
    """
    Adjustments for the different marketplaces who are provided by Audible.
    
    """

    def __init__(
            self,
            country_code: Optional[str] = None,
            domain: Optional[str] = None,
            language: Optional[str] = None
    ) -> None:

        if not all([country_code, domain, language]):
            locale = None
            if country_code:
                locale = search_template("country_code", country_code)
            elif domain:
                locale = search_template("domain", domain)

            if locale is None:
                raise Exception("can\'t find locale")

        self._country_code = country_code or locale["country_code"]
        self._domain = domain or locale["domain"]
        self._language = language or locale["language"]

    def __repr__(self):
        return (
            f"Locale class for domain: {self.domain}"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "country_code": self.country_code,
            "domain": self.domain,
            "language": self.language
        }

    @property
    def country_code(self) -> str:
        return self._country_code

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def language(self) -> str:
        return self._language
