import json

def lambda_handler(event, context):
    """Lambda Funktion zum Abrufen der echten IP-Adresse der Anfrage"""

    # Die IP-Adresse wird bevorzugt aus den Headern extrahiert
    ip_address = None

    # Überprüfen, ob der X-Forwarded-For Header vorhanden ist
    if 'headers' in event:
        x_forwarded_for = event['headers'].get('X-Forwarded-For')
        if x_forwarded_for:
            # Die erste IP-Adresse im X-Forwarded-For Header ist die ursprüngliche IP-Adresse des Clients
            ip_address = x_forwarded_for.split(',')[0].strip()
    
    # Wenn die IP-Adresse nicht im X-Forwarded-For Header gefunden wurde, prüfe X-Real-IP
    if not ip_address and 'headers' in event:
        x_real_ip = event['headers'].get('X-Real-IP')
        if x_real_ip:
            ip_address = x_real_ip.strip()

    # Wenn die IP-Adresse immer noch nicht gefunden wurde, nehme sie aus dem sourceIp im Event
    if not ip_address:
        ip_address = event['requestContext']['identity'].get('sourceIp')

    # Rückgabe der IP-Adresse im JSON-Format (Format, wie es viele IP-Checker verwenden)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "ip": ip_address,
            "message": "Ihre IP-Adresse"
        }),
    }
