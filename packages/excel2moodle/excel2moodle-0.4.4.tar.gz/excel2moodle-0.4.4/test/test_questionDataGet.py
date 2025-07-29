from pathlib import Path

import pandas as pd
import pytest

from excel2moodle.core.dataStructure import QuestionDB
from excel2moodle.core.settings import Settings, Tags
from excel2moodle.core.validator import Validator

settings = Settings()

katName = "NFM2"
database = QuestionDB(settings)

settings.set(Tags.QUESTIONVARIANT, 1)
excelFile = Path("test/TestQuestion.ods").resolve()
database.spreadsheet = excelFile
database.readCategoriesMetadata(excelFile)
category = database.initCategory(katName, sheetPath=excelFile)

validator = Validator()
qdat: pd.Series = category.dataframe[1]
validator.setup(qdat, 1)
validator.validate()
questionData = validator.getQuestionData()


@pytest.mark.parametrize(
    ("tag", "expectedType"),
    [
        (Tags.BPOINTS, list),
        (Tags.TEXT, list),
        (Tags.ANSPICWIDTH, int),
        (Tags.POINTS, float),
    ],
)
def test_validatorQuestionDataGeneration(tag, expectedType) -> None:
    assert type(questionData.get(tag)) == expectedType


@pytest.mark.parametrize(
    ("tag", "expectedLiteral"),
    [
        (Tags.TYPE, ("MC", "NFM", "CLOZE")),
    ],
)
def test_literalReturs(tag, expectedLiteral) -> None:
    assert questionData.get(tag) in expectedLiteral


def test_ReturnTypeWhileIterating() -> None:
    for tag in Tags:
        if tag.place == "project":
            val = questionData.get(tag)
            if val:
                assert type(val) == tag.typ()
