"""
IA Parc Inference decoders
"""
from typing import Any
from struct import unpack
from PIL.Image import Image
from io import BytesIO
import msgpack
import msgpack_numpy as m
import lz4.frame as lz4


Error = ValueError | None

## Data decoders


def decode(data: bytes, decoder: str) -> tuple[Any, Error]:
    """
    Decode data
    Arguments:
    data: bytes
    decoder: str
    """
    use_lz4 = False
    if "lz4(" in decoder:
        use_lz4 = True
        decoder = decoder.replace("lz4(", "").replace(")", "")
    if decoder == "float":
        return decode_float(data)
    if decoder == "int":
        return decode_float(data)
    if decoder == "bool":
        return decode_bool(data)
    if decoder == "file":
        return decode_file(data, use_lz4)
    elif decoder == "image":
        return decode_image(data, use_lz4)
    elif decoder == "text":
        return decode_text(data, use_lz4)
    elif decoder == "json":
        return decode_json(data, use_lz4)
    elif decoder == "msgpack":
        return decode_msgpack(data, use_lz4)
    elif decoder == "numpy":
        return decode_numpy(data, use_lz4)
    elif decoder == "multipart":
        return decode_multipart(data, [], "", use_lz4)

    
    return None, ValueError(f"Decoder {decoder} is not supported")

def decode_float(data: bytes) -> tuple[float, Error]:
    """
    Read float
    Arguments:
    data: bytes
    """
    if data is None:
        return 0.0, ValueError("No data to read")
    if not isinstance(data, bytes):
        return 0.0, ValueError("Data is not bytes")
    try:
        value = unpack('f', data)[0]
    except Exception as e:
        return 0.0, ValueError(f"Error reading float: {e}")
    return value, None

def decode_int(data: bytes) -> tuple[int, Error]:
    """
    Read int
    Arguments:
    data: bytes
    """
    if data is None:
        return 0, ValueError("No data to read")
    if not isinstance(data, bytes):
        return 0, ValueError("Data is not bytes")
    try:
        value = unpack('i', data)[0]
    except Exception as e:
        return 0, ValueError(f"Error reading int: {e}")
    return value, None

def decode_bool(data: bytes) -> tuple[bool, Error]:
    """
    Read bool
    Arguments:
    data: bytes
    """
    if data is None:
        return False, ValueError("No data to read")
    if not isinstance(data, bytes):
        return False, ValueError("Data is not bytes")
    try:
        value = unpack('?', data)[0]
    except Exception as e:
        return False, ValueError(f"Error reading bool: {e}")
    return value, None

def decode_file(data: bytes, use_lz4: bool=False) -> tuple[BytesIO, Error]:
    """
    Read file
    Arguments:
    data: bytes
    """
    if not data:
        return BytesIO(), ValueError("No data to read")
    if not isinstance(data, bytes):
        return BytesIO(), ValueError("Data is not bytes")
    try:
        if use_lz4:
            data = lz4.decompress(data)
        file = BytesIO(data)
    except Exception as e:
        return BytesIO(), ValueError(f"Error reading file: {e}")
    return file, None

def decode_image(data: bytes, use_lz4: bool=False) -> tuple[Image|None, Error]:
    """
    Read image
    Arguments:
    data: bytes
    """
    if not data:
        return None, ValueError("No data to read")
    if not isinstance(data, bytes):
        return None, ValueError("Data is not bytes")
    try:
        from PIL import Image
        if use_lz4:
            data = lz4.decompress(data)
        image = Image.open(BytesIO(data))
    except Exception as e:
        return None, ValueError(f"Error reading image: {e}")
    return image, None

def decode_text(data: bytes, use_lz4: bool=False) -> tuple[str, Error]:
    """
    Read text
    Arguments:
    data: bytes
    """
    if not data:
        return "", ValueError("No data to read")
    if not isinstance(data, bytes):
        return "", ValueError("Data is not bytes")
    try:
        if use_lz4:
            data = lz4.decompress(data)
        text = data.decode("utf-8")
    except Exception as e:
        return "", ValueError(f"Error reading text: {e}")
    return text, None

def decode_json(data: bytes, use_lz4: bool=False) -> tuple[dict, Error]:
    """
    Read json
    Arguments:
    data: bytes
    """
    if not data:
        return {}, ValueError("No data to read")
    if not isinstance(data, bytes):
        return {}, ValueError("Data is not bytes")
    try:
        from json_tricks import loads
        if use_lz4:
            data = lz4.decompress(data)
        json_data = loads(data.decode("utf-8"))
    except Exception as e:
        return {}, ValueError(f"Error reading json: {e}")
    return json_data, None

def decode_msgpack(data: bytes, use_lz4: bool=False) -> tuple[dict, Error]:
    """
    Read msgpack
    Arguments:
    data: bytes
    """
    if not data:
        return {}, ValueError("No data to read")
    if not isinstance(data, bytes):
        return {}, ValueError("Data is not bytes")
    try:
        if use_lz4:
            data = lz4.decompress(data)
        json_data = msgpack.unpackb(data, object_hook=m.decode)
    except Exception as e:
        return {}, ValueError(f"Error reading msgpack: {e}")
    return json_data, None

def decode_numpy(data: bytes, use_lz4: bool=False) -> tuple[dict, Error]:
    """
    Read numpy
    Arguments:
    data: bytes
    """
    return decode_msgpack(data, use_lz4)

def decode_multipart(data: bytes, items: list, content_type: str, use_lz4: bool=False) -> tuple[dict, Error]:
    """
    Read multi-part data
    Arguments:
    data: bytes
    """
    if not data:
        return {}, ValueError("No data to read")
    if not isinstance(data, bytes):
        return {}, ValueError("Data is not bytes")
    if not items:
        return {}, ValueError("No items to read")
    try:
        from streaming_form_data import StreamingFormDataParser
        from streaming_form_data.targets import BaseTarget
        if use_lz4:
            data = lz4.decompress(data)
        class BytesTarget(BaseTarget):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._data = None
                
            def on_data_received(self, data: bytes):
                self.data = data

        res = {}
        results = {}
        if "boundary" not in content_type:
            boundary = _get_boundary(data)
            if boundary:
                content_type += f'; boundary={boundary}'
        
        headers = {'Content-Type': content_type}
        #headers = {'Content-Type': 'multipart/form-data; boundary=boundary'}
        parser = StreamingFormDataParser(headers=headers)
        for item in items:
            res[item["name"]] = BytesTarget()
            parser.register(item["name"], res[item["name"]])
        parser.data_received(data)
        
        for item in items:
            results[item["name"]] = res[item["name"]].data

    except Exception as e:
        return {}, ValueError(f"Error reading multi-part data: {e}")
    return results, None

def decode_audio(data: bytes):
    """
    Read audio
    Arguments:
    data: bytes
    """
    pass


def _get_boundary(data: bytes) -> str | None:
    """
    Get boundary
    Arguments:
    data: bytes
    """
    splitted = data.split(b"\r\n")
    if len(splitted) < 2:
        return None
    boundary = splitted[0]
    if len(boundary) < 2:
        return None
    return boundary[2:].decode("utf-8")