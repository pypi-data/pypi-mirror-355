from datetime import datetime

def get_timestamp_now_as_string(include_ms:bool = True):
    if include_ms:
        return datetime.now().strftime("%Y%m%d_%H%M%S%f")
    else:
        return datetime.now().strftime("%Y%m%d_%H%M%S")