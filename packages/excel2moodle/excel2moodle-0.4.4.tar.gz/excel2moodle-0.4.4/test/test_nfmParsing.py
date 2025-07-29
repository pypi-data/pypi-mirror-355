from pathlib import Path
from typing import TYPE_CHECKING

import lxml.etree as ET
import pytest

from excel2moodle.core.dataStructure import QuestionDB
from excel2moodle.core.settings import Settings, Tags

if TYPE_CHECKING:
    from excel2moodle.core.question import Question

settings = Settings()

katName = "NFM2"
database = QuestionDB(settings)

settings.set(Tags.QUESTIONVARIANT, 1)
database.spreadsheet = Path("test/TestQuestion.ods")
excelFile = settings.get(Tags.SPREADSHEETPATH)
database.readCategoriesMetadata(excelFile)
database.initAllCategories(excelFile)


def test_resultValueOfNFMQuestion() -> None:
    category = database.categories[katName]
    settings.set(Tags.TOLERANCE, 0.01)
    database.setupAndParseQuestion(category, 1)
    tree = ET.Element("quiz")
    qlist: list[Question] = []
    qlist.append(category.questions[1])
    print(qlist)
    settings.set(Tags.QUESTIONVARIANT, 1)
    database._appendQElements(category, qlist, tree, includeHeader=False)
    ET.dump(tree)
    answer = tree.find("question").find("answer")
    tolerance = answer.find("tolerance")
    result = answer.find("text")
    print(result)
    assert result.text == "127.0"
    assert tolerance.text == "1.27"


@pytest.mark.parametrize(
    ("relTol", "absTol"),
    [(0.01, 1.27), (0.02, 2.54)],
)
def test_toleranceUsageModified(relTol, absTol) -> None:
    category = database.categories[katName]
    settings.set(Tags.TOLERANCE, relTol)
    database.setupAndParseQuestion(category, 1)
    tree = ET.Element("quiz")
    qlist: list[Question] = []
    qlist.append(category.questions[1])
    print(qlist)
    settings.set(Tags.QUESTIONVARIANT, 1)
    database._appendQElements(category, qlist, tree, includeHeader=False)
    ET.dump(tree)
    answer = tree.find("question").find("answer")
    tolerance = answer.find("tolerance")
    assert tolerance.text == str(absTol)
