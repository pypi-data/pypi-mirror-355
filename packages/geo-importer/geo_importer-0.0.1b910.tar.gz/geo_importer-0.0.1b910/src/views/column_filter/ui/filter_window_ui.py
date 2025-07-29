# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'filter_window.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QSplitter, QStatusBar,
    QTableView, QTextEdit, QVBoxLayout, QWidget)

class Ui_FilterWindow(object):
    def setupUi(self, FilterWindow):
        if not FilterWindow.objectName():
            FilterWindow.setObjectName(u"FilterWindow")
        self.centralwidget = QWidget(FilterWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.root = QVBoxLayout(self.centralwidget)
        self.root.setObjectName(u"root")
        self.splitMain = QSplitter(self.centralwidget)
        self.splitMain.setObjectName(u"splitMain")
        self.splitMain.setOrientation(Qt.Horizontal)
        self.groupPreview = QGroupBox(self.splitMain)
        self.groupPreview.setObjectName(u"groupPreview")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupPreview.sizePolicy().hasHeightForWidth())
        self.groupPreview.setSizePolicy(sizePolicy)
        self.vlayPreview = QVBoxLayout(self.groupPreview)
        self.vlayPreview.setObjectName(u"vlayPreview")
        self.tablePreview = QTableView(self.groupPreview)
        self.tablePreview.setObjectName(u"tablePreview")

        self.vlayPreview.addWidget(self.tablePreview)

        self.splitMain.addWidget(self.groupPreview)
        self.splitRight = QSplitter(self.splitMain)
        self.splitRight.setObjectName(u"splitRight")
        self.splitRight.setOrientation(Qt.Vertical)
        sizePolicy.setHeightForWidth(self.splitRight.sizePolicy().hasHeightForWidth())
        self.splitRight.setSizePolicy(sizePolicy)
        self.groupBasics = QGroupBox(self.splitRight)
        self.groupBasics.setObjectName(u"groupBasics")
        self.formBasics = QFormLayout(self.groupBasics)
        self.formBasics.setObjectName(u"formBasics")
        self.lblSkip = QLabel(self.groupBasics)
        self.lblSkip.setObjectName(u"lblSkip")

        self.formBasics.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblSkip)

        self.spinSkipRows = QSpinBox(self.groupBasics)
        self.spinSkipRows.setObjectName(u"spinSkipRows")
        self.spinSkipRows.setValue(1)
        self.spinSkipRows.setMinimum(0)

        self.formBasics.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spinSkipRows)

        self.splitRight.addWidget(self.groupBasics)
        self.groupColumns = QGroupBox(self.splitRight)
        self.groupColumns.setObjectName(u"groupColumns")
        self.vlayColumns = QVBoxLayout(self.groupColumns)
        self.vlayColumns.setObjectName(u"vlayColumns")
        self.layColumnButtons = QHBoxLayout()
        self.layColumnButtons.setObjectName(u"layColumnButtons")
        self.btnSelectAll = QPushButton(self.groupColumns)
        self.btnSelectAll.setObjectName(u"btnSelectAll")

        self.layColumnButtons.addWidget(self.btnSelectAll)

        self.btnDeselectAll = QPushButton(self.groupColumns)
        self.btnDeselectAll.setObjectName(u"btnDeselectAll")

        self.layColumnButtons.addWidget(self.btnDeselectAll)


        self.vlayColumns.addLayout(self.layColumnButtons)

        self.listColumns = QListWidget(self.groupColumns)
        self.listColumns.setObjectName(u"listColumns")

        self.vlayColumns.addWidget(self.listColumns)

        self.splitRight.addWidget(self.groupColumns)
        self.groupFilter = QGroupBox(self.splitRight)
        self.groupFilter.setObjectName(u"groupFilter")
        self.vlayFilter = QVBoxLayout(self.groupFilter)
        self.vlayFilter.setObjectName(u"vlayFilter")
        self.splitLists = QSplitter(self.groupFilter)
        self.splitLists.setObjectName(u"splitLists")
        self.splitLists.setOrientation(Qt.Horizontal)
        self.listFields = QListWidget(self.splitLists)
        self.listFields.setObjectName(u"listFields")
        self.splitLists.addWidget(self.listFields)
        self.listValues = QListWidget(self.splitLists)
        self.listValues.setObjectName(u"listValues")
        self.splitLists.addWidget(self.listValues)

        self.vlayFilter.addWidget(self.splitLists)

        self.gridOps = QGridLayout()
        self.gridOps.setObjectName(u"gridOps")
        self.btnEq = QPushButton(self.groupFilter)
        self.btnEq.setObjectName(u"btnEq")

        self.gridOps.addWidget(self.btnEq, 0, 0, 1, 1)

        self.btnNe = QPushButton(self.groupFilter)
        self.btnNe.setObjectName(u"btnNe")

        self.gridOps.addWidget(self.btnNe, 0, 1, 1, 1)

        self.btnLt = QPushButton(self.groupFilter)
        self.btnLt.setObjectName(u"btnLt")

        self.gridOps.addWidget(self.btnLt, 0, 2, 1, 1)

        self.btnGt = QPushButton(self.groupFilter)
        self.btnGt.setObjectName(u"btnGt")

        self.gridOps.addWidget(self.btnGt, 0, 3, 1, 1)

        self.btnAnd = QPushButton(self.groupFilter)
        self.btnAnd.setObjectName(u"btnAnd")

        self.gridOps.addWidget(self.btnAnd, 1, 0, 1, 1)

        self.btnOr = QPushButton(self.groupFilter)
        self.btnOr.setObjectName(u"btnOr")

        self.gridOps.addWidget(self.btnOr, 1, 1, 1, 1)

        self.btnLike = QPushButton(self.groupFilter)
        self.btnLike.setObjectName(u"btnLike")

        self.gridOps.addWidget(self.btnLike, 1, 2, 1, 1)

        self.btnIn = QPushButton(self.groupFilter)
        self.btnIn.setObjectName(u"btnIn")

        self.gridOps.addWidget(self.btnIn, 1, 3, 1, 1)


        self.vlayFilter.addLayout(self.gridOps)

        self.textExpr = QTextEdit(self.groupFilter)
        self.textExpr.setObjectName(u"textExpr")

        self.vlayFilter.addWidget(self.textExpr)

        self.layExprButtons = QHBoxLayout()
        self.layExprButtons.setObjectName(u"layExprButtons")
        self.btnClearExpr = QPushButton(self.groupFilter)
        self.btnClearExpr.setObjectName(u"btnClearExpr")

        self.layExprButtons.addWidget(self.btnClearExpr)

        self.spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layExprButtons.addItem(self.spacerItem)

        self.btnTestExpr = QPushButton(self.groupFilter)
        self.btnTestExpr.setObjectName(u"btnTestExpr")

        self.layExprButtons.addWidget(self.btnTestExpr)


        self.vlayFilter.addLayout(self.layExprButtons)

        self.splitRight.addWidget(self.groupFilter)
        self.splitMain.addWidget(self.splitRight)

        self.root.addWidget(self.splitMain)

        FilterWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(FilterWindow)
        self.statusbar.setObjectName(u"statusbar")
        FilterWindow.setStatusBar(self.statusbar)

        self.retranslateUi(FilterWindow)

        QMetaObject.connectSlotsByName(FilterWindow)
    # setupUi

    def retranslateUi(self, FilterWindow):
        FilterWindow.setWindowTitle(QCoreApplication.translate("FilterWindow", u"Columns & Filter", None))
        self.groupPreview.setTitle(QCoreApplication.translate("FilterWindow", u"Preview", None))
        self.groupBasics.setTitle(QCoreApplication.translate("FilterWindow", u"Data Range", None))
        self.lblSkip.setText(QCoreApplication.translate("FilterWindow", u"Skip Rows:", None))
        self.groupColumns.setTitle(QCoreApplication.translate("FilterWindow", u"Column Selection", None))
        self.btnSelectAll.setText(QCoreApplication.translate("FilterWindow", u"Select All", None))
        self.btnDeselectAll.setText(QCoreApplication.translate("FilterWindow", u"Deselect All", None))
        self.groupFilter.setTitle(QCoreApplication.translate("FilterWindow", u"Filter / Query", None))
        self.btnEq.setText(QCoreApplication.translate("FilterWindow", u"==", None))
        self.btnNe.setText(QCoreApplication.translate("FilterWindow", u"!=", None))
        self.btnLt.setText(QCoreApplication.translate("FilterWindow", u"<", None))
        self.btnGt.setText(QCoreApplication.translate("FilterWindow", u">", None))
        self.btnAnd.setText(QCoreApplication.translate("FilterWindow", u"AND", None))
        self.btnOr.setText(QCoreApplication.translate("FilterWindow", u"OR", None))
        self.btnLike.setText(QCoreApplication.translate("FilterWindow", u"LIKE", None))
        self.btnIn.setText(QCoreApplication.translate("FilterWindow", u"IN", None))
        self.btnClearExpr.setText(QCoreApplication.translate("FilterWindow", u"Clear", None))
        self.btnTestExpr.setText(QCoreApplication.translate("FilterWindow", u"Test / Preview", None))
    # retranslateUi

