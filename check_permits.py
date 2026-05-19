"""
Posio kanalintulupa -saatavuusmonitori
Tarkistaa onko Posion kanalintulupa (product 5, area 744) saatavilla eraluvat.fi:ssä.
Lähettää ntfy.sh-push-ilmoituksen kun lupia vapautuu.
"""
import urllib.request
import json
import sys
import subprocess
from datetime import datetime

API_URL = "https://api.eraluvat.fi/orders/v1/keywords/areas/744?locale=fi"
PRODUCT_ID = 5  # Kanalintulupa
NTFY_TOPIC = "posio-kanalintulupa-2620"
PURCHASE_URL = "https://www.eraluvat.fi/kohteet/2620-posio-744/tuotteet/kanalintulupa-5"


def check_availability():
    req = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://www.eraluvat.fi",
            "Referer": "https://www.eraluvat.fi/",
        },
    )
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    products = data.get("products", [])
    kanalintulupa = next((p for p in products if p.get("id") == PRODUCT_ID), None)
    if not kanalintulupa:
        return None
    return kanalintulupa.get("permitsAvailable", 0)


def send_alert(available):
    message = (
        f"Kanalintulupa: {available} lupaa vapaana! "
        f"Osta heti: {PURCHASE_URL}"
    )
    subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            f"https://ntfy.sh/{NTFY_TOPIC}",
            "-H", "Title: 🦌 LUPIA SAATAVILLA - Posio!",
            "-H", "Priority: urgent",
            "-H", "Tags: tada",
            "-d", message,
        ],
        check=True,
    )


def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Tarkistetaan saatavuus...")

    try:
        available = check_availability()
    except Exception as e:
        print(f"VIRHE API-kutsussa: {e}")
        sys.exit(1)

    if available is None:
        print("VIRHE: Kanalintulupa-tuotetta ei löydy API:sta (product id=5)")
        sys.exit(1)

    print(f"permitsAvailable: {available}")

    if available > 0:
        print(f"*** LUPIA SAATAVILLA: {available} kpl — lähetetään ilmoitus! ***")
        try:
            send_alert(available)
            print("Push-ilmoitus lähetetty ntfy.sh-kanavalle.")
        except Exception as e:
            print(f"VIRHE ilmoituksen lähetyksessä: {e}")
            sys.exit(1)
    else:
        print("Ei lupia saatavilla tällä hetkellä.")


if __name__ == "__main__":
    main()
