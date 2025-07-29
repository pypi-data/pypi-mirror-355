"""Implementation of the cloze question type.

This question type is like the NFM but supports multiple fields of answers.
All Answers are calculated off an equation using the same variables.
"""

import math
import re

import lxml.etree as ET

from excel2moodle.core.exceptions import QNotParsedException
from excel2moodle.core.globals import (
    Tags,
    TextElements,
)
from excel2moodle.core.question import ParametricQuestion
from excel2moodle.core.settings import Tags
from excel2moodle.question_types.nfm import NFMQuestionParser


class ClozeQuestion(ParametricQuestion):
    """Cloze Question Type."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.answerVariants: dict[int, list[float]] = {}
        self.answerStrings: dict[int, list[str]] = {}
        self.answerTypes: dict[int, str] = {}
        self.questionTexts: dict[int, list[ET.Element]] = {}
        self.partsNum: int = 0

    def _setAnswerElement(self, variant: int = 1) -> None:
        for part, ans in self.answerVariants.items():
            result = ans[variant - 1]
            if self.answerTypes.get(part, None) == "MC":
                ansStr = ClozeQuestionParser.getMCAnsStr(answers)
            else:
                ansStr = ClozeQuestionParser.getNumericAnsStr(
                    result,
                    self.rawData.get(Tags.TOLERANCE),
                    wrongSignCount=self.rawData.get(Tags.WRONGSIGNPERCENT),
                )
            ul = TextElements.ULIST.create()
            item = TextElements.LISTITEM.create()
            item.text = ansStr
            ul.append(item)
            self.questionTexts[part].append(ul)
            self.logger.debug("Appended Question Parts %s to main text", part)
            self.questionTexts[part].append(ET.Element("hr"))

    def _assembleMainTextParts(self, variant=0) -> list[ET.Element]:
        textParts = super()._assembleMainTextParts(variant=variant)
        self.logger.debug("Appending QuestionParts to main text")
        for paragraphs in self.questionTexts.values():
            for par in paragraphs:
                textParts.append(par)
        return textParts


class ClozeQuestionParser(NFMQuestionParser):
    """Parser for the cloze question type."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.question: ClozeQuestion

    def setup(self, question: ClozeQuestion) -> None:
        self.question: ClozeQuestion = question
        super().setup(question)

    def _parseAnswers(self) -> None:
        self._parseAnswerParts()
        self._parseQuestionParts()

    def _parseAnswerParts(self) -> None:
        """Parse the numeric or MC result items."""
        self.question.answerTypes: dict[int, str] = {
            self.getPartNumber(key): self.rawInput[key]
            for key in self.rawInput
            if key.startswith(Tags.PARTTYPE)
        }
        equations: dict[int, str] = {
            self.getPartNumber(key): self.rawInput[key]
            for key in self.rawInput
            if key.startswith(Tags.RESULT)
        }
        self.logger.debug("Got the following answers: %s", equations)
        bps = str(self.rawInput[Tags.BPOINTS])
        varNames: list[str] = self._getVarsList(bps)
        numericAnswers: dict[int, list[float]] = {key: [] for key in equations}
        self.question.variables, number = self._getVariablesDict(varNames)
        for n in range(number):
            self.setupAstIntprt(self.question.variables, n)
            for ansNum, eq in equations.items():
                result = self.astEval(eq)
                if isinstance(result, float):
                    firstResult = self.rawInput.get(Tags.FIRSTRESULT)
                    if n == 0 and not math.isclose(result, firstResult, rel_tol=0.01):
                        self.logger.warning(
                            "The calculated result %s differs from given firstResult: %s",
                            result,
                            firstResult,
                        )
                    numericAnswers[ansNum].append(result)
                else:
                    msg = f"The expression {eq} could not be evaluated."
                    raise QNotParsedException(msg, self.question.id)

        self.question.answerVariants = numericAnswers
        self._setVariants(number)

    def _parseQuestionParts(self) -> None:
        """Generate the question parts aka the clozes."""
        parts: dict[int, list[str]] = {
            self.getPartNumber(key): self.rawInput[key]
            for key in self.rawInput
            if key.startswith(Tags.QUESTIONPART)
        }
        questionParts: dict[int, list[ET.Element]] = {}
        for number, text in parts.items():
            questionParts[number] = []
            for t in text:
                questionParts[number].append(TextElements.PLEFT.create())
                questionParts[number][-1].text = t
        self.logger.debug("The Question Parts are created:", questionParts)
        self.question.questionTexts = questionParts
        self.question.partsNum = len(questionParts)
        self.logger.info("The Question has %s parts", self.question.partsNum)

    # def setMainText(self) -> None:
    #     super().setMainText()
    #     self.question.qtextParagraphs

    def getPartNumber(self, indexKey: str) -> int:
        """Return the number of the question Part.

        The number should be given after the `@` sign.
        This is number is used, to reference the question Text
        and the expected answer fields together.
        """
        try:
            num = re.findall(r":(\d+)$", indexKey)[0]
        except IndexError:
            msg = f"No :i question Part value given for {indexKey}"
            raise QNotParsedException(msg, self.question.id)
        else:
            return int(num)

    @staticmethod
    def getNumericAnsStr(
        result: float,
        tolerance: float,
        weight: int = 1,
        wrongSignCount: int = 50,
        wrongSignFeedback: str = "your result has the wrong sign (+-)",
    ) -> str:
        """Generate the answer string from `result`.

        Parameters.
        ----------
        weight:
            The weight of the answer relative to the other answer elements.
            Of one answer has `weight=2` and two other answers `weight=1`,
            this answer will be counted as 50% of the questions points.
            The other two will counted as 25% of the questions points.

        wrongSignCount:
            If the wrong sign `+` or `-` is given, how much of the points should be given.
            Interpreted as percent.
        tolerance:
            The relative tolerance, as fraction

        """
        absTol = f":{round(result * tolerance, 3)}"
        answerParts: list[str | float] = [
            "{",
            weight,
            ":NUMERICAL:=",
            round(result, 3),
            absTol,
            "~%",
            wrongSignCount,
            "%",
            round(result * (-1), 3),
            absTol,
            f"#{wrongSignFeedback}",
            "}",
        ]
        answerPStrings = [str(part) for part in answerParts]
        return "".join(answerPStrings)

    @staticmethod
    def getMCAnsStr(
        true: list[str],
        false: list[str],
        weight: int = 1,
    ) -> str:
        """Generate the answer string for the MC answers."""
        answerParts: list[str | float] = [
            "{",
            weight,
            ":MC:",
            "}",
        ]
        answerPStrings = [str(part) for part in answerParts]
        return "".join(answerPString)
