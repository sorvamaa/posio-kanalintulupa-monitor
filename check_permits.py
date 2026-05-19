"""
Posio kanalintulupa - saatavuusmonitori paivamaarakohtaisesti
Tarkistaa onko Posion kanalintupaa saatavilla paiville 10.-17.9.2026.
Lahettaa ntfy.sh-push-ilmoituksen kun lupia vapautuu.
"""
import urllib.request
import urllib.parse
import json
import sys
import subprocess
from datetime import datetime
 
AREA_ID = 744
PRODUCT_ID = 5
NTFY_TOPIC = "posio-kanalintulupa-2620"
PURCHASE_URL = "https://www.eraluvat.fi/kohteet/2620-posio-744/tuotteet/kanalintulupa-5"
 
# Seurantajakso: 10.-17.9.2026 (UTC: Suomi on UTC+3 kesalla)
CALENDAR_FROM = "2026-09-09T21:00:00Z"
CALENDAR_TO   = "2026-09-17T21:00:00Z"
 
CALENDAR_URL = (
    "https://api.eraluvat.fi/orders/v1/areas/{}/products/{}/calendar"
    "?duration=P1D&from={}&to={}"
).format(AREA_ID, PRODUCT_ID,
         urllib.parse.quote(CALENDAR_FROM),
         urllib.parse.quote(CALENDAR_TO))
 
GUEST_URL = "https://www.eraluvat.fi/"
 
 
def get_guest_id():
    """Hakee x-era-guest-id cookien eraluvat.fi:lta."""
    req = urllib.request.Request(
        GUEST_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp = urllib.request.urlopen(req, timeout=10)
    for header, value in resp.headers.items():
        if header.lower() == "set-cookie" and "x-era-guest-id" in value:
            for part in value.split(";"):
                if "x-era-guest-id" in part:
                    return part.split("=", 1)[1].strip()
    return None
 
 
def check_availability(guest_id):
    """Hakee paivakohtaisen saatavuuden 10.-17.9.2026."""
    req = urllib.request.Request(
        CALENDAR_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://www.eraluvat.fi",
            "Referer": "https://www.eraluvat.fi/",
            "x-era-guest-id": guest_id,
        },
    )
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    return data.get("capacities", [])
 
 
def send_alert(available_days):
    lines = []
    for day in available_days:
        date = day["from"][:10]
        count = day["available"]
        lines.append("{}: {} lupaa".format(date, count))
    message = "Vapaita lupia:\n" + "\n".join(lines) + "\nOsta heti: " + PURCHASE_URL
    subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://ntfy.sh/" + NTFY_TOPIC,
            "-H", "Title: LUPIA SAATAVILLA 10-17.9 - Posio!",
            "-H", "Priority: urgent",
            "-H", "Tags: tada",
            "-d", message,
        ],
        check=True,
    )
 
 
def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print("[{}] Tarkistetaan saatavuus 10.-17.9.2026...".format(now))
 
    try:
        guest_id = get_guest_id()
    except Exception as e:
        print("VIRHE guest-id:n haussa: {}".format(e))
        sys.exit(1)
 
    if not guest_id:
        print("VIRHE: guest-id:ta ei saatu")
        sys.exit(1)
 
    print("Guest ID: {}...".format(guest_id[:8]))
 
    try:
        capacities = check_availability(guest_id)
    except Exception as e:
        print("VIRHE API-kutsussa: {}".format(e))
        sys.exit(1)
 
    if not capacities:
        print("VIRHE: Kalenteri-API ei palauttanut dataa")
        sys.exit(1)
 
    available_days = [d for d in capacities if (d.get("available") or 0) > 0]
 
    print("Paivakohtainen saatavuus:")
    for day in capacities:
        date = day["from"][:10]
        avail = day.get("available", 0)
        total = day.get("total", "?")
        marker = " *** VAPAANA ***" if avail > 0 else ""
        print("  {}: {}/{}{}".format(date, avail, total, marker))
 
    if available_days:
        print("\n*** LUPIA SAATAVILLA {} PAIVALLE - lahetetaan ilmoitus! ***".format(len(available_days)))
        try:
            send_alert(available_days)
            print("Push-ilmoitus lahetetty ntfy.sh-kanavalle.")
        except Exception as e:
            print("VIRHE ilmoituksen lahetyksessa: {}".format(e))
            sys.exit(1)
    else:
        print("Ei vapaita lupia 10.-17.9. talla hetkella.")
 
 
if __name__ == "__main__":
    main()
