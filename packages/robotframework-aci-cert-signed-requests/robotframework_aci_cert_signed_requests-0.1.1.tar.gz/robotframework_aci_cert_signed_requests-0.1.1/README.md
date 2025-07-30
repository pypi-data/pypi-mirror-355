# robotframework-aci-cert-signed-requests

A Robot Framework library that allows sending certificate-signed HTTP requests to Cisco ACI using signature-based authentication.

## Installation

```bash
pip install robotframework-aci-cert-signed-requests
```

## Usage

```robot
Library    aci_cert_signed_requests

*** Variables ***
${APIC_URL}    https://10.0.0.1
${CERT_DN}     uni/userext/user-fu/usercert-fu
${KEY_PATH}    path/to/private.key

*** Test Cases ***
Example
    ${resp}=    Get With Signature    ${APIC_URL}    ${CERT_DN}    ${KEY_PATH}    /api/mo/uni.json
    Log    ${resp.status_code}
```
