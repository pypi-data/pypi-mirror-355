# IBAN Oplata API client ✍

[![PyPI](https://img.shields.io/pypi/v/iban-oplata?style=flat-square)](https://pypi.python.org/pypi/iban-oplata/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/iban-oplata?style=flat-square)](https://pypi.python.org/pypi/iban-oplata/)
[![PyPI - License](https://img.shields.io/pypi/l/iban-oplata?style=flat-square)](https://pypi.python.org/pypi/iban-oplata/)

---
**Documentation**: [https://docs.google.com/document/d/1u4pARzom4oM9gYB7yGd_W5upJSvEk9KJNSc-K0XpMy0/edit?tab=t.0#heading=h.hnxvx03248a6](https://docs.google.com/document/d/1u4pARzom4oM9gYB7yGd_W5upJSvEk9KJNSc-K0XpMy0/edit?tab=t.0#heading=h.hnxvx03248a6)

**Source Code**: [https://github.com/DmytroLitvinov/python-iban-oplata](https://github.com/DmytroLitvinov/python-iban-oplata)

**PyPI**: [https://pypi.org/project/iban-oplata/](https://pypi.org/project/iban-oplata/)

---

Python API wrapper around IBAN Oplata API. Feel free to contribute and make it better! 🚀


## Installation

```sh
pip install iban-oplata
```

## Usage 

1) Create your account at [IBAN Oplata](https://ibanoplata.com/) and generate [API token](https://ibanoplata.com/api-token). 

2) Use that token to initialize client:

```python
from iban_oplata import IBANOplataAPIClient

token = 'your_api_token_here'

dummy_data = {
    'organization_name': 'Test organization',
    'identification_code': '12345678',
    'iban': 'UA213223130000026007233566001',
    'amount': 100.75,
    'payment_purpose': 'Test invoice via iban-oplata python SDK',
}

iban_oplata = IBANOplataAPIClient(token)

response = iban_oplata.create_invoice(dummy_data)
iban_invoice_url = response.data['ibanInvoiceUrl']
print(f'IBAN Invoice URL: {iban_invoice_url}')
```

## License

This project is licensed under the terms of the [MIT license](https://github.com/DmytroLitvinov/python-iban-oplata/blob/master/LICENSE).


### HOW TO MAKE A RELEASE

Prepare build packages:
* pip install build
* pip install twine

* Add changes to `CHANGELOG.md`
* Change version in `iban_oplata/__init__.py` and `pyproject.toml`
* `source .env/bin/activate`
* `python3 -m build --sdist --wheel`
* `twine upload dist/*`
