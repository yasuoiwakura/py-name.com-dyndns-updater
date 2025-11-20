# main.py
import pandas as pd
import requests
import time
import json
from requests.auth import HTTPBasicAuth


def main():
    # example call - use run_local.py (will read secrets.yml) or run_remote.py for docker deployment (reads ENV)
    example_updater = NameComDNSUpdater(
        domain="example.com",
        record_name="", # your subdomain, empty string for 
        ttl=300, # apex domains CANNOT have values below 300, so in THEORY the DNS clients MIGHT try the OLD IP, resulting in a 5minute downtime
        current_ip_file="current_ip.txt",
        check_interval=60,
        api_username="your_namecom_username",
        api_key="your_namecom_api_key"
    )

    print("Starte Beispiel-Loop (nur für lokale Tests)...")
    example_updater.loop()


class NameComDNSUpdater:
    def __init__(self, domain, record_name, ttl, current_ip_file, check_interval, api_username, api_key):
        self.domain = domain
        self.record_name = record_name
        self.ttl = ttl
        self.current_ip_file = current_ip_file
        self.check_interval = check_interval
        self.api_username = api_username
        self.api_key = api_key

    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org?format=json')
            return response.json()['ip']
        except requests.RequestException as e:
            print(f"Fehler beim Abrufen der IP-Adresse: {e}", flush=True)
            return None

    def get_current_ip(self):
        try:
            with open(self.current_ip_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def set_current_ip(self, ip):
        with open(self.current_ip_file, 'w') as f:
            f.write(ip)

    def get_dns_record(self, fqdn=None, record_type="A"):
        if fqdn is None:
            fqdn = self.domain + "."

        api_url = f"https://api.name.com/core/v1/domains/{self.domain}/records"
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.get(api_url, headers=headers,
                                    auth=HTTPBasicAuth(self.api_username, self.api_key))
            df = pd.DataFrame(response.json().get('records', []))
            filtered_df = df[(df['fqdn'] == fqdn) & (df['type'] == record_type)]
            if filtered_df.empty:
                return None
            return filtered_df.iloc[0].to_dict()
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen des DNS-Eintrags: {e}")

    def update_dns_record(self, ip):
        old_dns_entry = self.get_dns_record()
        if old_dns_entry is None:
            print("DNS-Eintrag nicht gefunden. Bitte erst anlegen.", flush=True)
            return

        api_url = f"https://api.name.com/core/v1/domains/{self.domain}/records/{old_dns_entry['id']}"
        data = {
            "answer": ip,
            "fqdn": old_dns_entry['fqdn'],
            "host": old_dns_entry['host'],
            "priority": 0,
            "ttl": self.ttl,
            "type": "A"
        }
        response = requests.put(api_url, headers={'Content-Type': 'application/json'},
                                data=json.dumps(data),
                                auth=HTTPBasicAuth(self.api_username, self.api_key))
        print(response.text, flush=True)
        if response.status_code == 200:
            print(f"DNS-Eintrag erfolgreich aktualisiert: {self.record_name}.{self.domain} -> {ip}", flush=True)

    def loop(self):
        while True:
            public_ip = self.get_public_ip()
            if public_ip:
                current_ip = self.get_current_ip()
                if public_ip != current_ip:
                    print(f"IP changed: {current_ip} -> {public_ip}", flush=True)
                    self.update_dns_record(public_ip)
                    self.set_current_ip(public_ip)
            else:
                print("Konnte die öffentliche IP-Adresse nicht ermitteln.", flush=True)
            time.sleep(self.check_interval)


if __name__ == "__main__":
    main()
