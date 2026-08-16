"""
Prompt 加载器

从 prompts/ 目录加载外部 Markdown Prompt 文件。
禁止在业务代码中硬编码 Prompt。

用法:
    prompt = load_prompt("rewrite")
    prompt = load_prompt("rewrite", variables={"source": "奇门小道"})
"""
from pathlib import Path
from typing import Optional


_PROMPTS_DIR: Path = Path(__file__).resolve().parent.parent / "prompts"
_CACHE: dict[str, str] = {}


def load_prompt(
    name: str,
    variables: Optional[dict[str, str]] = None,
) -> str:
    """
    加载 prompt 文件

    Args:
        name: prompt 文件名（不含 .md）
        variables: 模板变量替换

    Returns:
        Prompt 文本
    """
    # 缓存命中
    if name in _CACHE:
        content = _CACHE[name]
    else:
        prompt_path = _PROMPTS_DIR / f"{name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt 文件不存在: {prompt_path}\n"
                f"请创建 prompts/{name}.md"
            )

        content = prompt_path.read_text(encoding="utf-8").strip()
        _CACHE[name] = content

    # 变量替换
    if variables:
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", value)

    return content


def reload_cache():
    """重新加载所有 prompt（调试用）"""
    _CACHE.clear()
