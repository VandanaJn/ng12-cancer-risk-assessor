from pathlib import Path
import re

PROMPT_PATH = Path(__file__).parent / "PROMPTS.md"

def load_system_prompt(section: str) -> str:
    """
    Load a named prompt section from PROMPTS.md.

    Args:
        section: Section header name (e.g. 'ROOT_AGENT')

    Returns:
        Prompt text for that section.
    """
    text = PROMPT_PATH.read_text(encoding="utf-8")

    pattern = rf"## {section}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.S)

    if not match:
        raise ValueError(f"Prompt section '{section}' not found in PROMPTS.md")

    return match.group(1).strip()