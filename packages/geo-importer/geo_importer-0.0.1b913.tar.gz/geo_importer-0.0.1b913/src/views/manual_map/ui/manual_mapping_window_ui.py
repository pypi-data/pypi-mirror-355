# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manual_mapping_window.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTabWidget, QTableView,
    QVBoxLayout, QWidget)

class Ui_ManualMappingWindow(object):
    def setupUi(self, ManualMappingWindow):
        if not ManualMappingWindow.objectName():
            ManualMappingWindow.setObjectName(u"ManualMappingWindow")
        ManualMappingWindow.resize(1000, 600)
        self.centralwidget = QWidget(ManualMappingWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutRoot = QVBoxLayout(self.centralwidget)
        self.layoutRoot.setObjectName(u"layoutRoot")
        self.tabManualMapping = QTabWidget(self.centralwidget)
        self.tabManualMapping.setObjectName(u"tabManualMapping")
        self.tabMapped = QWidget()
        self.tabMapped.setObjectName(u"tabMapped")
        self.layoutTabMapped = QVBoxLayout(self.tabMapped)
        self.layoutTabMapped.setObjectName(u"layoutTabMapped")
        self.editSearchMappedManual = QLineEdit(self.tabMapped)
        self.editSearchMappedManual.setObjectName(u"editSearchMappedManual")

        self.layoutTabMapped.addWidget(self.editSearchMappedManual)

        self.tableViewMapped = QTableView(self.tabMapped)
        self.tableViewMapped.setObjectName(u"tableViewMapped")
        self.tableViewMapped.setAlternatingRowColors(True)

        self.layoutTabMapped.addWidget(self.tableViewMapped)

        self.layoutUnmap = QHBoxLayout()
        self.layoutUnmap.setObjectName(u"layoutUnmap")
        self.spacerUnmap = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutUnmap.addItem(self.spacerUnmap)

        self.buttonUnmap = QPushButton(self.tabMapped)
        self.buttonUnmap.setObjectName(u"buttonUnmap")
        self.buttonUnmap.setEnabled(False)

        self.layoutUnmap.addWidget(self.buttonUnmap)


        self.layoutTabMapped.addLayout(self.layoutUnmap)

        self.tabManualMapping.addTab(self.tabMapped, "")
        self.tabUnmapped = QWidget()
        self.tabUnmapped.setObjectName(u"tabUnmapped")
        self.layoutTabUnmapped = QVBoxLayout(self.tabUnmapped)
        self.layoutTabUnmapped.setObjectName(u"layoutTabUnmapped")
        self.layoutTwoTables = QHBoxLayout()
        self.layoutTwoTables.setObjectName(u"layoutTwoTables")
        self.layoutStatsRestBlock = QVBoxLayout()
        self.layoutStatsRestBlock.setObjectName(u"layoutStatsRestBlock")
        self.editSearchStatsRestManual = QLineEdit(self.tabUnmapped)
        self.editSearchStatsRestManual.setObjectName(u"editSearchStatsRestManual")

        self.layoutStatsRestBlock.addWidget(self.editSearchStatsRestManual)

        self.tableViewStatsRest = QTableView(self.tabUnmapped)
        self.tableViewStatsRest.setObjectName(u"tableViewStatsRest")
        self.tableViewStatsRest.setAlternatingRowColors(True)

        self.layoutStatsRestBlock.addWidget(self.tableViewStatsRest)


        self.layoutTwoTables.addLayout(self.layoutStatsRestBlock)

        self.layoutGeoRestBlock = QVBoxLayout()
        self.layoutGeoRestBlock.setObjectName(u"layoutGeoRestBlock")
        self.editSearchGeoRestManual = QLineEdit(self.tabUnmapped)
        self.editSearchGeoRestManual.setObjectName(u"editSearchGeoRestManual")

        self.layoutGeoRestBlock.addWidget(self.editSearchGeoRestManual)

        self.tableViewGeoRest = QTableView(self.tabUnmapped)
        self.tableViewGeoRest.setObjectName(u"tableViewGeoRest")
        self.tableViewGeoRest.setAlternatingRowColors(True)

        self.layoutGeoRestBlock.addWidget(self.tableViewGeoRest)


        self.layoutTwoTables.addLayout(self.layoutGeoRestBlock)


        self.layoutTabUnmapped.addLayout(self.layoutTwoTables)

        self.layoutManual = QHBoxLayout()
        self.layoutManual.setObjectName(u"layoutManual")
        self.spacerManual = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutManual.addItem(self.spacerManual)

        self.buttonManualMap = QPushButton(self.tabUnmapped)
        self.buttonManualMap.setObjectName(u"buttonManualMap")
        self.buttonManualMap.setEnabled(False)

        self.layoutManual.addWidget(self.buttonManualMap)


        self.layoutTabUnmapped.addLayout(self.layoutManual)

        self.tabManualMapping.addTab(self.tabUnmapped, "")

        self.layoutRoot.addWidget(self.tabManualMapping)

        ManualMappingWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ManualMappingWindow)
        self.menubar.setObjectName(u"menubar")
        ManualMappingWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ManualMappingWindow)
        self.statusbar.setObjectName(u"statusbar")
        ManualMappingWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ManualMappingWindow)

        QMetaObject.connectSlotsByName(ManualMappingWindow)
    # setupUi

    def retranslateUi(self, ManualMappingWindow):
        ManualMappingWindow.setWindowTitle(QCoreApplication.translate("ManualMappingWindow", u"Step 5 - Manual Mapping", None))
        self.editSearchMappedManual.setPlaceholderText(QCoreApplication.translate("ManualMappingWindow", u"Search...", None))
        self.buttonUnmap.setText(QCoreApplication.translate("ManualMappingWindow", u"Unmap Selection", None))
        self.tabManualMapping.setTabText(self.tabManualMapping.indexOf(self.tabMapped), QCoreApplication.translate("ManualMappingWindow", u"Mapped", None))
        self.editSearchStatsRestManual.setPlaceholderText(QCoreApplication.translate("ManualMappingWindow", u"Search...", None))
        self.editSearchGeoRestManual.setPlaceholderText(QCoreApplication.translate("ManualMappingWindow", u"Search...", None))
        self.buttonManualMap.setText(QCoreApplication.translate("ManualMappingWindow", u"Map Manually", None))
        self.tabManualMapping.setTabText(self.tabManualMapping.indexOf(self.tabUnmapped), QCoreApplication.translate("ManualMappingWindow", u"Unmapped", None))
    # retranslateUi

