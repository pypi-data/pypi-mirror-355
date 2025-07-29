# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pdf_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QSplitter,
    QStatusBar, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_PDFWindow(object):
    def setupUi(self, PDFWindow):
        if not PDFWindow.objectName():
            PDFWindow.setObjectName(u"PDFWindow")
        PDFWindow.resize(900, 700)
        self.centralwidget = QWidget(PDFWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topLayout = QHBoxLayout()
        self.topLayout.setObjectName(u"topLayout")
        self.labelPage = QLabel(self.centralwidget)
        self.labelPage.setObjectName(u"labelPage")

        self.topLayout.addWidget(self.labelPage)

        self.spinPage = QSpinBox(self.centralwidget)
        self.spinPage.setObjectName(u"spinPage")
        self.spinPage.setMinimum(1)

        self.topLayout.addWidget(self.spinPage)

        self.btnExtract = QPushButton(self.centralwidget)
        self.btnExtract.setObjectName(u"btnExtract")

        self.topLayout.addWidget(self.btnExtract)

        self.spacerHoriz = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.topLayout.addItem(self.spacerHoriz)


        self.verticalLayout.addLayout(self.topLayout)

        self.splitMain = QSplitter(self.centralwidget)
        self.splitMain.setObjectName(u"splitMain")
        self.splitMain.setOrientation(Qt.Horizontal)
        self.groupPdfView = QGroupBox(self.splitMain)
        self.groupPdfView.setObjectName(u"groupPdfView")
        self.layoutPdf = QVBoxLayout(self.groupPdfView)
        self.layoutPdf.setObjectName(u"layoutPdf")
        self.pdfView = QGraphicsView(self.groupPdfView)
        self.pdfView.setObjectName(u"pdfView")

        self.layoutPdf.addWidget(self.pdfView)

        self.splitMain.addWidget(self.groupPdfView)
        self.groupTable = QGroupBox(self.splitMain)
        self.groupTable.setObjectName(u"groupTable")
        self.layoutTable = QVBoxLayout(self.groupTable)
        self.layoutTable.setObjectName(u"layoutTable")
        self.tableWidget = QTableWidget(self.groupTable)
        self.tableWidget.setObjectName(u"tableWidget")

        self.layoutTable.addWidget(self.tableWidget)

        self.splitMain.addWidget(self.groupTable)

        self.verticalLayout.addWidget(self.splitMain)

        PDFWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(PDFWindow)
        self.statusbar.setObjectName(u"statusbar")
        PDFWindow.setStatusBar(self.statusbar)

        self.retranslateUi(PDFWindow)

        QMetaObject.connectSlotsByName(PDFWindow)
    # setupUi

    def retranslateUi(self, PDFWindow):
        PDFWindow.setWindowTitle(QCoreApplication.translate("PDFWindow", u"Extract PDF Table", None))
        self.labelPage.setText(QCoreApplication.translate("PDFWindow", u"Page:", None))
        self.btnExtract.setText(QCoreApplication.translate("PDFWindow", u"Extract Table", None))
        self.groupPdfView.setTitle(QCoreApplication.translate("PDFWindow", u"PDF Viewer", None))
        self.groupTable.setTitle(QCoreApplication.translate("PDFWindow", u"Editable Table", None))
    # retranslateUi

