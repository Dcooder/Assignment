"""Unit conversion at form/display boundaries; domain and packing values stay in cm/kg."""

from decimal import Decimal

CENTIMETRES_PER_INCH = Decimal("2.54")
DIMENSION_UNITS = (("cm", "cm"), ("in", "inch"))


def to_centimetres(value: Decimal, unit: str) -> Decimal:
    return value * CENTIMETRES_PER_INCH if unit == "in" else value


def from_centimetres(value: Decimal, unit: str) -> Decimal:
    return value / CENTIMETRES_PER_INCH if unit == "in" else value


def format_dimensions(values, unit: str) -> str:
    converted = [
        from_centimetres(Decimal(value), unit).quantize(Decimal("0.01"))
        for value in values
    ]
    return " × ".join(str(value) for value in converted)
