import pytz
from datetime import datetime, timedelta
from tzlocal import get_localzone_name

utc = pytz.utc
local = pytz.timezone(get_localzone_name())

def datetime_errorCheck(d: datetime, tz: pytz) -> None:
    if type(d) is not datetime:
        raise Exception('Testing a non-datetime object!')
    elif d.tzinfo is None and d.tzinfo.utcoffset(d) is None:
        raise Exception('Datetime is not Timezone Aware!')
    elif str(d.tzinfo) != str(tz):
        raise Exception(f"Datetime Timezone ({d.tzinfo}) is not {tz}")
    return None

def DATETIME(yyyy: int, mm: int, dd: int, h=0, m=0, s=0, ms=0, tz=pytz.utc) -> datetime: 
    naive_datetime = datetime(yyyy, mm, dd, hour=h, minute=m, second=s, microsecond=ms)
    aware_datetime = tz.localize(naive_datetime)
    return aware_datetime

def DATETIME_NOW(tz=pytz.utc) -> datetime:
    aware_datetime = datetime.now(tz)
    return aware_datetime

def UNIXTIMESTAMP(dt: datetime, milliseconds=False) -> int:
    new_aware_datetime = dt.astimezone(pytz.utc)
    seconds = new_aware_datetime.timestamp()
    if milliseconds is True:
        return int(seconds * 1000)
    else:
        return int(seconds)

def DATETIMEfromUNIXTIMESTAMP(t: float, tz=pytz.utc, milliseconds=False, display=False) -> datetime:
    seconds = t / 1000 if milliseconds is True else t
    aware_datetime = datetime.fromtimestamp(seconds, tz)
    if display is True:
        return aware_datetime.strftime("%b %d, %Y %I:%M %p")  
    else:
        return aware_datetime

def displayTIMEDELTA(td: timedelta) -> str:
    days = td.days
    seconds = td.seconds
    hours = seconds//3600
    minutes = (seconds//60)%60

    ret = f"{days}d {hours}h {minutes}m"
    return ret


