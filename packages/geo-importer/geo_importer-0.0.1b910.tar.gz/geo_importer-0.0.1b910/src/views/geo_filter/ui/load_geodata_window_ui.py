# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'load_geodata_window.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGridLayout,
    QGroupBox, QHeaderView, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QStatusBar, QTableView,
    QTextEdit, QVBoxLayout, QWidget)
class Ui_GeoDataWindow(object):
    def setupUi(self, GeoDataWindow):
        if not GeoDataWindow.objectName():
            GeoDataWindow.setObjectName(u"GeoDataWindow")
        self.centralwidget = QWidget(GeoDataWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutRoot = QVBoxLayout(self.centralwidget)
        self.layoutRoot.setObjectName(u"layoutRoot")
        self.groupSelect = QGroupBox(self.centralwidget)
        self.groupSelect.setObjectName(u"groupSelect")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupSelect.sizePolicy().hasHeightForWidth())
        self.groupSelect.setSizePolicy(sizePolicy)
        self.layoutSelect = QGridLayout(self.groupSelect)
        self.layoutSelect.setObjectName(u"layoutSelect")
        self.lblType = QLabel(self.groupSelect)
        self.lblType.setObjectName(u"lblType")

        self.layoutSelect.addWidget(self.lblType, 0, 0, 1, 1)

        self.comboGeoType = QComboBox(self.groupSelect)
        self.comboGeoType.setObjectName(u"comboGeoType")

        self.layoutSelect.addWidget(self.comboGeoType, 0, 1, 1, 1)

        self.lblVersion = QLabel(self.groupSelect)
        self.lblVersion.setObjectName(u"lblVersion")

        self.layoutSelect.addWidget(self.lblVersion, 1, 0, 1, 1)

        self.comboGeoVersion = QComboBox(self.groupSelect)
        self.comboGeoVersion.setObjectName(u"comboGeoVersion")

        self.layoutSelect.addWidget(self.comboGeoVersion, 1, 1, 1, 1)

        self.lblLevel = QLabel(self.groupSelect)
        self.lblLevel.setObjectName(u"lblLevel")

        self.layoutSelect.addWidget(self.lblLevel, 2, 0, 1, 1)

        self.comboGeoLevel = QComboBox(self.groupSelect)
        self.comboGeoLevel.setObjectName(u"comboGeoLevel")

        self.layoutSelect.addWidget(self.comboGeoLevel, 2, 1, 1, 1)

        self.buttonLoadGeo = QPushButton(self.groupSelect)
        self.buttonLoadGeo.setObjectName(u"buttonLoadGeo")

        self.layoutSelect.addWidget(self.buttonLoadGeo, 3, 0, 1, 2)


        self.layoutRoot.addWidget(self.groupSelect)

        self.splitMain = QSplitter(self.centralwidget)
        self.splitMain.setObjectName(u"splitMain")
        self.splitMain.setOrientation(Qt.Horizontal)
        self.widgetLeft = QWidget(self.splitMain)
        self.widgetLeft.setObjectName(u"widgetLeft")
        self.layoutLeft = QVBoxLayout(self.widgetLeft)
        self.layoutLeft.setObjectName(u"layoutLeft")
        self.layoutLeft.setContentsMargins(0, 0, 0, 0)
        self.groupColumns = QGroupBox(self.widgetLeft)
        self.groupColumns.setObjectName(u"groupColumns")
        self.layoutColumns = QVBoxLayout(self.groupColumns)
        self.layoutColumns.setObjectName(u"layoutColumns")
        self.listColumns = QListWidget(self.groupColumns)
        self.listColumns.setObjectName(u"listColumns")
        self.listColumns.setSelectionMode(QAbstractItemView.MultiSelection)

        self.layoutColumns.addWidget(self.listColumns)


        self.layoutLeft.addWidget(self.groupColumns)

        self.groupFilter = QGroupBox(self.widgetLeft)
        self.groupFilter.setObjectName(u"groupFilter")
        self.layoutQB = QVBoxLayout(self.groupFilter)
        self.layoutQB.setObjectName(u"layoutQB")
        self.splitLists = QSplitter(self.groupFilter)
        self.splitLists.setObjectName(u"splitLists")
        self.splitLists.setOrientation(Qt.Horizontal)
        self.listFields = QListWidget(self.splitLists)
        self.listFields.setObjectName(u"listFields")
        self.splitLists.addWidget(self.listFields)
        self.listValues = QListWidget(self.splitLists)
        self.listValues.setObjectName(u"listValues")
        self.splitLists.addWidget(self.listValues)

        self.layoutQB.addWidget(self.splitLists)

        self.layoutOps = QGridLayout()
        self.layoutOps.setObjectName(u"layoutOps")
        self.btnEq = QPushButton(self.groupFilter)
        self.btnEq.setObjectName(u"btnEq")

        self.layoutOps.addWidget(self.btnEq, 0, 0, 1, 1)

        self.btnNe = QPushButton(self.groupFilter)
        self.btnNe.setObjectName(u"btnNe")

        self.layoutOps.addWidget(self.btnNe, 0, 1, 1, 1)

        self.btnLt = QPushButton(self.groupFilter)
        self.btnLt.setObjectName(u"btnLt")

        self.layoutOps.addWidget(self.btnLt, 0, 2, 1, 1)

        self.btnGt = QPushButton(self.groupFilter)
        self.btnGt.setObjectName(u"btnGt")

        self.layoutOps.addWidget(self.btnGt, 0, 3, 1, 1)

        self.btnLe = QPushButton(self.groupFilter)
        self.btnLe.setObjectName(u"btnLe")

        self.layoutOps.addWidget(self.btnLe, 0, 4, 1, 1)

        self.btnGe = QPushButton(self.groupFilter)
        self.btnGe.setObjectName(u"btnGe")

        self.layoutOps.addWidget(self.btnGe, 0, 5, 1, 1)

        self.btnAnd = QPushButton(self.groupFilter)
        self.btnAnd.setObjectName(u"btnAnd")

        self.layoutOps.addWidget(self.btnAnd, 1, 0, 1, 1)

        self.btnOr = QPushButton(self.groupFilter)
        self.btnOr.setObjectName(u"btnOr")

        self.layoutOps.addWidget(self.btnOr, 1, 1, 1, 1)

        self.btnLike = QPushButton(self.groupFilter)
        self.btnLike.setObjectName(u"btnLike")

        self.layoutOps.addWidget(self.btnLike, 1, 2, 1, 1)

        self.btnIn = QPushButton(self.groupFilter)
        self.btnIn.setObjectName(u"btnIn")

        self.layoutOps.addWidget(self.btnIn, 1, 3, 1, 1)

        self.btnNot = QPushButton(self.groupFilter)
        self.btnNot.setObjectName(u"btnNot")

        self.layoutOps.addWidget(self.btnNot, 1, 4, 1, 1)


        self.layoutQB.addLayout(self.layoutOps)

        self.textExpr = QTextEdit(self.groupFilter)
        self.textExpr.setObjectName(u"textExpr")

        self.layoutQB.addWidget(self.textExpr)

        self.layoutRowFilter = QGridLayout()
        self.layoutRowFilter.setObjectName(u"layoutRowFilter")
        self.spacerRow = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutRowFilter.addItem(self.spacerRow, 0, 0, 1, 1)

        self.btnTestExpr = QPushButton(self.groupFilter)
        self.btnTestExpr.setObjectName(u"btnTestExpr")

        self.layoutRowFilter.addWidget(self.btnTestExpr, 0, 1, 1, 1)

        self.btnClearExpr = QPushButton(self.groupFilter)
        self.btnClearExpr.setObjectName(u"btnClearExpr")

        self.layoutRowFilter.addWidget(self.btnClearExpr, 0, 2, 1, 1)


        self.layoutQB.addLayout(self.layoutRowFilter)


        self.layoutLeft.addWidget(self.groupFilter)

        self.splitMain.addWidget(self.widgetLeft)
        self.groupPreview = QGroupBox(self.splitMain)
        self.groupPreview.setObjectName(u"groupPreview")
        self.layoutPreview = QVBoxLayout(self.groupPreview)
        self.layoutPreview.setObjectName(u"layoutPreview")
        self.tablePreview = QTableView(self.groupPreview)
        self.tablePreview.setObjectName(u"tablePreview")

        self.layoutPreview.addWidget(self.tablePreview)

        self.splitMain.addWidget(self.groupPreview)

        self.layoutRoot.addWidget(self.splitMain)

        GeoDataWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(GeoDataWindow)
        self.statusbar.setObjectName(u"statusbar")
        GeoDataWindow.setStatusBar(self.statusbar)

        self.retranslateUi(GeoDataWindow)

        QMetaObject.connectSlotsByName(GeoDataWindow)
    # setupUi

    def retranslateUi(self, GeoDataWindow):
        GeoDataWindow.setWindowTitle(QCoreApplication.translate("GeoDataWindow", u"Step 2b - Geo Filter", None))
        self.groupSelect.setTitle(QCoreApplication.translate("GeoDataWindow", u"Select Geo File", None))
        self.lblType.setText(QCoreApplication.translate("GeoDataWindow", u"Type:", None))
        self.lblVersion.setText(QCoreApplication.translate("GeoDataWindow", u"Version:", None))
        self.lblLevel.setText(QCoreApplication.translate("GeoDataWindow", u"Level:", None))
        self.buttonLoadGeo.setText(QCoreApplication.translate("GeoDataWindow", u"Load", None))
        self.groupColumns.setTitle(QCoreApplication.translate("GeoDataWindow", u"Select Columns", None))
        self.groupFilter.setTitle(QCoreApplication.translate("GeoDataWindow", u"Filter / Query Builder", None))
        self.btnEq.setText(QCoreApplication.translate("GeoDataWindow", u"==", None))
        self.btnNe.setText(QCoreApplication.translate("GeoDataWindow", u"!=", None))
        self.btnLt.setText(QCoreApplication.translate("GeoDataWindow", u"<", None))
        self.btnGt.setText(QCoreApplication.translate("GeoDataWindow", u">", None))
        self.btnLe.setText(QCoreApplication.translate("GeoDataWindow", u"<=", None))
        self.btnGe.setText(QCoreApplication.translate("GeoDataWindow", u">=", None))
        self.btnAnd.setText(QCoreApplication.translate("GeoDataWindow", u"AND", None))
        self.btnOr.setText(QCoreApplication.translate("GeoDataWindow", u"OR", None))
        self.btnLike.setText(QCoreApplication.translate("GeoDataWindow", u"LIKE", None))
        self.btnIn.setText(QCoreApplication.translate("GeoDataWindow", u"IN", None))
        self.btnNot.setText(QCoreApplication.translate("GeoDataWindow", u"NOT", None))
        self.btnTestExpr.setText(QCoreApplication.translate("GeoDataWindow", u"Test / Preview", None))
        self.btnClearExpr.setText(QCoreApplication.translate("GeoDataWindow", u"Clear", None))
        self.groupPreview.setTitle(QCoreApplication.translate("GeoDataWindow", u"Vorschau", None))
    # retranslateUi

