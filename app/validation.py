"""Kiểm tra và chuẩn hoá dữ liệu đầu vào. Mọi thông báo lỗi đều bằng tiếng Việt."""
from __future__ import annotations

import math
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import request

from app import clock
from app.errors import ValidationFailed

MISSING = object()

_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_VN = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_DATETIME_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?(Z|[+-]\d{2}:?\d{2})?$")
_DATETIME_VN = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$")


class FieldError(Exception):
    """Lỗi của một trường dữ liệu."""


def field_error(field: str, label: str, message: str) -> dict:
    return {"field": field, "label": label, "message": message}


def invalid(field: str, label: str, message: str) -> ValidationFailed:
    """Tạo lỗi 422 cho một trường (dùng: raise invalid(...))."""
    return ValidationFailed([field_error(field, label, message)])


def _fmt(number) -> str:
    if isinstance(number, (int, Decimal)) and abs(number) >= 10000:
        return f"{int(number):,}".replace(",", ".")
    return str(number)


class Field:
    def __init__(self, label: str, *, required: bool = False, nullable: bool = True, default=MISSING):
        self.label = label
        self.required = required
        self.nullable = nullable and not required
        self.default = default

    def clean(self, value):
        if isinstance(value, str) and value.strip() == "" and not isinstance(self, Str):
            value = None
        if value is None:
            if not self.nullable:
                raise FieldError(f"{self.label} không được để trống.")
            return None
        return self.convert(value)

    def convert(self, value):
        return value

    def default_value(self):
        if self.default is MISSING:
            return None
        return self.default() if callable(self.default) else self.default


class Str(Field):
    def __init__(self, label: str, *, min_len: int = 0, max_len: int = 255, strip: bool = True, **kwargs):
        super().__init__(label, **kwargs)
        self.min_len = min_len
        self.max_len = max_len
        self.strip = strip

    def convert(self, value):
        if not isinstance(value, str):
            raise FieldError(f"{self.label} phải là chuỗi ký tự.")
        if self.strip:
            value = value.strip()
        if not value:
            if self.min_len > 0 or not self.nullable:
                raise FieldError(f"{self.label} không được để trống.")
            return None
        if len(value) < self.min_len:
            raise FieldError(f"{self.label} phải có ít nhất {self.min_len} ký tự.")
        if len(value) > self.max_len:
            raise FieldError(f"{self.label} không được vượt quá {self.max_len} ký tự.")
        return value


