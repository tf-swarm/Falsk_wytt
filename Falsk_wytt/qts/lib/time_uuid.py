import datetime
import uuid


def create_time_uuid():
    return '{0:%Y%m%d%H%M%S}'.format(datetime.datetime.now()) + str(uuid.uuid4()).upper()[:10]


def create_notice_uuid():
    return '{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())[:-3] + str(uuid.uuid4()).upper()