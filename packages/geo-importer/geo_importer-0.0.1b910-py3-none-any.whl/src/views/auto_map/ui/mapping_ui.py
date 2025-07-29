# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mapping.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMenuBar, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QStackedWidget,
    QStatusBar, QTabWidget, QTableView, QVBoxLayout,
    QWidget)

class Ui_MappingWindow(object):
    def setupUi(self, MappingWindow):
        if not MappingWindow.objectName():
            MappingWindow.setObjectName(u"MappingWindow")
        MappingWindow.resize(1200, 800)
        self.centralwidget = QWidget(MappingWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutRoot = QVBoxLayout(self.centralwidget)
        self.layoutRoot.setObjectName(u"layoutRoot")
        self.labelTitle = QLabel(self.centralwidget)
        self.labelTitle.setObjectName(u"labelTitle")
        self.labelTitle.setAlignment(Qt.AlignCenter)
        self.labelTitle.setMargin(6)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.labelTitle.setFont(font)

        self.layoutRoot.addWidget(self.labelTitle)

        self.splitterConfig = QSplitter(self.centralwidget)
        self.splitterConfig.setObjectName(u"splitterConfig")
        self.splitterConfig.setOrientation(Qt.Horizontal)
        self.groupMatchers = QGroupBox(self.splitterConfig)
        self.groupMatchers.setObjectName(u"groupMatchers")
        self.layoutMatchers = QVBoxLayout(self.groupMatchers)
        self.layoutMatchers.setObjectName(u"layoutMatchers")
        self.listMatchers = QListWidget(self.groupMatchers)
        self.listMatchers.setObjectName(u"listMatchers")

        self.layoutMatchers.addWidget(self.listMatchers)

        self.buttonAddMatcher = QPushButton(self.groupMatchers)
        self.buttonAddMatcher.setObjectName(u"buttonAddMatcher")

        self.layoutMatchers.addWidget(self.buttonAddMatcher)

        self.splitterConfig.addWidget(self.groupMatchers)
        self.groupSettings = QGroupBox(self.splitterConfig)
        self.groupSettings.setObjectName(u"groupSettings")
        self.layoutSettings = QVBoxLayout(self.groupSettings)
        self.layoutSettings.setObjectName(u"layoutSettings")
        self.stackMatcherSettings = QStackedWidget(self.groupSettings)
        self.stackMatcherSettings.setObjectName(u"stackMatcherSettings")

        self.layoutSettings.addWidget(self.stackMatcherSettings)

        self.splitterConfig.addWidget(self.groupSettings)

        self.layoutRoot.addWidget(self.splitterConfig)

        self.layoutStatsMap = QHBoxLayout()
        self.layoutStatsMap.setObjectName(u"layoutStatsMap")
        self.labelTotal = QLabel(self.centralwidget)
        self.labelTotal.setObjectName(u"labelTotal")

        self.layoutStatsMap.addWidget(self.labelTotal)

        self.labelMatched = QLabel(self.centralwidget)
        self.labelMatched.setObjectName(u"labelMatched")

        self.layoutStatsMap.addWidget(self.labelMatched)

        self.labelProgress = QLabel(self.centralwidget)
        self.labelProgress.setObjectName(u"labelProgress")

        self.layoutStatsMap.addWidget(self.labelProgress)

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setMaximum(100)

        self.layoutStatsMap.addWidget(self.progressBar)

        self.spacerStats = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutStatsMap.addItem(self.spacerStats)

        self.buttonRunPipeline = QPushButton(self.centralwidget)
        self.buttonRunPipeline.setObjectName(u"buttonRunPipeline")
        self.buttonRunPipeline.setEnabled(False)

        self.layoutStatsMap.addWidget(self.buttonRunPipeline)


        self.layoutRoot.addLayout(self.layoutStatsMap)

        self.groupTabResults = QGroupBox(self.centralwidget)
        self.groupTabResults.setObjectName(u"groupTabResults")
        self.layoutTabs = QVBoxLayout(self.groupTabResults)
        self.layoutTabs.setObjectName(u"layoutTabs")
        self.tabResults = QTabWidget(self.groupTabResults)
        self.tabResults.setObjectName(u"tabResults")
        self.tabMapped = QWidget()
        self.tabMapped.setObjectName(u"tabMapped")
        self.layoutTabMapped = QVBoxLayout(self.tabMapped)
        self.layoutTabMapped.setObjectName(u"layoutTabMapped")
        self.editSearchMapped = QLineEdit(self.tabMapped)
        self.editSearchMapped.setObjectName(u"editSearchMapped")

        self.layoutTabMapped.addWidget(self.editSearchMapped)

        self.tableViewMapped = QTableView(self.tabMapped)
        self.tableViewMapped.setObjectName(u"tableViewMapped")
        self.tableViewMapped.setAlternatingRowColors(True)

        self.layoutTabMapped.addWidget(self.tableViewMapped)

        self.layoutUnmap = QHBoxLayout()
        self.layoutUnmap.setObjectName(u"layoutUnmap")
        self.spacerUnmap = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutUnmap.addItem(self.spacerUnmap)


        self.layoutTabMapped.addLayout(self.layoutUnmap)

        self.tabResults.addTab(self.tabMapped, "")
        self.tabUnmapped = QWidget()
        self.tabUnmapped.setObjectName(u"tabUnmapped")
        self.layoutTabUnmapped = QVBoxLayout(self.tabUnmapped)
        self.layoutTabUnmapped.setObjectName(u"layoutTabUnmapped")
        self.layoutTwoTables = QHBoxLayout()
        self.layoutTwoTables.setObjectName(u"layoutTwoTables")
        self.groupStatsRest = QGroupBox(self.tabUnmapped)
        self.groupStatsRest.setObjectName(u"groupStatsRest")
        self.layoutStatsRest = QVBoxLayout(self.groupStatsRest)
        self.layoutStatsRest.setObjectName(u"layoutStatsRest")
        self.editSearchStatsRest = QLineEdit(self.groupStatsRest)
        self.editSearchStatsRest.setObjectName(u"editSearchStatsRest")

        self.layoutStatsRest.addWidget(self.editSearchStatsRest)

        self.tableViewStatsRest = QTableView(self.groupStatsRest)
        self.tableViewStatsRest.setObjectName(u"tableViewStatsRest")
        self.tableViewStatsRest.setAlternatingRowColors(True)

        self.layoutStatsRest.addWidget(self.tableViewStatsRest)


        self.layoutTwoTables.addWidget(self.groupStatsRest)

        self.groupGeoRest = QGroupBox(self.tabUnmapped)
        self.groupGeoRest.setObjectName(u"groupGeoRest")
        self.layoutGeoRest = QVBoxLayout(self.groupGeoRest)
        self.layoutGeoRest.setObjectName(u"layoutGeoRest")
        self.editSearchGeoRest = QLineEdit(self.groupGeoRest)
        self.editSearchGeoRest.setObjectName(u"editSearchGeoRest")

        self.layoutGeoRest.addWidget(self.editSearchGeoRest)

        self.tableViewGeoRest = QTableView(self.groupGeoRest)
        self.tableViewGeoRest.setObjectName(u"tableViewGeoRest")
        self.tableViewGeoRest.setAlternatingRowColors(True)

        self.layoutGeoRest.addWidget(self.tableViewGeoRest)


        self.layoutTwoTables.addWidget(self.groupGeoRest)


        self.layoutTabUnmapped.addLayout(self.layoutTwoTables)

        self.layoutManual = QHBoxLayout()
        self.layoutManual.setObjectName(u"layoutManual")
        self.spacerManual = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutManual.addItem(self.spacerManual)


        self.layoutTabUnmapped.addLayout(self.layoutManual)

        self.tabResults.addTab(self.tabUnmapped, "")
        self.tabGeoAll = QWidget()
        self.tabGeoAll.setObjectName(u"tabGeoAll")
        self.layoutTabGeoAll = QVBoxLayout(self.tabGeoAll)
        self.layoutTabGeoAll.setObjectName(u"layoutTabGeoAll")
        self.editSearchGeoAll = QLineEdit(self.tabGeoAll)
        self.editSearchGeoAll.setObjectName(u"editSearchGeoAll")

        self.layoutTabGeoAll.addWidget(self.editSearchGeoAll)

        self.tableViewGeoAll = QTableView(self.tabGeoAll)
        self.tableViewGeoAll.setObjectName(u"tableViewGeoAll")
        self.tableViewGeoAll.setAlternatingRowColors(True)

        self.layoutTabGeoAll.addWidget(self.tableViewGeoAll)

        self.tabResults.addTab(self.tabGeoAll, "")
        self.tabStatsAll = QWidget()
        self.tabStatsAll.setObjectName(u"tabStatsAll")
        self.layoutTabStatsAll = QVBoxLayout(self.tabStatsAll)
        self.layoutTabStatsAll.setObjectName(u"layoutTabStatsAll")
        self.editSearchStatsAll = QLineEdit(self.tabStatsAll)
        self.editSearchStatsAll.setObjectName(u"editSearchStatsAll")

        self.layoutTabStatsAll.addWidget(self.editSearchStatsAll)

        self.tableViewStatsAll = QTableView(self.tabStatsAll)
        self.tableViewStatsAll.setObjectName(u"tableViewStatsAll")
        self.tableViewStatsAll.setAlternatingRowColors(True)

        self.layoutTabStatsAll.addWidget(self.tableViewStatsAll)

        self.tabResults.addTab(self.tabStatsAll, "")

        self.layoutTabs.addWidget(self.tabResults)


        self.layoutRoot.addWidget(self.groupTabResults)

        MappingWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MappingWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 22))
        MappingWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MappingWindow)
        self.statusbar.setObjectName(u"statusbar")
        MappingWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MappingWindow)

        QMetaObject.connectSlotsByName(MappingWindow)
    # setupUi

    def retranslateUi(self, MappingWindow):
        MappingWindow.setWindowTitle(QCoreApplication.translate("MappingWindow", u"Step 3 - Geodata Mapping", None))
        self.labelTitle.setText(QCoreApplication.translate("MappingWindow", u"Step 3 - Geodata Mapping", None))
        self.groupMatchers.setTitle(QCoreApplication.translate("MappingWindow", u"Matcher", None))
        self.buttonAddMatcher.setText(QCoreApplication.translate("MappingWindow", u"\uff0b Add Matcher", None))
        self.groupSettings.setTitle(QCoreApplication.translate("MappingWindow", u"Matcher Settings", None))
        self.labelTotal.setText(QCoreApplication.translate("MappingWindow", u"Total Rows: 0", None))
        self.labelMatched.setText(QCoreApplication.translate("MappingWindow", u"Mapped: 0", None))
        self.labelProgress.setText("")
        self.buttonRunPipeline.setText(QCoreApplication.translate("MappingWindow", u"Start Mapping", None))
        self.groupTabResults.setTitle("")
        self.editSearchMapped.setPlaceholderText(QCoreApplication.translate("MappingWindow", u"Search...", None))
        self.tabResults.setTabText(self.tabResults.indexOf(self.tabMapped), QCoreApplication.translate("MappingWindow", u"Mapped", None))
        self.groupStatsRest.setTitle(QCoreApplication.translate("MappingWindow", u"Statistics Remaining", None))
        self.editSearchStatsRest.setPlaceholderText(QCoreApplication.translate("MappingWindow", u"Search...", None))
        self.groupGeoRest.setTitle(QCoreApplication.translate("MappingWindow", u"Geo Remaining", None))
        self.editSearchGeoRest.setPlaceholderText(QCoreApplication.translate("MappingWindow", u"Search...", None))
        self.tabResults.setTabText(self.tabResults.indexOf(self.tabUnmapped), QCoreApplication.translate("MappingWindow", u"Unmapped", None))
        self.editSearchGeoAll.setPlaceholderText(QCoreApplication.translate("MappingWindow", u"Geo suchen\u2026", None))
        self.tabResults.setTabText(self.tabResults.indexOf(self.tabGeoAll), QCoreApplication.translate("MappingWindow", u"Geo-Daten", None))
        self.editSearchStatsAll.setPlaceholderText(QCoreApplication.translate("MappingWindow", u"Statistics suchen\u2026", None))
        self.tabResults.setTabText(self.tabResults.indexOf(self.tabStatsAll), QCoreApplication.translate("MappingWindow", u"Statistics", None))
    # retranslateUi

