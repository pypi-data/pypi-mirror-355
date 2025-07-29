from typing import Dict, Tuple, Optional
from requests.structures import CaseInsensitiveDict
import re

_token_pattern  = r"([\w!#$%&'*+\-.^_`|~]+)"
_quoted_pattern = r'"([^"]*)"'
_option_regex = re.compile(fr";\s*{_token_pattern}=(?:{_token_pattern}|{_quoted_pattern})", re.ASCII)
_firefox_escape_fix = re.compile(r'\\"(?!; |\s*$)')

def parse_options_header(value: str) -> Tuple[str, Dict[str, str]]:
    value = _firefox_escape_fix.sub("%22", value)
    pos = value.find(";")
    if pos >= 0:
        options = { 
            m.group(1).lower(): m.group(2) or m.group(3).replace("%22", "") for m in _option_regex.finditer(value[pos:])
        }
        value = value[:pos]
    else:
        options = {}

    return value.strip().lower(), options

def get_header_value(headers: Dict[str, str], header: str, default_value: Optional[str] = None) -> Optional[str]:
    return CaseInsensitiveDict(headers or {}).get(header, default_value)
