# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'excel_sheet_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QSizePolicy, QStatusBar,
    QTableView, QVBoxLayout, QWidget)

class Ui_ExcelSheetWindow(object):
    def setupUi(self, ExcelSheetWindow):
        if not ExcelSheetWindow.objectName():
            ExcelSheetWindow.setObjectName(u"ExcelSheetWindow")
        self.centralwidget = QWidget(ExcelSheetWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.vboxLayout = QVBoxLayout(self.centralwidget)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.lblSheet = QLabel(self.centralwidget)
        self.lblSheet.setObjectName(u"lblSheet")

        self.hboxLayout.addWidget(self.lblSheet)

        self.comboSheet = QComboBox(self.centralwidget)
        self.comboSheet.setObjectName(u"comboSheet")

        self.hboxLayout.addWidget(self.comboSheet)


        self.vboxLayout.addLayout(self.hboxLayout)

        self.tablePreview = QTableView(self.centralwidget)
        self.tablePreview.setObjectName(u"tablePreview")

        self.vboxLayout.addWidget(self.tablePreview)

        ExcelSheetWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(ExcelSheetWindow)
        self.statusbar.setObjectName(u"statusbar")
        ExcelSheetWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ExcelSheetWindow)

        QMetaObject.connectSlotsByName(ExcelSheetWindow)
    # setupUi

    def retranslateUi(self, ExcelSheetWindow):
        ExcelSheetWindow.setWindowTitle(QCoreApplication.translate("ExcelSheetWindow", u"Select Worksheet", None))
        self.lblSheet.setText(QCoreApplication.translate("ExcelSheetWindow", u"Worksheet:", None))
    # retranslateUi

