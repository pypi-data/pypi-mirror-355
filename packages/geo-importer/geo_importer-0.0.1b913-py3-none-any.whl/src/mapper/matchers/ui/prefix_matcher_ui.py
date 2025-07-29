# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prefix_matcher.ui'
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
    QPushButton, QSizePolicy, QSpinBox, QWidget)

class Ui_PrefixMatcher(object):
    def setupUi(self, PrefixMatcher):
        if not PrefixMatcher.objectName():
            PrefixMatcher.setObjectName(u"PrefixMatcher")
        self.layoutForm = QFormLayout(PrefixMatcher)
        self.layoutForm.setObjectName(u"layoutForm")
        self.layoutForm.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.lblExcel = QLabel(PrefixMatcher)
        self.lblExcel.setObjectName(u"lblExcel")

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblExcel)

        self.comboExcel = QComboBox(PrefixMatcher)
        self.comboExcel.setObjectName(u"comboExcel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboExcel.sizePolicy().hasHeightForWidth())
        self.comboExcel.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboExcel)

        self.lblGeo = QLabel(PrefixMatcher)
        self.lblGeo.setObjectName(u"lblGeo")

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblGeo)

        self.comboGeo = QComboBox(PrefixMatcher)
        self.comboGeo.setObjectName(u"comboGeo")
        sizePolicy.setHeightForWidth(self.comboGeo.sizePolicy().hasHeightForWidth())
        self.comboGeo.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.comboGeo)

        self.lblLength = QLabel(PrefixMatcher)
        self.lblLength.setObjectName(u"lblLength")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblLength)

        self.spinLength = QSpinBox(PrefixMatcher)
        self.spinLength.setObjectName(u"spinLength")
        sizePolicy.setHeightForWidth(self.spinLength.sizePolicy().hasHeightForWidth())
        self.spinLength.setSizePolicy(sizePolicy)
        self.spinLength.setMinimum(1)
        self.spinLength.setMaximum(10)
        self.spinLength.setValue(3)

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spinLength)

        self.lblStats = QLabel(PrefixMatcher)
        self.lblStats.setObjectName(u"lblStats")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lblStats)

        self.labelStats = QLabel(PrefixMatcher)
        self.labelStats.setObjectName(u"labelStats")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.labelStats)

        self.buttonRemove = QPushButton(PrefixMatcher)
        self.buttonRemove.setObjectName(u"buttonRemove")
        sizePolicy.setHeightForWidth(self.buttonRemove.sizePolicy().hasHeightForWidth())
        self.buttonRemove.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.buttonRemove)


        self.retranslateUi(PrefixMatcher)

        QMetaObject.connectSlotsByName(PrefixMatcher)
    # setupUi

    def retranslateUi(self, PrefixMatcher):
        self.lblExcel.setText(QCoreApplication.translate("PrefixMatcher", u"Excel Column:", None))
        self.lblGeo.setText(QCoreApplication.translate("PrefixMatcher", u"Geo Column:", None))
        self.lblLength.setText(QCoreApplication.translate("PrefixMatcher", u"Prefix Length:", None))
        self.lblStats.setText(QCoreApplication.translate("PrefixMatcher", u"Zuordnungen:", None))
        self.labelStats.setText(QCoreApplication.translate("PrefixMatcher", u"0", None))
        self.buttonRemove.setText(QCoreApplication.translate("PrefixMatcher", u"Delete", None))
#if QT_CONFIG(tooltip)
        self.buttonRemove.setToolTip(QCoreApplication.translate("PrefixMatcher", u"Remove Matcher", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

