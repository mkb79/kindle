# found api endpoints
# there are many more but what they do?

import base64
import json
import pathlib
import re
from datetime import datetime
from typing import Dict, Optional, Union

import httpx
import xmltodict
from amazon.ion import simpleion

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import kindle


def get_library(auth: "kindle.Authenticator",
                last_sync: Optional[Union[str, Dict]] = None) -> Dict:
    """Fetches the user library.

    Args:
        auth: The Kindle Authenticator
        last_sync: If not `None`, the library will be updated instead of a 
            full sync. The `last_sync` value have to be taken from last sync 
            response `sync_time` key as string or provide the full sync
            response and the function will extract the value.

    Returns:
        The user library.

    """
    url = "https://todo-ta-g7g.amazon.com/FionaTodoListProxy/syncMetaData"
    params = {"item_count": 1000}

    if isinstance(last_sync, dict):
        if "sync_time" in last_sync:
            last_sync = last_sync["sync_time"]
        else:
            raise ValueError("`last_sync` doesn't contain a `sync_time`.")

    if last_sync is not None:
        params["last_sync_time"] = last_sync

    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        r.raise_for_status()
        library = xmltodict.parse(r.text)
        library = json.loads(json.dumps(library))
        return library.get("response", library)


def _build_correlation_id(auth: "kindle.Authenticator",
                          asin: str,
                          timestamp: Optional[str] = None) -> str:
    device = auth.device_info["device_type"]
    serial = auth.device_info["device_serial_number"]
    if timestamp is None:
        timestamp = datetime.utcnow().timestamp()
        timestamp = str(int(timestamp)*1000)
    return f"Device:{device}:{serial};kindle.EBOK:{asin}:{timestamp}"


def _b64ion_to_dict(b64ion: str) -> Dict:
    ion = base64.b64decode(b64ion)
    ion = simpleion.loads(ion)
    return dict(ion)


def get_manifest_ebook(auth: "kindle.Authenticator", asin: str) -> Dict:
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
        manifest = r.json()

    manifest["responseContext"] = _b64ion_to_dict(manifest["responseContext"])
    for resource in manifest["resources"]:
        if "responseContext" in resource:
            resource["responseContext"] = _b64ion_to_dict(resource["responseContext"])
    return manifest


def download_ebook(auth: "kindle.Authenticator", manifest: Dict, make_zip=True):
    """proof-of-concent, quick and dirty, donwload content and saving them in current working dir."""
    session = httpx.Client(auth=auth)
    for resource in manifest["resources"]:
        delivery = resource.get("deliveryType")
        requirement = resource.get("requirement")
        type = resource.get("type")
        size = resource.get("size")
        endpoint = resource.get("optimalEndpoint", resource["endpoint"])
        
        print(f"DELIVERY:    {delivery}")
        print(f"ENDPOINT:    {endpoint}")
        print(f"REQUIREMENT: {requirement}")
        print(f"TYPE:        {type}")
        print(f"SIZE:        {size}")
    
        url = None
        if "directUrl" in endpoint:
            url = endpoint["directUrl"]
        elif "url" in endpoint:
            url = endpoint["url"]
        else:
            print("Error in url")
    
        if url:
            if type == "DRM_VOUCHER":
                timestamp = manifest["responseContext"]["manifestTime"]
                asin = manifest["content"]["id"]
                correlation_id = _build_correlation_id(auth, asin, timestamp)
                headers = {
                    "User-Agent": "Kindle/1.0.235280.0.10 CFNetwork/1220.1 Darwin/20.3.0",
                    "X-ADP-AttemptCount": "1",
                    "X-ADP-CorrelationId": correlation_id,
                    "X-ADP-Transport": manifest["responseContext"]["transport"],
                    "X-ADP-Reason": manifest["responseContext"]["reason"],
                    "Accept-Language": auth.locale.language,
                    "x-amzn-accept-type": "application/x.amzn.digital.deliverymanifest@1.0",
                    "X-ADP-SW": manifest["responseContext"]["swVersion"],
                    "X-ADP-LTO": "60",
                    "Accept": "application/x-com.amazon.drm.Voucher@1.0"
                }
                if "country" in manifest["responseContext"]:
                    headers["X-ADP-Country"] = manifest["responseContext"]["country"]
                print("Found DRM Voucher")
                url += "&supportedVoucherVersions=V1%2CV2%2CV3%2CV4%2CV5%2CV6%2CV7%2CV8%2CV9%2CV10%2CV11%2CV12%2CV13%2CV14%2CV15%2CV16%2CV17%2CV18%2CV19%2CV20%2CV21%2CV22%2CV23%2CV24%2CV25%2CV26%2CV27%2CV28%2CV9708%2CV1031%2CV2069%2CV9041%2CV3646%2CV6052%2CV9479%2CV9888%2CV4648%2CV5683"
                r = session.get(url, headers=headers)
            else:
                r = session.get(url)
            try:
                r.raise_for_status()
                if r.headers.get("content-disposition"):
                    cd = r.headers.get("content-disposition")
                    fn = re.findall('filename="?(.+)"?', cd)
                    fn = fn[0]
                else:
                    fn = resource["id"]
                fn = pathlib.Path(fn)
                fn.write_bytes(r.content)
            except:
                print("ERROR")
                print(r.status_code)
                print(r.content)
        print()
        print()


def download_pdoc(auth: "kindle.Authenticator", asin: str) -> None:
    "Downloading personal added documents"
    url = "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/FSDownloadContent"
    params = {
        "type": "PDOC",
        "key": asin,
        "is_archived_items": 1,
        "software_rev": 1184370688
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        pathlib.Path(asin).write_bytes(r.content)


def whispersync(auth: "kindle.Authenticator") -> Dict:
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


def whispersync_records_by_identifier(auth: "kindle.Authenticator",
                                      identifier: str) -> Dict:
    user_id = auth.customer_info["user_id"]
    url = f"https://api.amazon.com/whispersync/v2/data/{user_id}/datasets/{identifier}/records"
    params = {
        "after": 201
    }
    with httpx.Client(auth=auth) as session:
        r = session.get(url, params=params)
        return r.json()


def sidecar_ebook(auth: "kindle.Authenticator", asin: str) -> Dict:
    url = f"https://sars.amazon.com/sidecar/sa/EBOK/{asin}"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def sidecar_pdoc(auth: "kindle.Authenticator", asin: str) -> Dict:
    url = f"https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/sidecar"
    params = {
        "type": "PDOC",
        "key": asin
    }
    with httpx.Client(auth=auth, params=params) as session:
        r = session.get(url)
        return r.json()


def get_news(auth: "kindle.Authenticator") -> Dict:
    url = "https://sars.amazon.com/kinapps/notifications/new"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def get_notification_channels(auth: "kindle.Authenticator", marketplace: str) -> Dict:
    # marketplace e.g. A1PA6795UKMFR9
    url = f"https://d3ohh9b4v3oawh.cloudfront.net/iOS/1.1/{marketplace}/notificationsChannels.json"
    with httpx.Client(auth=auth) as session:
        r = session.get(url)
        return r.json()


def get_device_credentials(auth: "kindle.Authenticator") -> Dict:
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
