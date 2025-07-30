from robot.api.deco import keyword
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AciCertSignedRequests:
    @keyword
    def get_with_signature(self, apic_url, cert_dn, key_path, endpoint, params=None):
        method = "GET"
        signed_url = endpoint
        if params:
            if isinstance(params, str):
                params_dict = dict(x.split("=", 1) for x in params.split("&"))
            else:
                params_dict = params
            query = "&".join([f"{k}={v}" for k, v in params_dict.items()])
            signed_url = f"{endpoint}?{query}"
        else:
            params_dict = None

        data_to_sign = f"{method}{signed_url}".encode("utf-8")

        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)

        signature = private_key.sign(
            data_to_sign,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        signature_b64 = base64.b64encode(signature).decode("utf-8")

        cookies = {
            "APIC-Request-Signature": signature_b64,
            "APIC-Certificate-DN": cert_dn,
            "APIC-Certificate-Algorithm": "v1.0"
        }

        url = apic_url + endpoint
        response = requests.get(url, cookies=cookies, params=params_dict, verify=False)
        response.raise_for_status()
        return response
