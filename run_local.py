# run_local.py
import os
import yaml
from main import NameComDNSUpdater

FILE_PATH_SECRETS = './secrets.yml' # 'c:/secrets/secrets-name-com.yml'

# Default Secrets-File
SECRETS_FILE = os.environ.get('SECRETS_FILE', FILE_PATH_SECRETS)
if os.path.exists(SECRETS_FILE):
    with open(SECRETS_FILE, 'r') as f:
        secrets = yaml.safe_load(f)
else:
    # secrets = {}
    raise RuntimeError(f"run_local.py failed to read secrets.yml from {FILE_PATH_SECRETS}")

updater = NameComDNSUpdater(
    domain='domain.tld',
    record_name='',
    ttl=300,
    current_ip_file='current_ip.txt',
    check_interval=60, #seconds

    api_username=secrets['API_USERNAME'],
    api_key=secrets['API_KEY']
)

updater.loop()
