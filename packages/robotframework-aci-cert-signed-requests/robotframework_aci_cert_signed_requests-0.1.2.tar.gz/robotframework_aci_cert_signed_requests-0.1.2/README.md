# robotframework-aci-cert-signed-requests

**Robot Framework library for sending certificate-signed REST API requests to Cisco ACI.**

This library enables signature-based authentication (certificate + private key) for interacting with Cisco ACI APIs, useful when local users and passwords are not used or disabled.

---

## 🏦 Installation

```bash
pip install robotframework-aci-cert-signed-requests
```

This library depends on:

* `robotframework`
* `requests`
* `cryptography`

These will be installed automatically if not already present.

---

## 📚 Usage

### Library Import

```robot
Library    robotframework_aci_cert_signed_requests.AciSignatureAuthentication
```

### Variables

```robot
*** Variables ***
${APIC_URL}     https://10.0.0.1
${CERT_DN}      uni/userext/user-fu/usercert-fu
${KEY_PATH}     path/to/private.key
```

### Test Case Example

```robot
*** Test Cases ***
Example With Signature
    ${resp}=    Get With SignatureBasedAuth    ${APIC_URL}    ${CERT_DN}    ${KEY_PATH}    /api/mo/uni.json
    Log    ${resp.status_code}
```

---

## 🔐 Keyword Reference

### `Get With SignatureBasedAuth`

**Arguments**:

* `${apic_url}` – Full APIC URL (e.g. `https://10.0.0.1`)
* `${cert_dn}` – APIC certificate DN (e.g. `uni/userext/user-xyz/usercert-xyz`)
* `${key_path}` – Path to the private `.key` file
* `${api_endpoint}` – API endpoint (e.g. `/api/mo/uni.json`)
* `params=...` – Optional query parameters

**Returns**: A standard `requests.Response` object

---

## 🧪 Example Use Case

This library is useful when:

* Using `local-user` certificate authentication to ACI
* Automating snapshot creation or cleanup via API
* Verifying API reachability during CI/CD pipelines
