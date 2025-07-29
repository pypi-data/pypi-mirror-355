import logging
import re

import lxml.etree as ET

import excel2moodle.core.etHelpers as eth
from excel2moodle.core.exceptions import QNotParsedException
from excel2moodle.core.globals import (
    Tags,
    TextElements,
    XMLTags,
    feedbackStr,
    feedBElements,
)
from excel2moodle.core.question import Picture, Question
from excel2moodle.core.settings import Settings, Tags
from excel2moodle.logger import LogAdapterQuestionID

loggerObj = logging.getLogger(__name__)


class QuestionParser:
    """Setup the Parser Object.

    This is the superclass which implements the general Behaviour of he Parser.
    Important to implement the answers methods.
    """

    settings = Settings()

    def __init__(self) -> None:
        """Initialize the general Question parser."""
        self.genFeedbacks: list[XMLTags] = []
        self.logger: logging.LoggerAdapter

    def setup(self, question: Question) -> None:
        self.question: Question = question
        self.rawInput = question.rawData
        self.logger = LogAdapterQuestionID(loggerObj, {"qID": self.question.id})
        self.logger.debug(
            "The following Data was provided: %s",
            self.rawInput,
        )

    def hasPicture(self) -> bool:
        """Create a ``Picture`` object ``question``if the question needs a pic."""
        if hasattr(self, "picture") and self.question.picture.ready:
            return True
        picKey = self.rawInput.get(Tags.PICTURE)
        f = self.settings.get(Tags.PICTUREFOLDER)
        svgFolder = (f / self.question.katName).resolve()
        if not hasattr(self.question, "picture"):
            self.question.picture = Picture(picKey, svgFolder, self.question.id)
        return bool(self.question.picture.ready)

    def setMainText(self) -> None:
        paragraphs: list[ET._Element] = [TextElements.PLEFT.create()]
        ET.SubElement(paragraphs[0], "b").text = f"ID {self.question.id}"
        text = self.rawInput[Tags.TEXT]
        for t in text:
            paragraphs.append(TextElements.PLEFT.create())
            paragraphs[-1].text = t
        self.question.qtextParagraphs = paragraphs
        self.logger.debug("Created main Text with: %s paragraphs", len(text))

    def setBPoints(self) -> None:
        """If there bulletPoints are set in the Spreadsheet it creates an unordered List-Element in ``Question.bulletList``."""
        if Tags.BPOINTS in self.rawInput:
            bps: list[str] = self.rawInput[Tags.BPOINTS]
            try:
                bulletList = self.formatBulletList(bps)
            except IndexError:
                msg = f"konnt Bullet Liste {self.question.id} nicht generieren"
                raise QNotParsedException(
                    msg,
                    self.question.id,
                    # exc_info=e,
                )
            self.logger.debug(
                "Generated BPoint List: \n %s",
                ET.tostring(bulletList, encoding="unicode"),
            )
            self.question.bulletList = bulletList

    def formatBulletList(self, bps: list[str]) -> ET.Element:
        self.logger.debug("Formatting the bulletpoint list")
        name = []
        var = []
        quant = []
        unit = []
        unorderedList = TextElements.ULIST.create()
        for item in bps:
            sc_split = item.split()
            name.append(sc_split[0])
            var.append(sc_split[1])
            quant.append(sc_split[3])
            unit.append(sc_split[4])
        for i in range(len(name)):
            if re.fullmatch(r"{\w+}", quant[i]):
                self.logger.debug("Got an variable bulletItem")
                num_s = quant[i]
            else:
                self.logger.debug("Got a normal bulletItem")
                num = quant[i].split(",")
                if len(num) == 2:
                    num_s = f"{num[0]!s},\\!{num[1]!s}~"
                else:
                    num_s = f"{num[0]!s},\\!0~"
            bullet = TextElements.LISTITEM.create()
            bullet.text = (
                f"{name[i]}: \\( {var[i]} = {num_s} \\mathrm{{ {unit[i]}  }}\\)\n"
            )
            unorderedList.append(bullet)
        return unorderedList

    def appendToTmpEle(
        self,
        eleName: str,
        text: str | Tags,
        txtEle=False,
        **attribs,
    ) -> None:
        """Append ``text`` to the temporary Element.

        It uses the data from ``self.rawInput`` if ``text`` is type``DFIndex``
        Otherwise the value of ``text`` will be inserted.
        """
        t = self.rawInput[text] if isinstance(text, Tags) else text
        if txtEle is False:
            self.tmpEle.append(eth.getElement(eleName, t, **attribs))
        elif txtEle is True:
            self.tmpEle.append(eth.getTextElement(eleName, t, **attribs))

    def _appendStandardTags(self) -> None:
        """Append the elements defined in the ``cls.standardTags``."""
        self.logger.debug(
            "Appending the Standard Tags %s", type(self.question).standardTags.items()
        )
        for k, v in type(self.question).standardTags.items():
            self.appendToTmpEle(k, text=v)

    def parse(self) -> None:
        """Parse the Question.

        Generates an new Question Element stored as ``self.tmpEle:ET.Element``
        if no Exceptions are raised, ``self.tmpEle`` is passed to ``self.question.element``
        """
        self.logger.info("Starting to parse")
        self.tmpEle: ET.Elemnt = ET.Element(
            XMLTags.QUESTION, type=self.question.moodleType
        )
        self.appendToTmpEle(XMLTags.NAME, text=Tags.NAME, txtEle=True)
        self.appendToTmpEle(XMLTags.ID, text=self.question.id)
        if self.hasPicture():
            self.tmpEle.append(self.question.picture.element)
        self.tmpEle.append(ET.Element(XMLTags.QTEXT, format="html"))
        self.appendToTmpEle(XMLTags.POINTS, text=str(self.question.points))
        self._appendStandardTags()
        for feedb in self.genFeedbacks:
            self.tmpEle.append(eth.getFeedBEle(feedb))
        ansList = self._parseAnswers()
        self.setMainText()
        self.setBPoints()
        if ansList is not None:
            for ele in ansList:
                self.tmpEle.append(ele)
        self.question.element = self.tmpEle
        self.question.isParsed = True
        self.logger.info("Sucessfully parsed")

    def getFeedBEle(
        self,
        feedback: XMLTags,
        text: str | None = None,
        style: TextElements | None = None,
    ) -> ET.Element:
        span = feedBElements[feedback] if style is None else style.create()
        if text is None:
            text = feedbackStr[feedback]
        ele = ET.Element(feedback, format="html")
        par = TextElements.PLEFT.create()
        span.text = text
        par.append(span)
        ele.append(eth.getCdatTxtElement(par))
        return ele

    def _parseAnswers(self) -> list[ET.Element] | None:
        """Needs to be implemented in the type-specific subclasses."""
        return None

    def getNumericAnsElement(
        self,
        result: float,
        fraction: float = 100,
        format: str = "moodle_auto_format",
    ) -> ET.Element:
        """Get ``<answer/>`` Element specific for the numerical Question.

        The element contains those children:
            ``<text/>`` which holds the value of the answer
            ``<tolerance/>`` with the *relative* tolerance for the result in percent
            ``<feedback/>`` with general feedback for a true answer.
        """
        ansEle: ET.Element = eth.getTextElement(
            XMLTags.ANSWER,
            text=str(result),
            fraction=str(fraction),
            format=format,
        )
        ansEle.append(
            eth.getFeedBEle(
                XMLTags.ANSFEEDBACK,
                feedbackStr["right1Percent"],
                TextElements.SPANGREEN,
            ),
        )
        absTolerance = round(result * self.rawInput.get(Tags.TOLERANCE), 4)
        ansEle.append(eth.getElement(XMLTags.TOLERANCE, text=str(absTolerance)))
        return ansEle
