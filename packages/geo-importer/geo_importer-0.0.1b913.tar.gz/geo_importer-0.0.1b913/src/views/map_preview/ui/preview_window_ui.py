# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preview_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_PreviewWindow(object):
    def setupUi(self, PreviewWindow):
        if not PreviewWindow.objectName():
            PreviewWindow.setObjectName(u"PreviewWindow")
        self.centralwidget = QWidget(PreviewWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutRoot = QVBoxLayout(self.centralwidget)
        self.layoutRoot.setObjectName(u"layoutRoot")
        self.splitMain = QSplitter(self.centralwidget)
        self.splitMain.setObjectName(u"splitMain")
        self.splitMain.setOrientation(Qt.Horizontal)
        self.pageControls = QWidget(self.splitMain)
        self.pageControls.setObjectName(u"pageControls")
        self.layoutCtrls = QVBoxLayout(self.pageControls)
        self.layoutCtrls.setObjectName(u"layoutCtrls")
        self.layoutCtrls.setContentsMargins(0, 0, 0, 0)
        self.groupGeo = QGroupBox(self.pageControls)
        self.groupGeo.setObjectName(u"groupGeo")
        self.layoutGeo = QHBoxLayout(self.groupGeo)
        self.layoutGeo.setObjectName(u"layoutGeo")
        self.lineEditGeoPath = QLineEdit(self.groupGeo)
        self.lineEditGeoPath.setObjectName(u"lineEditGeoPath")
        self.lineEditGeoPath.setReadOnly(True)

        self.layoutGeo.addWidget(self.lineEditGeoPath)

        self.buttonBrowseGeo = QPushButton(self.groupGeo)
        self.buttonBrowseGeo.setObjectName(u"buttonBrowseGeo")

        self.layoutGeo.addWidget(self.buttonBrowseGeo)


        self.layoutCtrls.addWidget(self.groupGeo)

        self.groupMapping = QGroupBox(self.pageControls)
        self.groupMapping.setObjectName(u"groupMapping")
        self.layoutMapping = QFormLayout(self.groupMapping)
        self.layoutMapping.setObjectName(u"layoutMapping")
        self.label = QLabel(self.groupMapping)
        self.label.setObjectName(u"label")

        self.layoutMapping.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.comboGeoId = QComboBox(self.groupMapping)
        self.comboGeoId.setObjectName(u"comboGeoId")

        self.layoutMapping.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboGeoId)

        self.label1 = QLabel(self.groupMapping)
        self.label1.setObjectName(u"label1")

        self.layoutMapping.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label1)

        self.comboStatsId = QComboBox(self.groupMapping)
        self.comboStatsId.setObjectName(u"comboStatsId")

        self.layoutMapping.setWidget(1, QFormLayout.ItemRole.FieldRole, self.comboStatsId)

        self.label2 = QLabel(self.groupMapping)
        self.label2.setObjectName(u"label2")

        self.layoutMapping.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label2)

        self.comboStatsValue = QComboBox(self.groupMapping)
        self.comboStatsValue.setObjectName(u"comboStatsValue")

        self.layoutMapping.setWidget(2, QFormLayout.ItemRole.FieldRole, self.comboStatsValue)


        self.layoutCtrls.addWidget(self.groupMapping)

        self.buttonRender = QPushButton(self.pageControls)
        self.buttonRender.setObjectName(u"buttonRender")

        self.layoutCtrls.addWidget(self.buttonRender)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layoutCtrls.addItem(self.verticalSpacer)

        self.splitMain.addWidget(self.pageControls)
        self.groupMap = QGroupBox(self.splitMain)
        self.groupMap.setObjectName(u"groupMap")
        self.layoutMap = QVBoxLayout(self.groupMap)
        self.layoutMap.setObjectName(u"layoutMap")
        self.pageMap = QWidget(self.groupMap)
        self.pageMap.setObjectName(u"pageMap")

        self.layoutMap.addWidget(self.pageMap)

        self.splitMain.addWidget(self.groupMap)

        self.layoutRoot.addWidget(self.splitMain)

        PreviewWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(PreviewWindow)
        self.statusbar.setObjectName(u"statusbar")
        PreviewWindow.setStatusBar(self.statusbar)

        self.retranslateUi(PreviewWindow)

        QMetaObject.connectSlotsByName(PreviewWindow)
    # setupUi

    def retranslateUi(self, PreviewWindow):
        PreviewWindow.setWindowTitle(QCoreApplication.translate("PreviewWindow", u"Step 6 - Preview", None))
        self.groupGeo.setTitle(QCoreApplication.translate("PreviewWindow", u"GeoJSON", None))
        self.buttonBrowseGeo.setText(QCoreApplication.translate("PreviewWindow", u"\u2026", None))
        self.groupMapping.setTitle(QCoreApplication.translate("PreviewWindow", u"Mapping", None))
        self.label.setText(QCoreApplication.translate("PreviewWindow", u"Geo-ID Column", None))
        self.label1.setText(QCoreApplication.translate("PreviewWindow", u"Stats-ID Column", None))
        self.label2.setText(QCoreApplication.translate("PreviewWindow", u"Display Value", None))
        self.buttonRender.setText(QCoreApplication.translate("PreviewWindow", u"Show Map", None))
        self.groupMap.setTitle(QCoreApplication.translate("PreviewWindow", u"Map", None))
    # retranslateUi

