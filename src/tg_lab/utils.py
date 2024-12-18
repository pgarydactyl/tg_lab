import datetime


def get_event_id(name=""):
    unix_timestamp = datetime.datetime.now().timestamp() * 1000
    return f"{int(unix_timestamp)}-{name}"
