from typing import List, Tuple, Sequence, Union

COMRESSED_GEOMETRY_PREFIX = "+0+1+"

POINT_XY = Tuple[float, float]
POINT_XYZ = Tuple[float, float, float]
POINT_XYM = Tuple[float, float, float]
POINT_XYZM = Tuple[float, float, float, float]


def decode(geometry: str) -> List[List[float]]:
    """
    Decode a polyline string into a set of coordinates.

    :param geometry: ArcGIS Compressed Geometry string, e.g.
        '+1m91-6fkfr+202tp+k+f+7+3+34+2d'.
    :return: List of coordinate lists, supports
        [x, z],[x,y,z],[x,y,m],[x,y,z,m].
    """
    parts: Sequence[str] = geometry.split("|")
    first: str = parts[0]
    format_version = first[0:2]
    if format_version != "+0":
        return _decode(geometry)
    else:
        flag = first[5:6]
        xy_part = first[6:]
        z_part = parts[1] if int(flag) == 1 else None
        m_part = parts[1] if int(flag) == 2 else None
        (z_part, m_part) = (
            (parts[1], parts[2]) if int(flag) == 3 else (z_part, m_part)
        )
        return _decode(xy_part, z_part, m_part)


def encode(
    coordinates: Union[
        List[List[float]],
        List[POINT_XY],
        List[POINT_XYZ],
        List[POINT_XYM],
        List[POINT_XYZM],
    ],
    coordinate_format="xy",
    xy_factor=10000,
    z_factor=None,
    m_factor=None,
) -> str:
    """
    Encode a set of coordinates in ArcGIS Compressed Geometry string.

    :param coordinates: List of coordinate lists.
    :param coordinate_format: format of coordinate, supports
        "xy","xyz","xym","xyzm"
    :param xy_factor factor for xy coordinate
    :param z_factor factor for z coordinate
    :param m_factor factor for m coordinate
    :return: The encoded polyline string.
    """
    xy_geometry = _encode_xy([c[0:2] for c in coordinates], xy_factor)
    z_geometry = (
        "|" + _encode_z([c[2] for c in coordinates], z_factor)
        if coordinate_format.startswith("xyz")
        else ""
    )
    m_geometry = (
        "|" + _encode_m([c[2] for c in coordinates], m_factor)
        if coordinate_format == "xym"
        else ""
    )
    m_geometry = (
        "|" + _encode_m([c[3] for c in coordinates], m_factor)
        if coordinate_format == "xyzm"
        else m_geometry
    )
    z_flag = 1 if z_geometry else 0
    m_flag = 2 if m_geometry else 0
    flag = z_flag | m_flag
    return (
        f"{COMRESSED_GEOMETRY_PREFIX}{flag}"
        f"{xy_geometry}{z_geometry}{m_geometry}"
    )


def _extract(part: str) -> List[str]:
    result = []
    current = ""

    for char in part:
        if char in ["+", "-"]:
            if current:
                result.append(current)
            current = char
        else:
            current += char

    if current:
        result.append(current)

    return result


def _decode(xy_part: str, z_part=None, m_part=None) -> List[List[float]]:
    coordinates_xy = _decode_xy(xy_part)
    if z_part and m_part:
        return [
            xy + list(zm)
            for xy, zm in zip(
                coordinates_xy, zip(_decode_z(z_part), _decode_z(m_part))
            )
        ]
    elif z_part:
        return [xy + [z] for xy, z in zip(coordinates_xy, _decode_z(z_part))]
    elif m_part:
        return [xy + [m] for xy, m in zip(coordinates_xy, _decode_m(m_part))]
    return coordinates_xy


def _encode_xy(
    coordinates: Union[
        List[List[float]],
        List[POINT_XY],
        List[POINT_XYZ],
        List[POINT_XYM],
        List[POINT_XYZM],
    ],
    factor=10000,
) -> str:
    result = []
    first_x = int(coordinates[0][0] * factor)
    first_y = int(coordinates[0][1] * factor)
    result.append(base32_encode(factor))
    result.append(base32_encode(first_x))
    result.append(base32_encode(first_y))

    prev_x = first_x
    prev_y = first_y

    for x, y in coordinates[1:]:
        curr_x = int(x * factor)
        curr_y = int(y * factor)
        diff_x = curr_x - prev_x
        diff_y = curr_y - prev_y
        result.append(base32_encode(diff_x))
        result.append(base32_encode(diff_y))
        prev_x = curr_x
        prev_y = curr_y

    return "".join(result)


def base32_encode(num: int) -> str:
    """
    convert int to 32-based string
    """
    if num == 0:
        return "+0"

    chars = "0123456789abcdefghijklmnopqrstuv"
    result = []
    is_negative = num < 0
    num = abs(num)

    while num:
        num, remainder = divmod(num, 32)
        result.append(chars[remainder])

    result.reverse()
    return ("-" if is_negative else "+") + "".join(result)


def _encode_m(coordinates: List[float], factor=10000) -> str:
    result = []
    first = int(coordinates[0] * factor)
    result.append(base32_encode(factor))
    result.append(base32_encode(first))

    prev = first

    for x in coordinates[1:]:
        curr = int(x * factor)
        diff = curr - prev
        result.append(base32_encode(diff))
        prev = curr

    return "".join(result)


def _encode_z(coordinates: List[float], factor=10000) -> str:
    return _encode_m(coordinates, factor)


def _decode_xy(part: str) -> List[List[float]]:
    xys = _extract(part)
    factor = int(xys[0], 32)
    difference_x = 0
    difference_y = 0
    coordinates = []
    for i in range(1, len(xys), 2):
        point = []
        x = int(xys[i], 32)
        y = int(xys[i + 1], 32)
        difference_x += x
        difference_y += y
        x = difference_x / factor
        y = difference_y / factor
        point.append(x)
        point.append(y)
        coordinates.append(point)
    return coordinates


def _decode_m(part: str) -> List[float]:
    result = []
    difference = 0
    ms: Sequence[str] = _extract(part)
    factor = int(ms[0], 32)
    for i in range(1, len(ms)):
        val = int(ms[i], 32)
        difference += val
        val = difference / factor
        result.append(val)
    return result


def _decode_z(part: str) -> List[float]:
    return _decode_m(part)
