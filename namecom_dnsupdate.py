# pip install pyyaml pandas
import os # for ENV
import pandas as pd
import requests
import time
import json
import yaml
import logging
from requests.auth import HTTPBasicAuth

print("Starting App...", flush=True)
DYNDNS_DOMAIN       = os.environ.get('DYNDNS_DOMAIN',       'domain.tld')
RECORD_NAME         = os.environ.get('RECORD_NAME',         '')

TTL                 = int(os.environ.get('TTL',             300)) # 300 is minimum
CHECK_INTERVAL      = int(os.environ.get('CHECK_INTERVAL',  60))

CURRENT_IP_FILE     = os.environ.get('CURRENT_IP_FILE',  'current_ip.txt')

# Konfiguration
if os.environ.get("API_USERNAME") and os.environ.get("API_USERNAME"):
    API_USERNAME    = os.environ.get('API_USERNAME')
    API_KEY         = os.environ.get('API_KEY')
    print("Got secrets from Docker Environment Variables", flush=True)
else:
    SECRETS_FILE = os.environ.get('SECRETS_FILE', './secrets.yml') # docker -e SECRETS_FILE=/secrets.json
    # {
    #   "API_USERNAME": "your name.com username",
    #   "API_KEY": "your name.com api-key"
    # }
    with open(SECRETS_FILE, 'r') as f: SECRETS = yaml.safe_load(f)
    API_USERNAME    = SECRETS['API_USERNAME']
    API_KEY         = SECRETS['API_KEY']
    print(f"Got secrets from {SECRETS_FILE}", flush=True)
    


# Name.com API-URL
API_URL_LIST = f"https://api.name.com/core/v1/domains/{DYNDNS_DOMAIN}/records?perPage=0&page=0"


REMOTE_DEBUG       = os.environ.get('REMOTE_DEBUG',       False)
if REMOTE_DEBUG:
    try:
        import debugpy
    except Exception as e:
        print("debugpy not found - rebuild environment:\ndocker compose build --build-arg INSTALL_DEBUG=true", flush=True)
        raise e
        sys.exit(1)  # Beende das Skript mit einem Fehlercode (1), damit Docker den Container nicht neu startet

    # Debugger auf Port 5678 aktivieren (du kannst auch einen anderen Port wählen)
    debugpy.listen(('0.0.0.0', 5678))  
    print("REMOTE_DEBUG=True; Warte auf Debugger-Verbindung...", flush=True)
    debugpy.wait_for_client()  # Dies hält den Code an, bis der Debugger verbunden ist
    debugpy.breakpoint()  # Setzt einen Breakpoint direkt hier, wenn gewünscht


def get_public_ip():
    try:
       # Hole die öffentliche IP-Adresse
       response = requests.get('https://api.ipify.org?format=json')
       return response.json()['ip']
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der IP-Adresse: {e}", flush=True)
        return None


def get_current_ip():
    try:
        with open(CURRENT_IP_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def set_current_ip(ip):
    with open(CURRENT_IP_FILE, 'w') as f:
        f.write(ip)


def get_dns_record(domain=DYNDNS_DOMAIN, fqdn=None, record_type="A"):
    if fqdn is None:
        fqdn = domain + "."

    # API URL und Header
    API_URL_LIST = f"https://api.name.com/core/v1/domains/{domain}/records"
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # GET-Anfrage senden
        response = requests.get(API_URL_LIST, headers=headers, auth=HTTPBasicAuth(API_USERNAME, API_KEY))

        # Überprüfen, ob die Antwort JSON ist
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            raise Exception(f"Antwort hat den falschen Content-Type: {content_type}, erwartet 'application/json'.")

        # Antwort als JSON dekodieren
        response_json = response.json()

        # Umwandlung der Records in einen Pandas DataFrame
        df = pd.DataFrame(response_json.get('records', []))

        # Filtern des DataFrames nach den Kriterien fqdn und record_type
        filtered_df = df[(df['fqdn'] == fqdn) & (df['type'] == record_type)]
        
        print(filtered_df, flush=True)

        if filtered_df.empty:
            return None
        else:
            # Rückgabe des ersten passenden Datensatzes als JSON
            return filtered_df.iloc[0].to_dict()

    except requests.RequestException as e:
        # Fehler bei der Anfrage
        raise Exception(f"Fehler bei der DNS-Anfrage: {e}")
    except Exception as e:
        # Fehler beim Verarbeiten der Antwort oder bei der Datenstruktur
        raise Exception(f"You need to create the DNS entry first, so the script can retrieve the DNS entry ID: {e}")


def update_dns_record(ip):
    headers = {
        # 'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    # response = requests.get(API_URL_LIST, headers=headers, auth=HTTPBasicAuth(API_USERNAME, API_KEY))
    # content_type=response.headers._store['content-type'][1]
    # if not response.headers._store['content-type'][1] == 'application/json':
    #     raise Exception("no json response - cannot idnetify ID")
    # response_json = json.loads(response.text)

    old_dns_entry = get_dns_record(domain=DYNDNS_DOMAIN)

    api_url = f"https://api.name.com/core/v1/domains/{DYNDNS_DOMAIN}/records/{old_dns_entry['id']}"

    data = {
        "answer": ip,
        "fqdn": old_dns_entry['fqdn'],  # FQDN muss mit einem Punkt enden!
        "host": old_dns_entry['host'],
        "priority": 0,
        "ttl": TTL,
        "type": "A"
    }

    try:
        response = requests.put(api_url, headers=headers, data=json.dumps(data), auth=HTTPBasicAuth(API_USERNAME, API_KEY))
        df = pd.DataFrame([json.loads(response.text)])
        print(df, flush=True)

        if response.status_code == 200:
            print(f"DNS-Eintrag erfolgreich aktualisiert: {RECORD_NAME}.{DYNDNS_DOMAIN} -> {ip}", flush=True)
        else:
            print(f"Fehler beim Aktualisieren des DNS-Eintrags: {response.text}", flush=True)
    except requests.RequestException as e:
        print(f"Fehler bei der DNS-Aktualisierung: {e}", flush=True)


def main():
    public_ip = get_public_ip()
    update_dns_record(public_ip)
    print(f"Going into loop every {str(CHECK_INTERVAL)}s...", flush=True)
    while True:
        public_ip = get_public_ip()
        if public_ip:
            current_ip = get_current_ip()
            if public_ip != current_ip:
                print(f"IP changed: {current_ip} -> {public_ip}", flush=True)
                update_dns_record(public_ip)
                set_current_ip(public_ip)
        else:
            print("Konnte die öffentliche IP-Adresse nicht ermitteln.", flush=True)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

