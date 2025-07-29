# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'regex_matcher.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_RegexMatcher(object):
    def setupUi(self, RegexMatcher):
        if not RegexMatcher.objectName():
            RegexMatcher.setObjectName(u"RegexMatcher")
        self.layoutForm = QFormLayout(RegexMatcher)
        self.layoutForm.setObjectName(u"layoutForm")
        self.lblExcel = QLabel(RegexMatcher)
        self.lblExcel.setObjectName(u"lblExcel")

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblExcel)

        self.comboExcel = QComboBox(RegexMatcher)
        self.comboExcel.setObjectName(u"comboExcel")

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboExcel)

        self.lblExcelRegex = QLabel(RegexMatcher)
        self.lblExcelRegex.setObjectName(u"lblExcelRegex")

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblExcelRegex)

        self.editExcelRegex = QLineEdit(RegexMatcher)
        self.editExcelRegex.setObjectName(u"editExcelRegex")

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.editExcelRegex)

        self.lblGeo = QLabel(RegexMatcher)
        self.lblGeo.setObjectName(u"lblGeo")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblGeo)

        self.comboGeo = QComboBox(RegexMatcher)
        self.comboGeo.setObjectName(u"comboGeo")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.comboGeo)

        self.lblGeoRegex = QLabel(RegexMatcher)
        self.lblGeoRegex.setObjectName(u"lblGeoRegex")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lblGeoRegex)

        self.editGeoRegex = QLineEdit(RegexMatcher)
        self.editGeoRegex.setObjectName(u"editGeoRegex")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.editGeoRegex)

        self.lblStats = QLabel(RegexMatcher)
        self.lblStats.setObjectName(u"lblStats")

        self.layoutForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.lblStats)

        self.labelStats = QLabel(RegexMatcher)
        self.labelStats.setObjectName(u"labelStats")

        self.layoutForm.setWidget(4, QFormLayout.ItemRole.FieldRole, self.labelStats)

        self.buttonRemove = QPushButton(RegexMatcher)
        self.buttonRemove.setObjectName(u"buttonRemove")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonRemove.sizePolicy().hasHeightForWidth())
        self.buttonRemove.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.buttonRemove)


        self.retranslateUi(RegexMatcher)

        QMetaObject.connectSlotsByName(RegexMatcher)
    # setupUi

    def retranslateUi(self, RegexMatcher):
        self.lblExcel.setText(QCoreApplication.translate("RegexMatcher", u"Excel Column:", None))
        self.lblExcelRegex.setText(QCoreApplication.translate("RegexMatcher", u"Excel RegEx:", None))
        self.editExcelRegex.setPlaceholderText(QCoreApplication.translate("RegexMatcher", u"e.g. `(\\d{4})`", None))
        self.lblGeo.setText(QCoreApplication.translate("RegexMatcher", u"Geo Column:", None))
        self.lblGeoRegex.setText(QCoreApplication.translate("RegexMatcher", u"Geo RegEx:", None))
        self.editGeoRegex.setPlaceholderText(QCoreApplication.translate("RegexMatcher", u"e.g. `ID-(\\w+)`", None))
        self.lblStats.setText(QCoreApplication.translate("RegexMatcher", u"Mappings:", None))
        self.labelStats.setText(QCoreApplication.translate("RegexMatcher", u"0", None))
        self.buttonRemove.setText(QCoreApplication.translate("RegexMatcher", u"Delete", None))
#if QT_CONFIG(tooltip)
        self.buttonRemove.setToolTip(QCoreApplication.translate("RegexMatcher", u"Remove Matcher", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

