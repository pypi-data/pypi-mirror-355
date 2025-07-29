# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'exportSettingsDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QCheckBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpinBox, QWidget)

class Ui_ExportDialog(object):
    def setupUi(self, ExportDialog):
        if not ExportDialog.objectName():
            ExportDialog.setObjectName(u"ExportDialog")
        ExportDialog.resize(572, 217)
        self.horizontalLayout = QHBoxLayout(ExportDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(5, 5, 5, 5)
        self.label_10 = QLabel(ExportDialog)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.spinBoxDefaultQVariant = QSpinBox(ExportDialog)
        self.spinBoxDefaultQVariant.setObjectName(u"spinBoxDefaultQVariant")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spinBoxDefaultQVariant)

        self.label_9 = QLabel(ExportDialog)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.checkBoxIncludeCategories = QCheckBox(ExportDialog)
        self.checkBoxIncludeCategories.setObjectName(u"checkBoxIncludeCategories")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.checkBoxIncludeCategories)

        self.label = QLabel(ExportDialog)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label)

        self.btnExportFile = QPushButton(ExportDialog)
        self.btnExportFile.setObjectName(u"btnExportFile")
        self.btnExportFile.setMinimumSize(QSize(200, 0))

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.btnExportFile)

        self.line_2 = QFrame(ExportDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.line_2)

        self.label_2 = QLabel(ExportDialog)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.questionCount = QSpinBox(ExportDialog)
        self.questionCount.setObjectName(u"questionCount")
        self.questionCount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.questionCount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.questionCount.setMaximum(999)

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.LabelRole, self.questionCount)

        self.pointCount = QDoubleSpinBox(ExportDialog)
        self.pointCount.setObjectName(u"pointCount")
        self.pointCount.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.pointCount.setAutoFillBackground(True)
        self.pointCount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pointCount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.pointCount.setDecimals(1)
        self.pointCount.setMaximum(1000.000000000000000)

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.FieldRole, self.pointCount)


        self.horizontalLayout.addLayout(self.formLayout_2)

        self.buttonBox = QDialogButtonBox(ExportDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ExportDialog)
        self.buttonBox.accepted.connect(ExportDialog.accept)
        self.buttonBox.rejected.connect(ExportDialog.reject)

        QMetaObject.connectSlotsByName(ExportDialog)
    # setupUi

    def retranslateUi(self, ExportDialog):
        ExportDialog.setWindowTitle(QCoreApplication.translate("ExportDialog", u"Dialog", None))
        self.label_10.setText(QCoreApplication.translate("ExportDialog", u"Default Question Variant", None))
#if QT_CONFIG(tooltip)
        self.label_9.setToolTip(QCoreApplication.translate("ExportDialog", u"If enabled, all questions will be categorized, when importing into moodle. Otherwise they will all be imported into one category", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("ExportDialog", u"Include Categories", None))
        self.checkBoxIncludeCategories.setText("")
        self.label.setText(QCoreApplication.translate("ExportDialog", u"Export File:", None))
        self.btnExportFile.setText("")
        self.label_2.setText(QCoreApplication.translate("ExportDialog", u"Export Information:", None))
        self.questionCount.setSuffix(QCoreApplication.translate("ExportDialog", u"   Qst.", None))
        self.pointCount.setSuffix(QCoreApplication.translate("ExportDialog", u"  Pts.", None))
    # retranslateUi

