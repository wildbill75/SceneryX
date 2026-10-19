import sys
import requests

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"


def verify_license(license_key: str, payload_params: dict, label: str):
    print(f"\n--- Testing [{label}] ---")
    print("Request Payload:", payload_params)
    response = requests.post(
        GUMROAD_VERIFY_URL,
        data=payload_params,
        headers={"Accept": "application/json"},
        timeout=10,
    )
    print("DEBUG GUMROAD RESPONSE:", response.status_code, response.text)
    return response


if __name__ == "__main__":
    key = sys.argv[1].strip() if len(sys.argv) > 1 else input("Enter a Gumroad license key to test: ").strip()

    # 1. Exact payload currently sent by installer/SceneryX_Setup.iss (Line 211)
    verify_license(
        key,
        {
            "product_permalink": "sceneryx",
            "license_key": key,
            "increment_uses_count": "false",
        },
        "Current SceneryX_Setup.iss (product_permalink='sceneryx')",
    )

    # 2. Using actual URL slug from https://sidestickpriority.gumroad.com/l/zzlsus
    verify_license(
        key,
        {
            "product_permalink": "zzlsus",
            "license_key": key,
            "increment_uses_count": "false",
        },
        "Actual URL Slug (product_permalink='zzlsus')",
    )

    # 3. Using Gumroad API v2 required product_id for products created after Jan 9, 2023
    verify_license(
        key,
        {
            "product_id": "IFBvOgJBf93MMvBUDofAPQ==",
            "license_key": key,
            "increment_uses_count": "false",
        },
        "Gumroad API v2 Product ID (product_id='IFBvOgJBf93MMvBUDofAPQ==')",
    )
