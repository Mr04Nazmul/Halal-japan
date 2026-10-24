"""Strict JAN-8/JAN-13 validation for Japanese food staging imports.

The crawler recognizes other GTIN lengths for discovery, but the staging
archive stores only Japanese JAN-8 and JAN-13 values in jan_code.
"""
import re

def jan_valid(value):
    if value is None:
        return False
    code=str(value)
    if not re.fullmatch(r"(?:[0-9]{8}|[0-9]{13})",code):
        return False
    weighted=sum(int(d)*(3 if i%2==0 else 1) for i,d in enumerate(code[-2::-1]))
    return (weighted+int(code[-1]))%10==0
