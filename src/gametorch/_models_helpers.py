"""Pydantic validators that mirror the loose typing used by the GameTorch API.

Credit and USD amounts are usually encoded as decimal strings
(``"5.003952358800"``) but a few endpoints emit JSON numbers (``300``). These
helpers accept either representation and decode into :class:`decimal.Decimal`.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BeforeValidator

__all__ = [
    "BoolOrInt",
    "DecimalMap",
    "DecimalValue",
    "OptionalDecimal",
    "StringListLenient",
]


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(1 if value else 0)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip()
        try:
            return Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"invalid decimal string {value!r}") from exc
    raise ValueError(f"expected decimal, found {value!r}")


def _to_optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return _to_decimal(value)


def _to_decimal_map(value: Any) -> dict[str, Decimal]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"expected decimal map, found {value!r}")
    out: dict[str, Decimal] = {}
    for key, item in value.items():
        if item is None:
            continue
        out[str(key)] = _to_decimal(item)
    return out


def _to_bool_or_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    raise ValueError(f"expected boolean or integer, found {value!r}")


def _to_string_list_lenient(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (int, float, bool)):
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"expected string, found {item!r}")
            out.append(item)
        return out
    raise ValueError(f"expected string array, found {value!r}")


# Annotated types for use in model field declarations. They rely on pydantic's
# ``BeforeValidator`` so the raw JSON value is normalised before validation.
DecimalValue = Annotated[Decimal, BeforeValidator(_to_decimal)]
OptionalDecimal = Annotated[Decimal | None, BeforeValidator(_to_optional_decimal)]
DecimalMap = Annotated[dict[str, Decimal], BeforeValidator(_to_decimal_map)]
BoolOrInt = Annotated[int, BeforeValidator(_to_bool_or_int)]
StringListLenient = Annotated[list[str], BeforeValidator(_to_string_list_lenient)]
