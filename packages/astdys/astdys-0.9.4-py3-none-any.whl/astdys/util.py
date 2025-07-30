import datetime


def convert_mjd_to_date(mjd: float) -> str:

    base_date = datetime.datetime(1858, 11, 17)
    delta = datetime.timedelta(days=mjd)
    date = base_date + delta
    formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_date


def convert_mjd_to_datetime(mjd: float) -> datetime.datetime:
    s = convert_mjd_to_date(mjd)
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
