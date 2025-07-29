import base64
import logging
from typing import Literal
from urllib.parse import urljoin

from iban_oplata import __version__

import requests

from iban_oplata.enum import HttpMethod
from iban_oplata.exceptions import IBANOplataException
from iban_oplata.response import IBANOplataAPIResponse
from iban_oplata.typed_dict import IBANOplataCreateInvoiceDict

logger = logging.getLogger('iban_oplata')


__all__ = ('IBANOplataAPIClient',)

API_VERSION_V1 = 'v1'
API_VERSION_V2 = 'v2'


class IBANOplataAPIClient:
    """
    Documentation:
    * V1 - https://docs.google.com/document/d/1u4pARzom4oM9gYB7yGd_W5upJSvEk9KJNSc-K0XpMy0/edit?tab=t.0#heading=h.hnxvx03248a6
    * V2 - https://docs.google.com/document/d/1u4pARzom4oM9gYB7yGd_W5upJSvEk9KJNSc-K0XpMy0/edit?tab=t.0#heading=h.opamuhdgxajx
    """

    DEFAULT_HEADERS = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'user-agent': f'python-iban-oplata/{__version__} | (https://github.com/DmytroLitvinov/python-iban-oplata)',
    }

    def __init__(self, token=None, user=None, password=None, api_version: Literal['v1', 'v2'] = 'v2'):
        if api_version not in ('v1', 'v2'):
            raise ValueError(f'Invalid API version: {api_version}. Supported versions are v1 and v2.')

        if api_version == API_VERSION_V1:
            if not user or not password:
                raise ValueError('User and password must be provided for API version v1.')

        elif api_version == API_VERSION_V2 and not token:
            raise ValueError('Token must be provided for API version v2.')

        self.api_version = api_version
        self.endpoint = f'https://api.ibanoplata.com/{api_version}/'

        if self.api_version == API_VERSION_V1:
            self.user = user
            self.password = password
            base64_basic_auth_token = base64.b64encode(f'{self.user}:{self.password}'.encode()).decode('utf-8')
            self.base64_basic_auth_token = base64_basic_auth_token
        elif self.api_version == API_VERSION_V2:
            self.token = token

    def _get_headers(self):
        headers = self.DEFAULT_HEADERS.copy()
        if self.api_version == API_VERSION_V1:
            headers.update({'Authorization': f'Basic {self.base64_basic_auth_token}'})
        elif self.api_version == API_VERSION_V2:
            headers.update({'X-Api-Key': f'{self.token}'})
        return headers

    def _request(self, method: HttpMethod, path: str, body: dict = dict) -> IBANOplataAPIResponse:
        """
        Fetches the given path in the IBAN Oplata API.
        :param path: Api path
        :param body: body of request
        :return: Serialized server response or error
        """
        url = urljoin(self.endpoint, path)
        headers = self._get_headers()

        logger.debug(f'Making {method} request to {url} with headers {headers} and body {body}')
        # https://github.com/psf/requests/issues/3070
        response = requests.request(method.value, url, headers=headers, json=body, timeout=10)
        logger.debug(f'Received response with status code {response.status_code} and body {response.text}')

        if response.status_code == 401:  # noqa: PLR2004
            raise IBANOplataException('Invalid credentials', response.status_code)

        return IBANOplataAPIResponse(response.json(), response.status_code)

    def create_invoice(self, data: IBANOplataCreateInvoiceDict):
        path = 'iban-invoice'
        body = {
            'organizationName': data['organization_name'],
            'identificationCode': data['identification_code'],
            'iban': data['iban'],
            'amount': data['amount'],
            'paymentPurpose': data['payment_purpose'],
        }
        return self._request(HttpMethod.POST, path, body=body)
