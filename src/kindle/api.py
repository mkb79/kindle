# found api endpoints
# have to find out more


import json
from datetime import datetime

import httpx
import xmltodict


def get_library(auth):
    url = "https://todo-ta-g7g.amazon.com/FionaTodoListProxy/syncMetaData"
    params = {"item_count": 1000}
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        library = xmltodict.parse(r.text)
        library = json.loads(json.dumps(library))
        return library.get("response", library)


def _build_correlation_id(auth, asin):
    device = auth.device_info["device_type"]
    serial = auth.device_info["device_serial_number"]
    timestamp = datetime.utcnow().timestamp()
    timestamp = str(int(timestamp)*1000)
    return f"Device:{device}:{serial};kindle.EBOK:{asin}:{timestamp}"


def get_manifest(auth, asin: str):
    asin = asin.upper()
    url = f"https://kindle-digital-delivery.amazon.com/delivery/manifest/kindle.ebook/{asin}"
    headers = {
        "User-Agent": "Kindle/1.0.235280.0.10 CFNetwork/1220.1 Darwin/20.3.0",
        "X-ADP-AttemptCount": "1",
        "X-ADP-CorrelationId": _build_correlation_id(auth, asin),
        "X-ADP-Transport": "WiFi",
        "X-ADP-Reason": "ArchivedItems",
        "Accept-Language": auth.locale.language,
        "x-amzn-accept-type": "application/x.amzn.digital.deliverymanifest@1.0",
        "X-ADP-SW": "1184366692"
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, headers=headers)
        return r.json()


def whispersync(auth):
    user_id = auth.customer_info["user_id"]
    url = f"https://api.amazon.com/whispersync/v2/data/{user_id}/datasets"
    params1 = {
        "embed": "records.first_page",
        "quiet": "true"
    }
    # alternative params in other requests found
    params2 = {
        "filterDeletedUpto": 201,
        "embed": "records.first_page",
        "filterDeleted": "true",
        "after": 188
    }
    params3 = {
        "after": 201,
        "quiet": "true"
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params1)
        return r.json()


def whispersync_records_by_identifier(auth, identifier: str):
    user_id = auth.customer_info["user_id"]
    url = f"https://api.amazon.com/whispersync/v2/data/{user_id}/datasets/{identifier}/records"
    params = {
        "after": 201
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        return r.json()


def sidecar(auth, asin: str):
    url = f"https://sars.amazon.com/sidecar/sa/EBOK/{asin}"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def get_news(auth):
    url = "https://sars.amazon.com/kinapps/notifications/new"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def get_notification_channels(auth, marketplace: str):
    # marketplace e.g. A1PA6795UKMFR9
    url = f"https://d3ohh9b4v3oawh.cloudfront.net/iOS/1.1/{marketplace}/notificationsChannels.json"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def get_device_credentials(auth):
    # gives same credential types like a device registration
    # value are different, but why?
    # credentials from device registration are still valid
    # gives cookies for more amazon domains
    url = "https://firs-ta-g7g.amazon.com/FirsProxy/getDeviceCredentials"
    params = {
        "softwareVersion": "1184366692"
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        cred = xmltodict.parse(r.text)
        cred = json.loads(json.dumps(cred))
        return cred.get("response", cred)
