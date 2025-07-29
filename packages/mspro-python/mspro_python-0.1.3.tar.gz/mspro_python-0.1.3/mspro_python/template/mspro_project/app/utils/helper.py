import hashlib
import json
import os
import random
import string
import time
import uuid
import secrets
from datetime import datetime

from pytz import timezone


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def json_success(message: str = 'Success', **kwargs):
    return json.dumps({'success': True, 'message': message, **kwargs}, cls=DateTimeEncoder, ensure_ascii=False)


def json_error(message: str = 'Failed', **kwargs):
    return json.dumps({'success': False, 'message': message, **kwargs}, cls=DateTimeEncoder, ensure_ascii=False)


def response_success(message: str = 'Success', **kwargs):
    return json.loads(json.dumps({'success': True, 'message': message, **kwargs}, cls=DateTimeEncoder, ensure_ascii=False))


def response_error(message: str = 'Failed', **kwargs):
    return json.loads(json.dumps({'success': False, 'message': message, **kwargs}, cls=DateTimeEncoder, ensure_ascii=False))


def get_random(size: int = 8) -> str:
    """生成随机数"""
    return ''.join(random.sample(string.ascii_letters + string.digits, size))


def get_time(date_format: str = '%Y-%m-%d %H:%M:%S', time_zone: str = None) -> str:
    """获取当前时间，默认澳洲时间"""
    time_zone = time_zone if time_zone else os.environ.get('TIME_ZONE')
    return datetime.now(timezone(time_zone)).strftime(date_format)


def get_timestamp(dt: str = None) -> float:
    """获取当前/指定时间戳"""
    return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").timestamp() if dt else time.time()


def to_time(ts: int, date_format: str = '%Y-%m-%d %H:%M:%S', time_zone: str = None) -> str:
    """时间戳转换成日期"""
    time_zone = time_zone if time_zone else os.environ.get('TIME_ZONE')
    return datetime.fromtimestamp(ts, timezone(time_zone)).strftime(date_format)


def get_md5(strs: str) -> str:
    md = hashlib.md5()
    md.update(strs.encode('utf-8'))
    return md.hexdigest()


def get_uuid():
    return str(uuid.uuid4())


def generate_api_key(length: int = 32) -> str:
    api_key = secrets.token_hex(length)
    return api_key


