# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'unique_value_matcher.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QLabel, QPushButton, QSizePolicy, QWidget)

class Ui_UniqueValueMatcher(object):
    def setupUi(self, UniqueValueMatcher):
        if not UniqueValueMatcher.objectName():
            UniqueValueMatcher.setObjectName(u"UniqueValueMatcher")
        self.layoutForm = QFormLayout(UniqueValueMatcher)
        self.layoutForm.setObjectName(u"layoutForm")
        self.layoutForm.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.lblExcel = QLabel(UniqueValueMatcher)
        self.lblExcel.setObjectName(u"lblExcel")

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblExcel)

        self.comboExcel = QComboBox(UniqueValueMatcher)
        self.comboExcel.setObjectName(u"comboExcel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboExcel.sizePolicy().hasHeightForWidth())
        self.comboExcel.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboExcel)

        self.lblGeo = QLabel(UniqueValueMatcher)
        self.lblGeo.setObjectName(u"lblGeo")

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblGeo)

        self.comboGeo = QComboBox(UniqueValueMatcher)
        self.comboGeo.setObjectName(u"comboGeo")
        sizePolicy.setHeightForWidth(self.comboGeo.sizePolicy().hasHeightForWidth())
        self.comboGeo.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.comboGeo)

        self.lblStats = QLabel(UniqueValueMatcher)
        self.lblStats.setObjectName(u"lblStats")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblStats)

        self.labelStats = QLabel(UniqueValueMatcher)
        self.labelStats.setObjectName(u"labelStats")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.labelStats)

        self.cbIgnoreCase = QCheckBox(UniqueValueMatcher)
        self.cbIgnoreCase.setObjectName(u"cbIgnoreCase")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.cbIgnoreCase)

        self.cbIgnoreWhitespace = QCheckBox(UniqueValueMatcher)
        self.cbIgnoreWhitespace.setObjectName(u"cbIgnoreWhitespace")

        self.layoutForm.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.cbIgnoreWhitespace)

        self.cbIgnorePunctuation = QCheckBox(UniqueValueMatcher)
        self.cbIgnorePunctuation.setObjectName(u"cbIgnorePunctuation")

        self.layoutForm.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.cbIgnorePunctuation)

        self.buttonRemove = QPushButton(UniqueValueMatcher)
        self.buttonRemove.setObjectName(u"buttonRemove")
        sizePolicy.setHeightForWidth(self.buttonRemove.sizePolicy().hasHeightForWidth())
        self.buttonRemove.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(6, QFormLayout.ItemRole.SpanningRole, self.buttonRemove)


        self.retranslateUi(UniqueValueMatcher)

        QMetaObject.connectSlotsByName(UniqueValueMatcher)
    # setupUi

    def retranslateUi(self, UniqueValueMatcher):
        self.lblExcel.setText(QCoreApplication.translate("UniqueValueMatcher", u"Excel Column:", None))
        self.lblGeo.setText(QCoreApplication.translate("UniqueValueMatcher", u"Geo Column:", None))
        self.lblStats.setText(QCoreApplication.translate("UniqueValueMatcher", u"Mappings:", None))
        self.labelStats.setText(QCoreApplication.translate("UniqueValueMatcher", u"0", None))
        self.cbIgnoreCase.setText(QCoreApplication.translate("UniqueValueMatcher", u"Ignore Case", None))
        self.cbIgnoreWhitespace.setText(QCoreApplication.translate("UniqueValueMatcher", u"Ignore Whitespace", None))
        self.cbIgnorePunctuation.setText(QCoreApplication.translate("UniqueValueMatcher", u"Ignore Punctuation", None))
        self.buttonRemove.setText(QCoreApplication.translate("UniqueValueMatcher", u"Delete", None))
#if QT_CONFIG(tooltip)
        self.buttonRemove.setToolTip(QCoreApplication.translate("UniqueValueMatcher", u"Remove Matcher", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

