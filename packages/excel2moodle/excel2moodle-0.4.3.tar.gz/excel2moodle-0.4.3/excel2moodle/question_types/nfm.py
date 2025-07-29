"""Numerical question multi implementation."""

import math
import re
from types import UnionType
from typing import TYPE_CHECKING, ClassVar

from asteval import Interpreter

from excel2moodle.core import stringHelpers
from excel2moodle.core.exceptions import QNotParsedException
from excel2moodle.core.globals import (
    Tags,
    XMLTags,
)
from excel2moodle.core.parser import QuestionParser
from excel2moodle.core.question import ParametricQuestion

if TYPE_CHECKING:
    import lxml.etree as ET


class NFMQuestion(ParametricQuestion):
    nfmMand: ClassVar[dict[Tags, type | UnionType]] = {
        Tags.RESULT: str,
        Tags.BPOINTS: str,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.answerVariants: list[ET.Element]

    def _setAnswerElement(self, variant: int = 1) -> None:
        prevAnsElement = self.element.find(XMLTags.ANSWER)
        if prevAnsElement is not None:
            self.element.remove(prevAnsElement)
            self.logger.debug("removed previous answer element")
        self.element.insert(5, self.answerVariants[variant - 1])


class NFMQuestionParser(QuestionParser):
    astEval = Interpreter(with_import=True)

    def __init__(self) -> None:
        super().__init__()
        self.genFeedbacks = [XMLTags.GENFEEDB]
        self.question: NFMQuestion
        module = self.settings.get(Tags.IMPORTMODULE)
        if module and not type(self).astEval.symtable.get(module):
            type(self).astEval(f"import {module}")
            self.logger.warning("Imported '%s' to Asteval symtable", module)

    def setup(self, question: NFMQuestion) -> None:
        self.question: NFMQuestion = question
        super().setup(question)

    def _parseAnswers(self) -> None:
        equation = self.rawInput.get(Tags.EQUATION)
        bps = self.rawInput.get(Tags.BPOINTS)
        ansElementsList: list[ET.Element] = []
        varNames: list[str] = self._getVarsList(bps)
        self.question.variables, number = self._getVariablesDict(varNames)
        for n in range(number):
            type(self).setupAstIntprt(self.question.variables, n)
            result = type(self).astEval(equation)
            if isinstance(result, float):
                firstResult = self.rawInput.get(Tags.FIRSTRESULT)
                if n == 0 and not math.isclose(result, firstResult, rel_tol=0.01):
                    self.logger.warning(
                        "The calculated result %s differs from given firstResult: %s",
                        result,
                        firstResult,
                    )
                ansElementsList.append(
                    self.getNumericAnsElement(result=round(result, 3)),
                )
            else:
                msg = f"The expression {equation} could not be evaluated."
                raise QNotParsedException(msg, self.question.id)
        self.question.answerVariants = ansElementsList
        self._setVariants(len(ansElementsList))

    def _setVariants(self, number: int) -> None:
        self.question.variants = number
        mvar = self.question.category.maxVariants
        if mvar is None:
            self.question.category.maxVariants = number
        else:
            self.question.category.maxVariants = min(number, mvar)

    @classmethod
    def setupAstIntprt(cls, var: dict[str, list[float | int]], index: int) -> None:
        """Setup the asteval Interpreter with the variables."""
        for name, value in var.items():
            cls.astEval.symtable[name] = value[index]

    def _getVariablesDict(self, keyList: list) -> tuple[dict[str, list[float]], int]:
        """Read variabel values for vars in `keyList` from `question.rawData`.

        Returns
        -------
        A dictionary containing a list of values for each variable
        The number of values for each variable

        """
        dic: dict = {}
        num: int = 0
        for k in keyList:
            val = self.rawInput[k.lower()]
            if isinstance(val, str):
                li = stringHelpers.getListFromStr(val)
                num = len(li)
                variables: list[float] = [float(i.replace(",", ".")) for i in li]
                dic[str(k)] = variables
            else:
                dic[str(k)] = [str(val)]
                num = 1
        self.logger.debug("The following variables were provided: %s", dic)
        return dic, num

    @staticmethod
    def _getVarsList(bps: str | list[str]) -> list:
        """Durchsucht den bulletPoints String nach den Variablen ``{var}``.

        It only finds variables after the ``=`` sign, to not catch LaTex.
        """
        varNames = []
        regexFinder = re.compile(r"=\s*\{(\w+)\}")
        if isinstance(bps, list):
            for _p in bps:
                varNames.extend(regexFinder.findall(str(_p)))
        else:
            varNames = regexFinder.findall(str(bps))
        return varNames
