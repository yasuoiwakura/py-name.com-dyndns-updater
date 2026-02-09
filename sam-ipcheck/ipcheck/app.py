import json
import logging

# Logger für detaillierte Debug-Ausgaben
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    """Lambda Funktion zum Abrufen der echten IP-Adresse der Anfrage mit Debug-Infos"""

    # Die IP-Adresse wird bevorzugt aus den Headern extrahiert
    ip_address = None

    logger.debug("Event: %s", json.dumps(event))  # Logge das gesamte Event für Debugging

    # Überprüfen, ob der X-Forwarded-For Header vorhanden ist
    if 'headers' in event:
        x_forwarded_for = event['headers'].get('X-Forwarded-For')
        if x_forwarded_for:
            # Die erste IP-Adresse im X-Forwarded-For Header ist die ursprüngliche IP-Adresse des Clients
            ip_address = x_forwarded_for.split(',')[0].strip()
            logger.debug("X-Forwarded-For Header gefunden: %s", ip_address)
    
    # Wenn die IP-Adresse nicht im X-Forwarded-For Header gefunden wurde, prüfe X-Real-IP
    if not ip_address and 'headers' in event:
        x_real_ip = event['headers'].get('X-Real-IP')
        if x_real_ip:
            ip_address = x_real_ip.strip()
            logger.debug("X-Real-IP Header gefunden: %s", ip_address)

    # Wenn die IP-Adresse immer noch nicht gefunden wurde, nehme sie aus dem sourceIp im Event
    if not ip_address:
        ip_address = event['requestContext']['identity'].get('sourceIp')
        logger.debug("sourceIp aus requestContext: %s", ip_address)

    if not ip_address:
        logger.debug("Keine IP-Adresse gefunden, alle Prüfungen erfolglos!")

    # Rückgabe der IP-Adresse im JSON-Format (Format, wie es viele IP-Checker verwenden)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "ip": ip_address,
            "message": "Ihre IP-Adresse",
            "event": event,  # Event zur Ansicht im Response für Debugging
        }),
    }
