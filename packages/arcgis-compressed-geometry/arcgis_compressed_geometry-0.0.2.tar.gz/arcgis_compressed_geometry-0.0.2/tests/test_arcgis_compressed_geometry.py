from arcgis_compressed_geometry import decode, encode


def test_decode_when_no_z_and_no_m():
    points = decode("+1m91-6fkfr+202tp+k+f+7+3+34+2d")
    assert points is not None
    assert len(points) == 4

    assert abs(points[0][0] - (-122.40645857695421)) < 0.0001
    assert abs(points[0][1] - 37.78272915354862) < 0.0001

    assert abs(points[1][0] - (-122.40609876765315)) < 0.0001
    assert abs(points[1][1] - 37.78299901052442) < 0.0001

    assert abs(points[2][0] - (-122.40597283439777)) < 0.0001
    assert abs(points[2][1] - 37.78305298191958) < 0.0001

    assert abs(points[3][0] - (-122.40417378789242)) < 0.0001
    assert abs(points[3][1] - 37.7844382477287) < 0.0001


def test_decode_when_no_z_and_no_m_new_version():
    points = decode("+0+1+0+1m91-6fkfr+202tp+k+f+7+3+34+2d")
    assert points is not None
    assert len(points) == 4

    assert abs(points[0][0] - (-122.40645857695421)) < 0.0001
    assert abs(points[0][1] - 37.78272915354862) < 0.0001

    assert abs(points[1][0] - (-122.40609876765315)) < 0.0001
    assert abs(points[1][1] - 37.78299901052442) < 0.0001

    assert abs(points[2][0] - (-122.40597283439777)) < 0.0001
    assert abs(points[2][1] - 37.78305298191958) < 0.0001

    assert abs(points[3][0] - (-122.40417378789242)) < 0.0001
    assert abs(points[3][1] - 37.7844382477287) < 0.0001


def test_decode_when_has_z_and_no_m():
    points = decode("+0+1+1+1+emjd+3j07m+3+0+0+1-3-1|+9og+0+lv4+0+lv4")
    assert points is not None
    assert len(points) == 4

    assert abs(points[0][0] - 481901.0) < 0.0001
    assert abs(points[0][1] - 3768566.0) < 0.0001
    assert abs(points[0][2] - 0) < 0.0001

    assert abs(points[1][0] - 481904.0) < 0.0001
    assert abs(points[1][1] - 3768566.0) < 0.0001
    assert abs(points[1][2] - 2.25) < 0.0001

    assert abs(points[2][0] - 481904.0) < 0.0001
    assert abs(points[2][1] - 3768567.0) < 0.0001
    assert abs(points[2][2] - 2.25) < 0.0001

    assert abs(points[3][0] - 481901.0) < 0.0001
    assert abs(points[3][1] - 3768566.0) < 0.0001
    assert abs(points[3][2] - 4.5) < 0.0001


def test_decode_when_has_m_and_no_z():
    points = decode(
        "+0+1+2+1m91-6733n+1pjfe+g-e+1b-r+9-9+c-h+2-j-3-v-7-j-b-m-5-7-e-f-1a-u"
        "-6-7-4-9-3-a-1-n+1-4j|+5rg+81s+7n+i0+4f+7r+7g+ce+7n+9j+3h+7n+ib+3a+3q"
        "+45+97+1qs"
    )
    assert points is not None
    assert len(points) == 17

    assert abs(points[0][0] - (-117.37020778987137)) < 0.0001
    assert abs(points[0][1] - 33.96106863362418) < 0.0001
    assert abs(points[0][2] - 1.3753333333333333) < 0.0001

    assert abs(points[1][0] - (-117.36991994243051)) < 0.0001
    assert abs(points[1][1] - 33.96081676711343) < 0.0001
    assert abs(points[1][2] - 1.4165) < 0.0001

    assert abs(points[2][0] - (-117.3691463524332)) < 0.0001
    assert abs(points[2][1] - 33.960331024556986) < 0.0001
    assert abs(points[2][2] - 1.5125) < 0.0001

    assert abs(points[3][0] - (-117.36898443824772)) < 0.0001
    assert abs(points[3][1] - 33.9601691103715) < 0.0001
    assert abs(points[3][2] - 1.5363333333333333) < 0.0001


