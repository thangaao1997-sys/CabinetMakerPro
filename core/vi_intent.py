"""Strict Vietnamese cabinet intent parser (DRAFT ONLY).

Only accepts the documented sentence grammar. Never guesses dimensions,
base height, construction, or accepts editing of existing designs.
"""
import re
import unicodedata

from .ai_idea_core import CommandError, validate_command

_TYPES = {
    "tủ bếp": "kitchen",
    "tủ áo": "wardrobe",
    "tủ giày": "shoe",
    "tủ khác": "other",
}
# Anchored grammar: tạo <kind> rộng <mm> sâu <mm> cao <mm> [chân <mm>]
_NUMBER = r"(?:0|[1-9][0-9]*)(?:[.,][0-9]+)?"
_PATTERN = re.compile(
    rf"^tạo (?P<kind>tủ bếp|tủ áo|tủ giày|tủ khác) "
    rf"rộng (?P<width>{_NUMBER}) mm sâu (?P<depth>{_NUMBER}) mm "
    rf"cao (?P<height>{_NUMBER}) mm"
    rf"(?: chân (?P<base>{_NUMBER}) mm)?$",
    re.UNICODE,
)

class IntentError(ValueError):
    pass

def parse_vietnamese(text, request_id="IDEA-DRAFT"):
    if not isinstance(text, str) or not 0 < len(text) <= 500:
        raise IntentError("Câu lệnh phải là chuỗi không rỗng (tối đa 500 ký tự).")
    phrase = unicodedata.normalize("NFC", " ".join(text.lower().split()))
    match = _PATTERN.fullmatch(phrase)
    if not match:
        raise IntentError(
            "Chỉ hỗ trợ: tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm. "
            "Tủ không phải tủ bếp cần ghi rõ 'chân 50 mm' hoặc 'chân 17 mm'. "
            "Không được suy đoán kích thước hoặc bỏ qua yêu cầu khác."
        )
    def number(key):
        raw = match.group(key)
        return float(raw.replace(",", ".")) if raw is not None else None
    raw_base = match.group("base")
    data = {
        "schema_version": "ai-idea.command.v1",
        "request_id": request_id,
        "cabinet_type": _TYPES[match.group("kind")],
        "dimensions_mm": {key: number(key) for key in ("width", "depth", "height")},
        "design_lock": False,
    }
    if raw_base is not None:
        data["base_mm"] = number("base")
    try:
        result = validate_command(data)
    except (CommandError, TypeError, ValueError) as exc:
        raise IntentError(str(exc)) from exc
    return result
