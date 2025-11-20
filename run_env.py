# run_env.py
import os
from main import NameComDNSUpdater

# Docker / CI erwartet Systemvariablen
updater = NameComDNSUpdater(
    domain=os.environ["DYNDNS_DOMAIN"],
    record_name=os.environ.get("RECORD_NAME", ""),
    ttl=int(os.environ.get("TTL", 300)),
    current_ip_file=os.environ.get("CURRENT_IP_FILE", "current_ip.txt"),
    check_interval=int(os.environ.get("CHECK_INTERVAL", 60)),
    api_username=os.environ["API_USERNAME"],
    api_key=os.environ["API_KEY"]
)

updater.loop()
