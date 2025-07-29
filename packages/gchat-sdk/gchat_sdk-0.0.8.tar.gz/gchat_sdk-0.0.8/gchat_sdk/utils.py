import pytz
from datetime import datetime, timedelta


def get_limit_date(hours: int) -> datetime:
    return datetime.now(pytz.timezone("America/Sao_Paulo")) - timedelta(hours=hours) 

def get_limit_date_minutes(minutes: int) -> datetime:
    return datetime.now(pytz.timezone("America/Sao_Paulo")) - timedelta(minutes=minutes) 

def get_limit_date_rule(unit: str):

    if unit == 'hours':
        return get_limit_date
    
    return get_limit_date_minutes