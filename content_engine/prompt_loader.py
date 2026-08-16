"""Content Engine Prompt 加载器"""
from pathlib import Path
from typing import Optional

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_CACHE: dict[str, str] = {}

def load_ce_prompt(name: str, variables: Optional[dict[str, str]] = None) -> str:
    if name in _CACHE:
        content = _CACHE[name]
    else:
        prompt_path = _PROMPTS_DIR / f"{name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"CE Prompt 不存在: {prompt_path}")
        content = prompt_path.read_text(encoding="utf-8").strip()
        _CACHE[name] = content
    if variables:
        for key, value in variables.items():
            content = content.replace("{{" + key + "}}", value)
    return content

def reload_ce_cache():
    _CACHE.clear()
