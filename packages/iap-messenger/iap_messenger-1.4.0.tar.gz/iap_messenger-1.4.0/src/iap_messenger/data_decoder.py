"""
IA Parc Inference data handler
"""
import os
#import io
import logging
import logging.config
from typing import Any
import iap_messenger.decoders as decoders

Error = ValueError | None

LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=LEVEL,
    force=True,
    format="%(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("Inference")
LOGGER.propagate = True


def decode(raw: bytes, content_type: str="", conf: dict={}) -> tuple[Any, Error]:
    if content_type == "":
        content_type = conf.get("type", "json")
    if content_type == "multimodal":
        raw_items, error = decoders.decode_multipart(
            raw, conf["items"], content_type)
        result = {}
        for item in conf["items"]:
            item_data = raw_items.get(item["name"])
            if item_data:
                result[item["name"]], error = decoders.decode(
                    item_data, item["type"])
                if error:
                    LOGGER.error(f"Error decoding {item['name']}: {error}")
                    return None, error
        return result, None
    else:
        return decoders.decode(raw, content_type)
