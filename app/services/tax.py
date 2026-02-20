"""
Washington State sales tax lookup via DOR Address Rates API.
https://dor.wa.gov/taxes-rates/sales-and-use-tax-rates/address-based-lookup-tool
"""
import requests
import urllib.parse


WA_TAX_API = 'https://webgis.dor.wa.gov/webapi/AddressRates.aspx'


def lookup_wa_tax(street: str, city: str, zip_code: str) -> dict | None:
    """
    Look up WA sales tax for a given address.
    Returns dict with 'code' (location code) and 'rate' (combined rate as decimal),
    or None if lookup fails.
    """
    if not street or not city:
        return None

    params = {
        'output': 'json',
        'addr': street,
        'city': city,
        'zip': zip_code or '',
    }

    try:
        resp = requests.get(WA_TAX_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # WA DOR API returns ResultCode 0 = success
        if data.get('ResultCode') == 0 or str(data.get('ResultCode', '')) == '0':
            rate = float(data.get('Rate', 0))
            code = str(data.get('LocationCode', ''))
            return {'code': code, 'rate': rate}

        # Some versions use AddressResults array
        results = data.get('AddressResults', [])
        if results:
            r = results[0]
            rate = float(r.get('Rate', 0))
            code = str(r.get('LocationCode', ''))
            return {'code': code, 'rate': rate}

    except (requests.RequestException, ValueError, KeyError):
        pass

    return None


def format_tax_rate(rate: float) -> str:
    """Return rate as percentage string, e.g. 0.106 -> '10.6%'"""
    return f'{rate * 100:.1f}%'
