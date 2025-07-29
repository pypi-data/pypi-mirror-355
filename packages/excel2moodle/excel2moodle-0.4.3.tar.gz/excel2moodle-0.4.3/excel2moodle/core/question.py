import base64
import logging
import re
from pathlib import Path
from re import Match
from types import UnionType
from typing import ClassVar, Literal, overload

import lxml.etree as ET

from excel2moodle.core import etHelpers
from excel2moodle.core.category import Category
from excel2moodle.core.exceptions import QNotParsedException
from excel2moodle.core.globals import (
    QUESTION_TYPES,
    Tags,
    TextElements,
    XMLTags,
)
from excel2moodle.core.settings import Settings, Tags
from excel2moodle.logger import LogAdapterQuestionID

loggerObj = logging.getLogger(__name__)
settings = Settings()


class QuestionData(dict):
    @overload
    def get(
        self,
        key: Literal[Tags.NAME, Tags.ANSTYPE, Tags.PICTURE, Tags.EQUATION],
    ) -> str: ...
    @overload
    def get(
        self,
        key: Literal[Tags.BPOINTS, Tags.TRUE, Tags.FALSE, Tags.QUESTIONPART, Tags.TEXT],
    ) -> list: ...
    @overload
    def get(
        self,
        key: Literal[
            Tags.VERSION,
            Tags.NUMBER,
            Tags.PICTUREWIDTH,
            Tags.ANSPICWIDTH,
            Tags.WRONGSIGNPERCENT,
        ],
    ) -> int: ...
    @overload
    def get(
        self, key: Literal[Tags.PARTTYPE, Tags.TYPE]
    ) -> Literal["MC", "NFM", "CLOZE"]: ...
    @overload
    def get(
        self, key: Literal[Tags.TOLERANCE, Tags.POINTS, Tags.FIRSTRESULT]
    ) -> float: ...
    @overload
    def get(self, key: Literal[Tags.RESULT]) -> float | str: ...

    def get(self, key: Tags, default=None):
        if key in self:
            val = self[key]
            try:
                typed = key.typ()(val)
            except ValueError:
                return None
            return typed
        return settings.get(key)


class Question:
    standardTags: ClassVar[dict[str, str | float]] = {
        "hidden": 0,
        "penalty": 0.33333,
    }
    mandatoryTags: ClassVar[dict[Tags, type | UnionType]] = {
        Tags.TEXT: str,
        Tags.NAME: str,
        Tags.TYPE: str,
    }
    optionalTags: ClassVar[dict[Tags, type | UnionType]] = {
        Tags.PICTURE: int | str,
    }

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        dictionaries = ("standardTags", "mandatoryTags", "optionalTags")
        for dic in dictionaries:
            cls._mergeDicts(dic)

    @classmethod
    def _mergeDicts(cls, dictName) -> None:
        superDict = getattr(super(cls, cls), dictName)
        subDict = getattr(cls, dictName, {})
        mergedDict = superDict.copy()
        mergedDict.update(subDict)
        setattr(cls, dictName, mergedDict)

    @classmethod
    def addStandardTag(cls, key, value) -> None:
        cls.standardTags[key] = value

    def __init__(
        self,
        category: Category,
        rawData: QuestionData,
        parent=None,
        points: float = 0,
    ) -> None:
        self.rawData: QuestionData = rawData
        self.category = category
        self.katName = self.category.name
        self.moodleType = QUESTION_TYPES[self.qtype]
        self.points = points if points != 0 else self.category.points
        self.element: ET.Element = None
        self.isParsed: bool = False
        self.picture: Picture
        self.id: str
        self.qtextParagraphs: list[ET.Element] = []
        self.bulletList: ET.Element = None
        self._setID()
        self.logger = LogAdapterQuestionID(loggerObj, {"qID": self.id})
        self.logger.debug("Sucess initializing")

    @property
    def name(self) -> str:
        return self.rawData.get(Tags.NAME)

    @property
    def qtype(self) -> str:
        return self.rawData.get(Tags.TYPE)

    def __repr__(self) -> str:
        li: list[str] = []
        li.append(f"Question v{self.id}")
        li.append(f"{self.qtype}")
        return "\t".join(li)

    def assemble(self, variant=0) -> None:
        """Assemble the question to the valid xml Tree."""
        mainText = self._getTextElement()
        self.logger.debug("Starting assembly")
        self._setAnswerElement(variant=variant)
        textParts = self._assembleMainTextParts()
        if hasattr(self, "picture") and self.picture.ready:
            mainText.append(self.picture.element)
            self.logger.debug("Appended Picture element to text")
        mainText.append(etHelpers.getCdatTxtElement(textParts))

    def _assembleMainTextParts(self, variant=0) -> list[ET.Element]:
        """Assemble the Question Text.

        Intended for the cloze question, where the answers parts are part of the text.
        """
        self.logger.debug("inserting MainText to element")
        textParts: list[ET.Element] = []
        textParts.extend(self.qtextParagraphs)
        bullets = self._getBPoints(variant=variant)
        if bullets is not None:
            textParts.append(bullets)
        if hasattr(self, "picture") and self.picture.ready:
            textParts.append(self.picture.htmlTag)
            self.logger.debug("Appended Picture html to text")
        return textParts

    def _getTextElement(self) -> ET.Element:
        if self.element is not None:
            mainText = self.element.find(XMLTags.QTEXT)
            self.logger.debug(f"found existing Text in element {mainText=}")
            txtele = mainText.find("text")
            if txtele is not None:
                mainText.remove(txtele)
                self.logger.debug("removed previously existing questiontext")
            return mainText
        msg = "Cant assamble, if element is none"
        raise QNotParsedException(msg, self.id)

    def _getBPoints(self, variant: int = 0) -> ET.Element:
        if hasattr(self, "bulletList"):
            return self.bulletList
        return None

    def _setAnswerElement(self, variant: int = 0) -> None:
        pass

    def _setID(self, id=0) -> None:
        if id == 0:
            self.id: str = f"{self.category.id}{self.rawData.get(Tags.NUMBER):02d}"
        else:
            self.id: str = str(id)


