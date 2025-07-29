# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'upload.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QProgressBar,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_UploadWindow(object):
    def setupUi(self, UploadWindow):
        if not UploadWindow.objectName():
            UploadWindow.setObjectName(u"UploadWindow")
        self.centralwidget = QWidget(UploadWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutRoot = QVBoxLayout(self.centralwidget)
        self.layoutRoot.setObjectName(u"layoutRoot")
        self.labelTitle = QLabel(self.centralwidget)
        self.labelTitle.setObjectName(u"labelTitle")
        self.labelTitle.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.labelTitle.setFont(font)
        self.labelTitle.setMargin(8)

        self.layoutRoot.addWidget(self.labelTitle)

        self.groupBoxFileType = QGroupBox(self.centralwidget)
        self.groupBoxFileType.setObjectName(u"groupBoxFileType")
        self.layoutFileType = QHBoxLayout(self.groupBoxFileType)
        self.layoutFileType.setObjectName(u"layoutFileType")
        self.radioExcel = QRadioButton(self.groupBoxFileType)
        self.radioExcel.setObjectName(u"radioExcel")
        self.radioExcel.setChecked(True)

        self.layoutFileType.addWidget(self.radioExcel)

        self.radioCSV = QRadioButton(self.groupBoxFileType)
        self.radioCSV.setObjectName(u"radioCSV")
        self.radioCSV.setEnabled(True)

        self.layoutFileType.addWidget(self.radioCSV)

        self.radioPDF = QRadioButton(self.groupBoxFileType)
        self.radioPDF.setObjectName(u"radioPDF")
        self.radioPDF.setEnabled(True)

        self.layoutFileType.addWidget(self.radioPDF)


        self.layoutRoot.addWidget(self.groupBoxFileType)

        self.groupBoxBrowse = QGroupBox(self.centralwidget)
        self.groupBoxBrowse.setObjectName(u"groupBoxBrowse")
        self.layoutBrowse = QHBoxLayout(self.groupBoxBrowse)
        self.layoutBrowse.setObjectName(u"layoutBrowse")
        self.lineEditFilePath = QLineEdit(self.groupBoxBrowse)
        self.lineEditFilePath.setObjectName(u"lineEditFilePath")
        self.lineEditFilePath.setReadOnly(True)

        self.layoutBrowse.addWidget(self.lineEditFilePath)

        self.buttonBrowse = QPushButton(self.groupBoxBrowse)
        self.buttonBrowse.setObjectName(u"buttonBrowse")

        self.layoutBrowse.addWidget(self.buttonBrowse)


        self.layoutRoot.addWidget(self.groupBoxBrowse)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layoutRoot.addItem(self.verticalSpacer)

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setTextVisible(True)

        self.layoutRoot.addWidget(self.progressBar)

        UploadWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(UploadWindow)
        self.menubar.setObjectName(u"menubar")
        UploadWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(UploadWindow)
        self.statusbar.setObjectName(u"statusbar")
        UploadWindow.setStatusBar(self.statusbar)

        self.retranslateUi(UploadWindow)

        QMetaObject.connectSlotsByName(UploadWindow)
    # setupUi

    def retranslateUi(self, UploadWindow):
        UploadWindow.setWindowTitle(QCoreApplication.translate("UploadWindow", u"Step 1: Upload", None))
        self.labelTitle.setText(QCoreApplication.translate("UploadWindow", u"Step 1: Select File", None))
        self.groupBoxFileType.setTitle(QCoreApplication.translate("UploadWindow", u"Select File Type", None))
        self.radioExcel.setText(QCoreApplication.translate("UploadWindow", u"Excel (.xlsx/.xls)", None))
        self.radioCSV.setText(QCoreApplication.translate("UploadWindow", u"CSV (.csv)", None))
        self.radioPDF.setText(QCoreApplication.translate("UploadWindow", u"PDF (.pdf)", None))
        self.groupBoxBrowse.setTitle(QCoreApplication.translate("UploadWindow", u"Select File", None))
        self.lineEditFilePath.setPlaceholderText(QCoreApplication.translate("UploadWindow", u"File path...", None))
        self.buttonBrowse.setText(QCoreApplication.translate("UploadWindow", u"Browse...", None))
    # retranslateUi

