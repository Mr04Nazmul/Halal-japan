"""Strict JAN-8/JAN-13 validation and preservation for Japanese food staging."""
import re

def jan_valid(value):
    if value is None:
        return False
    code=str(value)
    if not re.fullmatch(r"(?:[0-9]{8}|[0-9]{13})",code):
        return False
    weighted=sum(int(d)*(3 if i%2==0 else 1) for i,d in enumerate(code[-2::-1]))
    return (weighted+int(code[-1]))%10==0


def jan_for_staging(value):
    """Return a checksum-valid JAN-8 or JAN-13 unchanged; otherwise None."""
    if value is None:
        return None
    code = str(value)
    return code if jan_valid(code) else None
