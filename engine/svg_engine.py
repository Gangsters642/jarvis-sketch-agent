import xml.etree.ElementTree as ET
from engine.validator import validate_input

ET.register_namespace("", "http://www.w3.org/2000/svg")

DEFAULT_STROKE = "#00f0ff"
DEFAULT_FILL = "none"
DEFAULT_STROKE_WIDTH = "2"


def generate_sketch(raw_code: str, fmt: str = "svg"):
    """
    Validates input and generates clean, portable SVG markup.
    Returns: (success: bool, message: str, svg_content: str | None)
    """
    is_valid, msg, parsed = validate_input(raw_code, fmt)
    if not is_valid:
        return False, msg, None

    fmt = (fmt or "svg").lower().strip()

    try:
        if fmt == "svg":
            svg_out = _process_svg(parsed)
        elif fmt == "json":
            svg_out = _process_json(parsed)
        elif fmt == "coords":
            svg_out = _process_coords(parsed)
        else:
            return False, f"Unsupported format: {fmt}", None

        return True, msg, svg_out
    except Exception as exc:
        return False, f"Drawing Engine Error: {exc}", None


def _process_svg(wrapped_svg: str) -> str:
    root = ET.fromstring(wrapped_svg)
    width = root.attrib.get("width", "500")
    height = root.attrib.get("height", "500")

    clean_w = str(width).replace("px", "").strip() or "500"
    clean_h = str(height).replace("px", "").strip() or "500"

    if "viewBox" not in root.attrib:
        root.set("viewBox", f"0 0 {clean_w} {clean_h}")
    if "width" not in root.attrib:
        root.set("width", clean_w)
    if "height" not in root.attrib:
        root.set("height", clean_h)

    xml_str = ET.tostring(root, encoding="unicode")
    if 'xmlns="http://www.w3.org/2000/svg"' not in xml_str:
        xml_str = xml_str.replace(
            "<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1
        )
    return xml_str


def _process_json(data: dict) -> str:
    width = str(data.get("width", 500))
    height = str(data.get("height", 500))
    bg = data.get("background")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
    ]

    if bg:
        lines.append(f'  <rect width="100%" height="100%" fill="{bg}" />')

    for item in data.get("shapes", []):
        stype = str(item.get("type", "")).lower()
        attrs = []
        for k, v in item.items():
            if k in ("type", "text_content"):
                continue
            attr_name = k.replace("_", "-")
            attrs.append(f'{attr_name}="{v}"')

        if "stroke=" not in " ".join(attrs) and stype != "text":
            attrs.append(f'stroke="{DEFAULT_STROKE}"')
        if "fill=" not in " ".join(attrs) and stype != "text":
            attrs.append(f'fill="{DEFAULT_FILL}"')
        if "stroke-width=" not in " ".join(attrs) and stype != "text":
            attrs.append(f'stroke-width="{DEFAULT_STROKE_WIDTH}"')

        attr_str = " ".join(attrs)
        if stype == "text":
            content = item.get("text_content", item.get("text", "JARVIS"))
            lines.append(f"  <text {attr_str}>{content}</text>")
        else:
            lines.append(f"  <{stype} {attr_str} />")

    lines.append("</svg>")
    return "\n".join(lines)


def _process_coords(commands: list) -> str:
    width, height = "500", "500"
    elements = []

    for cmd, args in commands:
        try:
            if cmd == "CANVAS" and len(args) >= 2:
                width, height = args[0], args[1]
            elif cmd == "LINE" and len(args) >= 4:
                x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
                stroke = args[4] if len(args) > 4 else DEFAULT_STROKE
                sw = args[5] if len(args) > 5 else DEFAULT_STROKE_WIDTH
                elements.append(
                    f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" />'
                )
            elif cmd == "CIRCLE" and len(args) >= 3:
                cx, cy, r = args[0], args[1], args[2]
                stroke = args[3] if len(args) > 3 else DEFAULT_STROKE
                fill = args[4] if len(args) > 4 else DEFAULT_FILL
                sw = args[5] if len(args) > 5 else DEFAULT_STROKE_WIDTH
                elements.append(
                    f'  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}" />'
                )
            elif cmd == "RECT" and len(args) >= 4:
                x, y, w, h = args[0], args[1], args[2], args[3]
                stroke = args[4] if len(args) > 4 else DEFAULT_STROKE
                fill = args[5] if len(args) > 5 else DEFAULT_FILL
                sw = args[6] if len(args) > 6 else DEFAULT_STROKE_WIDTH
                elements.append(
                    f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}" />'
                )
            elif cmd == "ELLIPSE" and len(args) >= 4:
                cx, cy, rx, ry = args[0], args[1], args[2], args[3]
                stroke = args[4] if len(args) > 4 else DEFAULT_STROKE
                fill = args[5] if len(args) > 5 else DEFAULT_FILL
                sw = args[6] if len(args) > 6 else DEFAULT_STROKE_WIDTH
                elements.append(
                    f'  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}" />'
                )
            elif cmd in ("POLYGON", "POLYLINE") and len(args) >= 2:
                tag = cmd.lower()
                pts = " ".join(args)
                elements.append(
                    f'  <{tag} points="{pts}" stroke="{DEFAULT_STROKE}" fill="{DEFAULT_FILL}" stroke-width="{DEFAULT_STROKE_WIDTH}" />'
                )
            else:
                raise ValueError(f"Command '{cmd}' ke arguments kam hain.")
        except Exception as exc:
            raise ValueError(f"Error in '{cmd}': {exc}")

    header = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
    return "\n".join([header] + elements + ["</svg>"])
