from typing import Callable, Dict, List, Optional, Any
import re

class TemplateRenderer:
    def __init__(self, source_resolver: Callable[[str], Any]):
        self.source_resolver: Callable[[str], Any] = source_resolver
        self.patterns: Dict[str, re.Pattern] = {
            "placeholder": re.compile(
                r"""\$\{                   # ${ 
                    ([a-zA-Z_][\w\-]*)     # key: input, env, etc.
                    (?:\.([^\|\}]+))?      # path: key, key.path[0], etc.
                    (?:\s*\|\s*([^\}]+))?  # default value after `|`
                \}""",                     # }
                re.VERBOSE,
            ),
            "keypath": re.compile(r"[-_\w]+|\[\d+\]"),
        }

    def render(self, data: Any) -> Any:
        return self._render_element(data)

    def _render_element(self, element: Any) -> Any:
        if isinstance(element, str):
            return self._render_text(element)
        
        if isinstance(element, dict):
            return { key: self._render_element(value) for key, value in element.items() }
        
        if isinstance(element, list):
            return [ self._render_element(item) for item in element ]
        
        return element

    def _render_text(self, text: str) -> Any:
        while True:
            match = self.patterns["placeholder"].search(text)
            
            if not match:
                break

            key, path, default, placeholder = match.group(1), match.group(2), match.group(3), match.group(0)
            try:
                value = self._resolve_by_path(self.source_resolver(key), path)
            except Exception:
                value = default or ""

            if placeholder == text:
                return value

            text = text.replace(placeholder, str(value))

        return text

    def _resolve_by_path(self, source: Any, path: Optional[str]) -> Any:
        parts: List[str] = self.patterns["keypath"].findall(path) if path else []
        current = source
        for part in parts:
            if isinstance(current, dict) and not part.startswith("["):
                if part in current:
                    current = current[part]
                else:
                    return None
            elif isinstance(current, list) and part.startswith("["):
                index = int(part[1:-1])
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        return current
