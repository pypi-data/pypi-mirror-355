from pathlib import Path

import pytest

from excel2moodle.core.question import Picture
from excel2moodle.core.settings import Settings

settings = Settings()


imgFolder = Path("./test/Abbildungen")


qID = "10103"
katName = "MC1"


@pytest.mark.parametrize(
    ("imgKey", "expected"),
    [
        ("1", "10101.png"),
        ("true", "10103.svg"),
        ("1_a", "10101_a.png"),
        ("10101", "10101.png"),
        ("03", "10103.svg"),
        pytest.param("101_a", "10101_a.png", marks=pytest.mark.xfail),
    ],
)
def test_PictureFindImgFile(imgKey, expected) -> None:
    imgF = (imgFolder / katName).resolve()
    picture = Picture(imgKey, imgF, qID, width=300)
    print(picture.path)
    p = str(picture.path.stem + picture.path.suffix)
    assert p == expected


@pytest.mark.parametrize(
    ("imgKey", "expected"),
    [
        ("2_b", "10102_b"),
        ("1_a", "10101_a"),
        ("10101", "10101"),
        ("5-c", "10105-c"),
        ("201", "10201"),
        ("101_a", "10101_a"),
        pytest.param("false", None, marks=pytest.mark.xfail),
        pytest.param("101_a", "10101_a", marks=pytest.mark.xfail),
    ],
)
def test_Picture_EvaluateCorrectPicID(imgKey, expected) -> None:
    imgF = (imgFolder / katName).resolve(strict=True)
    picture = Picture(imgKey, imgF, qID, width=300)
    assert picture.picID == expected