class ParametricQuestion(Question):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.variants: int = 0
        self.variables: dict[str, list[float | int]] = {}

    def _getBPoints(self, variant: int = 1) -> ET.Element:
        """Get the bullet points with the variable set for `variant`."""
        if self.bulletList is None:
            msg = "Can't assemble a parametric question, without the bulletPoints variables"
            raise QNotParsedException(msg, self.id)
        # matches {a}, {some_var}, etc.
        varPlaceholder = re.compile(r"{(\w+)}")

        def replaceMatch(match: Match[str]) -> str | int | float:
            key = match.group(1)
            if key in self.variables:
                value = self.variables[key][variant]
                return f"{value}".replace(".", ",\\!")
            return match.group(0)  # keep original if no match

        unorderedList = TextElements.ULIST.create()
        for li in self.bulletList:
            listItemText = li.text or ""
            bullet = TextElements.LISTITEM.create()
            bullet.text = varPlaceholder.sub(replaceMatch, listItemText)
            unorderedList.append(bullet)
            self.logger.debug("Inserted Variables into List: %s", bullet.text)
        return unorderedList


class Picture:
    def __init__(
        self, picKey: str, imgFolder: Path, questionId: str, width: int = 0
    ) -> None:
        self.logger = LogAdapterQuestionID(loggerObj, {"qID": questionId})
        self.picID: str
        w: int = width if width > 0 else settings.get(Tags.PICTUREWIDTH)
        self.size: dict[str, str] = {"width": str(w)}
        self.ready: bool = False
        self.imgFolder = imgFolder
        self.htmlTag: ET.Element
        self.path: Path
        self.questionId: str = questionId
        self.logger.debug("Instantiating a new picture in %s", picKey)
        if self.getImgId(picKey):
            self.ready = self._getImg()
        else:
            self.ready = False

    def getImgId(self, imgKey: str) -> bool:
        """Get the image ID and width based on the given key.
        The key should either be the full ID (as the question) or only the question Num.
        If only the number is given, the category.id is prepended.
        The width should be specified by `ID:width:XX`. where xx is the px value.
        """
        width = re.findall(r"\:width\:(\d+)", str(imgKey))
        height = re.findall(r"\:height\:(\d+)", str(imgKey))
        if len(width) > 0 and width[0]:
            self.size["width"] = width[0]
        elif len(height) > 0 and height[0]:
            self.size["height"] = height[0]
            self.size.pop("width")
        self.logger.debug("Size of picture is %s", self.size)
        if imgKey in ("true", "True", "yes"):
            self.picID = self.questionId
            return True
        num: list[int | str] = re.findall(r"^\d+", str(imgKey))
        app: list[int | str] = re.findall(r"^\d+([A-Za-z_\-]+)", str(imgKey))
        if imgKey in ("false", "nan", False) or len(num) == 0:
            return False
        imgID: int = int(num[0])
        if imgID < 10:
            picID = f"{self.questionId[:3]}{imgID:02d}"
        elif imgID < 10000:
            picID = f"{self.questionId[:1]}{imgID:04d}"
        elif imgID <= 100000:
            picID = str(imgID)
        if len(app) > 0 and app[0]:
            self.picID = f"{picID}{app[0]}"
        else:
            self.picID = str(picID)
        self.logger.debug("Evaluated the imgID %s from %s", self.picID, imgKey)
        return True

    def _getBase64Img(self, imgPath: Path):
        with imgPath.open("rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")

    def _getImg(self) -> bool:
        suffixes = ["png", "svg", "jpeg", "jpg"]
        paths = [
            path
            for suf in suffixes
            for path in self.imgFolder.glob(f"{self.picID}.{suf}")
        ]
        self.logger.debug("Found the following paths %s", paths)
        try:
            self.path = paths[0]
        except IndexError:
            msg = f"The Picture {self.imgFolder}/{self.picID} is not found"
            self.logger.warning(msg=msg)
            self.element = None
            return False
            # raise FileNotFoundError(msg)
        base64Img = self._getBase64Img(self.path)
        self.element: ET.Element = ET.Element(
            "file",
            name=f"{self.path.name}",
            path="/",
            encoding="base64",
        )
        self.element.text = base64Img
        self.htmlTag = ET.Element(
            "img",
            src=f"@@PLUGINFILE@@/{self.path.name}",
            alt=f"Bild {self.path.name}",
            **self.size,
        )
        return True