def test_decode_when_has_m_and_z():
    points = decode(
        "+0+1+3+1+emjd+3j07m+3+0+0+1-3-1|+9og+0+lv4+0+lv4|+5rg+uq+r9+au+168"
    )
    assert points is not None
    assert len(points) == 4

    assert abs(points[0][0] - 481901.0) < 0.0001
    assert abs(points[0][1] - 3768566.0) < 0.0001
    assert abs(points[0][2] - 0) < 0.0001
    assert abs(points[0][3] - 0.16433333333333333) < 0.0001

    assert abs(points[1][0] - 481904.0) < 0.0001
    assert abs(points[1][1] - 3768566.0) < 0.0001
    assert abs(points[1][2] - 2.25) < 0.0001
    assert abs(points[1][3] - 0.30983333333333335) < 0.0001

    assert abs(points[2][0] - 481904.0) < 0.0001
    assert abs(points[2][1] - 3768567.0) < 0.0001
    assert abs(points[2][2] - 2.25) < 0.0001
    assert abs(points[2][3] - 0.36816666666666664) < 0.0001

    assert abs(points[3][0] - 481901.0) < 0.0001
    assert abs(points[3][1] - 3768566.0) < 0.0001
    assert abs(points[3][2] - 4.5) < 0.0001
    assert abs(points[3][3] - 0.5721666666666667) < 0.0001


def test_encode_when_no_z_and_no_m():
    coordinates = [
        [-122.40645857695421, 37.78272915354862],
        [-122.40609876765315, 37.78299901052442],
        [-122.40597283439777, 37.78305298191958],
        [-122.40417378789242, 37.7844382477287],
    ]
    geometry = encode(coordinates, "xy", 55585)
    assert geometry == "+0+1+0+1m91-6fkfr+202tp+k+f+7+3+34+2d"


def test_encode_when_has_z_and_no_m():
    coordinates = [
        [481901.0, 3768566.0, 0],
        [481904.0, 3768566.0, 2.25],
        [481904.0, 3768567.0, 2.25],
        [481901.0, 3768566.0, 4.5],
    ]
    geometry = encode(coordinates, "xyz", xy_factor=1, z_factor=10000)
    assert geometry == "+0+1+1+1+emjd+3j07m+3+0+0+1-3-1|+9og+0+lv4+0+lv4"


def test_encode_when_has_m_and_no_z():
    coordinates = [
        [-117.37020778987137, 33.96106863362418, 1.3753333333333333],
        [-117.36991994243051, 33.96081676711343, 1.4165],
        [-117.3691463524332, 33.960331024556986, 1.5125],
        [-117.36898443824772, 33.9601691103715, 1.5363333333333333],
    ]
    geometry = encode(coordinates, "xym", xy_factor=55585, m_factor=6000)
    assert geometry == "+0+1+2+1m91-6733n+1pjfe+g-e+1b-r+9-9|+5rg+81s+7n+i0+4f"
    coordinates = [
        (-117.37020778987137, 33.96106863362418, 1.3753333333333333),
        (-117.36991994243051, 33.96081676711343, 1.4165),
        (-117.3691463524332, 33.960331024556986, 1.5125),
        (-117.36898443824772, 33.9601691103715, 1.5363333333333333),
    ]
    geometry = encode(coordinates, "xym", xy_factor=55585, m_factor=6000)
    assert geometry == "+0+1+2+1m91-6733n+1pjfe+g-e+1b-r+9-9|+5rg+81s+7n+i0+4f"


def test_encode_when_has_m_and_has_z():
    coordinates = [
        [481901.0, 3768566.0, 0, 0.16433333333333333],
        [481904.0, 3768566.0, 2.25, 0.30983333333333335],
        [481904.0, 3768567.0, 2.25, 0.36816666666666664],
        [481901.0, 3768566.0, 4.5, 0.5721666666666667],
    ]
    geometry = encode(coordinates, "xyzm", 1, z_factor=10000, m_factor=6000)
    assert (
        geometry
        == "+0+1+3+1+emjd+3j07m+3+0+0+1-3-1|+9og+0+lv4+0+lv4|+5rg+uq+r9+au+168"
    )
    coordinates = [
        (481901.0, 3768566.0, 0, 0.16433333333333333),
        (481904.0, 3768566.0, 2.25, 0.30983333333333335),
        (481904.0, 3768567.0, 2.25, 0.36816666666666664),
        (481901.0, 3768566.0, 4.5, 0.5721666666666667),
    ]
    geometry = encode(coordinates, "xyzm", 1, z_factor=10000, m_factor=6000)
    assert (
        geometry
        == "+0+1+3+1+emjd+3j07m+3+0+0+1-3-1|+9og+0+lv4+0+lv4|+5rg+uq+r9+au+168"
    )
