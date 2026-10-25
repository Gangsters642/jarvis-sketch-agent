import json
import re
import xml.etree.ElementTree as ET

ALLOWED_SVG_SHAPES = {
    "circle", "rect", "line", "polyline", "polygon", "ellipse", "path", "text"
}

FORBIDDEN_PATTERNS = [
    (r"<\s*script\b", "Security Error: <script> tags allowed nahi hain."),
    (r"javascript\s*:", "Security Error: 'javascript:' links allowed nahi hain."),
    (r"\bon\w+\s*=", "Security Error: HTML event attributes (jaise onload/onclick) allowed nahi hain."),
    (r"<\s*(iframe|object|embed|foreignObject)\b", "Security Error: External embedded tags allowed nahi hain."),
]

VALID_COORD_COMMANDS = {
    "CANVAS", "LINE", "RECT", "CIRCLE", "ELLIPSE", "POLYLINE", "POLYGON"
}


def validate_input(raw_code: str, fmt: str = "svg"):
    """
    Validates drawing input safely without executing arbitrary code.
    Returns: (is_valid: bool, message: str, parsed_data: any)
    """
    if not raw_code or not raw_code.strip():
        return False, "Error: Drawing code khali hai. Kuch SVG ya drawing instructions paste karen.", None

    code = raw_code.strip()
    fmt = (fmt or "svg").lower().strip()

    # 1. Global security scan
    for pattern, err_msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, code, flags=re.IGNORECASE):
            return False, err_msg, None

    # 2. Format-specific validation
    if fmt == "svg":
        return _validate_svg(code)
    elif fmt == "json":
        return _validate_json(code)
    elif fmt == "coords":
        return _validate_coords(code)
    else:
        return False, f"Error: Format '{fmt}' supported nahi hai. SVG, JSON, ya COORDS select karen.", None


def _validate_svg(code: str):
    # If user only provided inner shapes (e.g. <circle ... />), wrap in <svg>
    if not re.search(r"<\s*svg\b", code, flags=re.IGNORECASE):
        wrapped = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" '
            'width="500" height="500">\n' + code + "\n</svg>"
        )
    else:
        wrapped = code
        if "xmlns=" not in wrapped:
            wrapped = re.sub(
                r"<\s*svg\b",
                '<svg xmlns="http://www.w3.org/2000/svg"',
                wrapped,
                count=1,
                flags=re.IGNORECASE,
            )

    try:
        root = ET.fromstring(wrapped)
    except ET.ParseError as exc:
        return False, f"SVG Syntax Error: XML/SVG tags sahi band nahi huay ({exc}).", None

    # Check that at least one visible drawing shape exists
    found_shapes = 0
    for elem in root.iter():
        tag_name = elem.tag.split("}")[-1].lower()
        if tag_name in ALLOWED_SVG_SHAPES:
            found_shapes += 1

    if found_shapes == 0:
        return (
            False,
            "Error: SVG mein koi drawing shape (circle, rect, line, path, polygon, etc.) nahi mili.",
            None,
        )

    return True, f"Valid SVG ({found_shapes} shape elements verified).", wrapped


def _validate_json(code: str):
    try:
        data = json.loads(code)
    except json.JSONDecodeError as exc:
        return False, f"JSON Syntax Error: Line {exc.lineno}, Column {exc.colno} par format galat hai.", None

    if isinstance(data, list):
        shapes = data
        payload = {"width": 500, "height": 500, "shapes": shapes}
    elif isinstance(data, dict) and isinstance(data.get("shapes"), list):
        shapes = data["shapes"]
        payload = data
    else:
        return False, "JSON Error: JSON mein 'shapes' list honi chahiye.", None

    if not shapes:
        return False, "JSON Error: 'shapes' list khali hai.", None

    for idx, item in enumerate(shapes, start=1):
        if not isinstance(item, dict) or "type" not in item:
            return False, f"JSON Error: Shape #{idx} mein 'type' mojood nahi hai.", None
        stype = str(item["type"]).lower()
        if stype not in ALLOWED_SVG_SHAPES:
            return False, f"JSON Error: Shape #{idx} ka type '{stype}' supported nahi hai.", None

    return True, f"Valid JSON ({len(shapes)} shapes verified).", payload


def _validate_coords(code: str):
    lines = [
        line.strip()
        for line in code.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return False, "Coordinates Error: Koi valid command line nahi mili.", None

    parsed_commands = []
    for idx, line in enumerate(lines, start=1):
        parts = line.split()
        cmd = parts[0].upper()
        if cmd not in VALID_COORD_COMMANDS:
            return (
                False,
                f"Coordinates Error (Line {idx}): Unknown command '{cmd}'. Allowed: {', '.join(sorted(VALID_COORD_COMMANDS))}",
                None,
            )
        if len(parts) < 2:
            return False, f"Coordinates Error (Line {idx}): Command '{cmd}' ke parameters missing hain.", None
        parsed_commands.append((cmd, parts[1:]))

    return True, f"Valid Coordinates ({len(parsed_commands)} commands verified).", parsed_commands
