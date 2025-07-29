# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fuzzy_matcher.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFormLayout,
    QLabel, QPushButton, QSizePolicy, QWidget)

class Ui_FuzzyMatcher(object):
    def setupUi(self, FuzzyMatcher):
        if not FuzzyMatcher.objectName():
            FuzzyMatcher.setObjectName(u"FuzzyMatcher")
        self.layoutForm = QFormLayout(FuzzyMatcher)
        self.layoutForm.setObjectName(u"layoutForm")
        self.layoutForm.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.lblExcel = QLabel(FuzzyMatcher)
        self.lblExcel.setObjectName(u"lblExcel")

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblExcel)

        self.comboExcel = QComboBox(FuzzyMatcher)
        self.comboExcel.setObjectName(u"comboExcel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboExcel.sizePolicy().hasHeightForWidth())
        self.comboExcel.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboExcel)

        self.lblGeo = QLabel(FuzzyMatcher)
        self.lblGeo.setObjectName(u"lblGeo")

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblGeo)

        self.comboGeo = QComboBox(FuzzyMatcher)
        self.comboGeo.setObjectName(u"comboGeo")
        sizePolicy.setHeightForWidth(self.comboGeo.sizePolicy().hasHeightForWidth())
        self.comboGeo.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.comboGeo)

        self.lblThreshold = QLabel(FuzzyMatcher)
        self.lblThreshold.setObjectName(u"lblThreshold")

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblThreshold)

        self.spinThreshold = QDoubleSpinBox(FuzzyMatcher)
        self.spinThreshold.setObjectName(u"spinThreshold")
        sizePolicy.setHeightForWidth(self.spinThreshold.sizePolicy().hasHeightForWidth())
        self.spinThreshold.setSizePolicy(sizePolicy)
        self.spinThreshold.setMinimum(0.000000000000000)
        self.spinThreshold.setMaximum(100.000000000000000)
        self.spinThreshold.setSingleStep(1.000000000000000)
        self.spinThreshold.setValue(80.000000000000000)
        self.spinThreshold.setDecimals(1)

        self.layoutForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spinThreshold)

        self.lblStats = QLabel(FuzzyMatcher)
        self.lblStats.setObjectName(u"lblStats")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lblStats)

        self.labelStats = QLabel(FuzzyMatcher)
        self.labelStats.setObjectName(u"labelStats")

        self.layoutForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.labelStats)

        self.buttonRemove = QPushButton(FuzzyMatcher)
        self.buttonRemove.setObjectName(u"buttonRemove")
        sizePolicy.setHeightForWidth(self.buttonRemove.sizePolicy().hasHeightForWidth())
        self.buttonRemove.setSizePolicy(sizePolicy)

        self.layoutForm.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.buttonRemove)


        self.retranslateUi(FuzzyMatcher)

        QMetaObject.connectSlotsByName(FuzzyMatcher)
    # setupUi

    def retranslateUi(self, FuzzyMatcher):
        self.lblExcel.setText(QCoreApplication.translate("FuzzyMatcher", u"Excel Column:", None))
        self.lblGeo.setText(QCoreApplication.translate("FuzzyMatcher", u"Geo Column:", None))
        self.lblThreshold.setText(QCoreApplication.translate("FuzzyMatcher", u"Threshold (%):", None))
        self.lblStats.setText(QCoreApplication.translate("FuzzyMatcher", u"Mappings:", None))
        self.labelStats.setText(QCoreApplication.translate("FuzzyMatcher", u"0", None))
        self.buttonRemove.setText(QCoreApplication.translate("FuzzyMatcher", u"Delete", None))
#if QT_CONFIG(tooltip)
        self.buttonRemove.setToolTip(QCoreApplication.translate("FuzzyMatcher", u"Remove Matcher", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