class Int(Field):
    def __init__(self, label: str, *, min_value: int | None = None, max_value: int | None = None, **kwargs):
        super().__init__(label, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def convert(self, value):
        if isinstance(value, bool):
            raise FieldError(f"{self.label} phải là số nguyên.")
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        elif isinstance(value, str) and re.fullmatch(r"\s*-?\d+\s*", value):
            value = int(value)
        if not isinstance(value, int):
            raise FieldError(f"{self.label} phải là số nguyên.")
        if self.min_value is not None and value < self.min_value:
            raise FieldError(f"{self.label} phải lớn hơn hoặc bằng {_fmt(self.min_value)}.")
        if self.max_value is not None and value > self.max_value:
            raise FieldError(f"{self.label} không được lớn hơn {_fmt(self.max_value)}.")
        return value


class Number(Field):
    """Số thập phân (trả về Decimal)."""

    def __init__(self, label: str, *, min_value=None, max_value=None, gt=None, max_decimals: int = 2, **kwargs):
        super().__init__(label, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.gt = gt
        self.max_decimals = max_decimals

    def convert(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
            raise FieldError(f"{self.label} phải là số.")
        if isinstance(value, float) and not math.isfinite(value):
            raise FieldError(f"{self.label} phải là số.")
        try:
            number = Decimal(str(value).strip())
        except InvalidOperation:
            raise FieldError(f"{self.label} phải là số.") from None
        if not number.is_finite():
            raise FieldError(f"{self.label} phải là số.")
        if self.gt is not None and number <= self.gt:
            raise FieldError(f"{self.label} phải lớn hơn {_fmt(self.gt)}.")
        if self.min_value is not None and number < self.min_value:
            raise FieldError(f"{self.label} phải lớn hơn hoặc bằng {_fmt(self.min_value)}.")
        if self.max_value is not None and number > self.max_value:
            raise FieldError(f"{self.label} không được lớn hơn {_fmt(self.max_value)}.")
        exponent = number.normalize().as_tuple().exponent
        if isinstance(exponent, int) and -exponent > self.max_decimals:
            raise FieldError(f"{self.label} chỉ được có tối đa {self.max_decimals} chữ số thập phân.")
        return number


class Bool(Field):
    _TRUE = {"true", "1", "yes", "co", "có"}
    _FALSE = {"false", "0", "no", "khong", "không"}

    def convert(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            text = value.strip().lower()
            if text in self._TRUE:
                return True
            if text in self._FALSE:
                return False
        raise FieldError(f"{self.label} phải là true hoặc false.")


class DateField(Field):
    """Ngày: chấp nhận YYYY-MM-DD hoặc DD/MM/YYYY."""

    def convert(self, value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            text = value.strip()
            try:
                if _DATE_ISO.match(text):
                    return date.fromisoformat(text)
                match = _DATE_VN.match(text)
                if match:
                    day, month, year = (int(x) for x in match.groups())
                    return date(year, month, day)
            except ValueError:
                pass
        raise FieldError(f"{self.label} không đúng định dạng ngày (YYYY-MM-DD hoặc DD/MM/YYYY).")


class DateTimeField(Field):
    """Thời điểm: chấp nhận ISO 8601 (có thể kèm múi giờ) hoặc DD/MM/YYYY HH:MM. Quy về giờ Việt Nam."""

    def convert(self, value):
        if isinstance(value, datetime):
            return clock.to_vn_naive(value)
        if isinstance(value, str):
            text = value.strip()
            try:
                match = _DATETIME_VN.match(text)
                if match:
                    day, month, year, hour, minute, second = match.groups()
                    return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second or 0))
                if _DATETIME_ISO.match(text):
                    normalized = text.replace(" ", "T", 1)
                    if normalized.endswith("Z"):
                        normalized = normalized[:-1] + "+00:00"
                    normalized = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", normalized)
                    return clock.to_vn_naive(datetime.fromisoformat(normalized))
            except ValueError:
                pass
        raise FieldError(
            f"{self.label} không đúng định dạng thời gian (YYYY-MM-DDTHH:MM hoặc DD/MM/YYYY HH:MM).")


class Choice(Field):
    def __init__(self, label: str, choices: dict, **kwargs):
        super().__init__(label, **kwargs)
        self.choices = choices

    def convert(self, value):
        if isinstance(value, str) and value.strip() in self.choices:
            return value.strip()
        allowed = ", ".join(f"{key} ({text})" for key, text in self.choices.items())
        raise FieldError(f"{self.label} không hợp lệ. Giá trị cho phép: {allowed}.")


class Obj(Field):
    def convert(self, value):
        if not isinstance(value, dict):
            raise FieldError(f"{self.label} phải là một đối tượng JSON.")
        return value


def validate(data, schema: dict, *, partial: bool = False, forbidden: dict | None = None) -> dict:
    """Kiểm tra dữ liệu theo schema.

    partial=True (dùng cho PATCH): chỉ kiểm tra các trường có gửi lên.
    forbidden: {tên trường: thông báo} cho các trường không được phép gửi.
    """
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValidationFailed([], message="Dữ liệu gửi lên phải là một đối tượng JSON.")
    errors, cleaned = [], {}
    for name, spec in schema.items():
        if name in data:
            try:
                cleaned[name] = spec.clean(data[name])
            except FieldError as exc:
                errors.append(field_error(name, spec.label, str(exc)))
        elif partial:
            continue
        elif spec.required:
            errors.append(field_error(name, spec.label, f"{spec.label} là bắt buộc."))
        else:
            cleaned[name] = spec.default_value()
    for name, message in (forbidden or {}).items():
        if name in data:
            errors.append(field_error(name, name, message))
    if errors:
        raise ValidationFailed(errors)
    return cleaned


def json_body() -> dict:
    """Đọc body JSON của request (body rỗng coi như {})."""
    raw = request.get_data(cache=True)
    if not raw or not raw.strip():
        return {}
    data = request.get_json(force=True, silent=True)
    if data is None:
        raise ValidationFailed([], message="Dữ liệu gửi lên không phải JSON hợp lệ.")
    if not isinstance(data, dict):
        raise ValidationFailed([], message="Dữ liệu gửi lên phải là một đối tượng JSON (dạng {...}).")
    return data


def query_args() -> dict:
    return request.args.to_dict(flat=True)


PAGINATION = {
    "page": Int("Trang", min_value=1, max_value=100000, default=1),
    "page_size": Int("Số dòng mỗi trang", min_value=1, max_value=100, default=20),
}


def page_window(params: dict) -> tuple[int, int]:
    """Trả về (limit, offset) từ tham số phân trang đã kiểm tra."""
    size = params.get("page_size") or 20
    page = params.get("page") or 1
    return size, (page - 1) * size


def page_result(items: list, total: int, params: dict) -> dict:
    size = params.get("page_size") or 20
    return {
        "items": items,
        "total": total,
        "page": params.get("page") or 1,
        "page_size": size,
        "total_pages": max(1, math.ceil(total / size)) if total else 1,
    }
