# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dataprep_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QStatusBar,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DataPrepWindow(object):
    def setupUi(self, DataPrepWindow):
        if not DataPrepWindow.objectName():
            DataPrepWindow.setObjectName(u"DataPrepWindow")
        self.centralwidget = QWidget(DataPrepWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.hLayMain = QHBoxLayout(self.centralwidget)
        self.hLayMain.setObjectName(u"hLayMain")
        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setObjectName(u"tableWidget")

        self.hLayMain.addWidget(self.tableWidget)

        self.controlsWidget = QWidget(self.centralwidget)
        self.controlsWidget.setObjectName(u"controlsWidget")
        self.controlsWidget.setMaximumWidth(200)
        self.vLayControls = QVBoxLayout(self.controlsWidget)
        self.vLayControls.setObjectName(u"vLayControls")
        self.vLayControls.setContentsMargins(0, 0, 0, 0)
        self.groupRows = QGroupBox(self.controlsWidget)
        self.groupRows.setObjectName(u"groupRows")
        self.vLayRows = QVBoxLayout(self.groupRows)
        self.vLayRows.setObjectName(u"vLayRows")
        self.hLayEveryNthRow = QHBoxLayout()
        self.hLayEveryNthRow.setObjectName(u"hLayEveryNthRow")
        self.labelEveryNthRow = QLabel(self.groupRows)
        self.labelEveryNthRow.setObjectName(u"labelEveryNthRow")

        self.hLayEveryNthRow.addWidget(self.labelEveryNthRow)

        self.spinRowN = QSpinBox(self.groupRows)
        self.spinRowN.setObjectName(u"spinRowN")
        self.spinRowN.setMinimum(0)
        self.spinRowN.setValue(0)

        self.hLayEveryNthRow.addWidget(self.spinRowN)


        self.vLayRows.addLayout(self.hLayEveryNthRow)

        self.hLayShiftRow = QHBoxLayout()
        self.hLayShiftRow.setObjectName(u"hLayShiftRow")
        self.labelShiftRow = QLabel(self.groupRows)
        self.labelShiftRow.setObjectName(u"labelShiftRow")

        self.hLayShiftRow.addWidget(self.labelShiftRow)

        self.spinRowShift = QSpinBox(self.groupRows)
        self.spinRowShift.setObjectName(u"spinRowShift")
        self.spinRowShift.setMinimum(-100)
        self.spinRowShift.setValue(0)

        self.hLayShiftRow.addWidget(self.spinRowShift)


        self.vLayRows.addLayout(self.hLayShiftRow)


        self.vLayControls.addWidget(self.groupRows)

        self.groupCols = QGroupBox(self.controlsWidget)
        self.groupCols.setObjectName(u"groupCols")
        self.vLayCols = QVBoxLayout(self.groupCols)
        self.vLayCols.setObjectName(u"vLayCols")
        self.hLayEveryNthCol = QHBoxLayout()
        self.hLayEveryNthCol.setObjectName(u"hLayEveryNthCol")
        self.labelEveryNthCol = QLabel(self.groupCols)
        self.labelEveryNthCol.setObjectName(u"labelEveryNthCol")

        self.hLayEveryNthCol.addWidget(self.labelEveryNthCol)

        self.spinColN = QSpinBox(self.groupCols)
        self.spinColN.setObjectName(u"spinColN")
        self.spinColN.setMinimum(0)
        self.spinColN.setValue(0)

        self.hLayEveryNthCol.addWidget(self.spinColN)


        self.vLayCols.addLayout(self.hLayEveryNthCol)

        self.hLayShiftCol = QHBoxLayout()
        self.hLayShiftCol.setObjectName(u"hLayShiftCol")
        self.labelShiftCol = QLabel(self.groupCols)
        self.labelShiftCol.setObjectName(u"labelShiftCol")

        self.hLayShiftCol.addWidget(self.labelShiftCol)

        self.spinColShift = QSpinBox(self.groupCols)
        self.spinColShift.setObjectName(u"spinColShift")
        self.spinColShift.setMinimum(-100)
        self.spinColShift.setValue(0)

        self.hLayShiftCol.addWidget(self.spinColShift)


        self.vLayCols.addLayout(self.hLayShiftCol)


        self.vLayControls.addWidget(self.groupCols)

        self.groupMode = QGroupBox(self.controlsWidget)
        self.groupMode.setObjectName(u"groupMode")
        self.vLayMode = QVBoxLayout(self.groupMode)
        self.vLayMode.setObjectName(u"vLayMode")
        self.hLayModeCombo = QHBoxLayout()
        self.hLayModeCombo.setObjectName(u"hLayModeCombo")
        self.labelMode = QLabel(self.groupMode)
        self.labelMode.setObjectName(u"labelMode")

        self.hLayModeCombo.addWidget(self.labelMode)

        self.comboMode = QComboBox(self.groupMode)
        self.comboMode.addItem("")
        self.comboMode.addItem("")
        self.comboMode.setObjectName(u"comboMode")

        self.hLayModeCombo.addWidget(self.comboMode)


        self.vLayMode.addLayout(self.hLayModeCombo)


        self.vLayControls.addWidget(self.groupMode)

        self.hLayResetApply = QHBoxLayout()
        self.hLayResetApply.setObjectName(u"hLayResetApply")
        self.btnReset = QPushButton(self.controlsWidget)
        self.btnReset.setObjectName(u"btnReset")

        self.hLayResetApply.addWidget(self.btnReset)

        self.btnApply = QPushButton(self.controlsWidget)
        self.btnApply.setObjectName(u"btnApply")

        self.hLayResetApply.addWidget(self.btnApply)


        self.vLayControls.addLayout(self.hLayResetApply)

        self.vSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vLayControls.addItem(self.vSpacer)

        self.btnTranspose = QPushButton(self.controlsWidget)
        self.btnTranspose.setObjectName(u"btnTranspose")

        self.vLayControls.addWidget(self.btnTranspose)

        self.btnExportCsv = QPushButton(self.controlsWidget)
        self.btnExportCsv.setObjectName(u"btnExportCsv")

        self.vLayControls.addWidget(self.btnExportCsv)

        self.btnExportExcel = QPushButton(self.controlsWidget)
        self.btnExportExcel.setObjectName(u"btnExportExcel")

        self.vLayControls.addWidget(self.btnExportExcel)

        self.hLayUndoRedo = QHBoxLayout()
        self.hLayUndoRedo.setObjectName(u"hLayUndoRedo")
        self.btnUndo = QPushButton(self.controlsWidget)
        self.btnUndo.setObjectName(u"btnUndo")

        self.hLayUndoRedo.addWidget(self.btnUndo)

        self.btnRedo = QPushButton(self.controlsWidget)
        self.btnRedo.setObjectName(u"btnRedo")

        self.hLayUndoRedo.addWidget(self.btnRedo)


        self.vLayControls.addLayout(self.hLayUndoRedo)


        self.hLayMain.addWidget(self.controlsWidget)

        DataPrepWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(DataPrepWindow)
        self.statusbar.setObjectName(u"statusbar")
        DataPrepWindow.setStatusBar(self.statusbar)

        self.retranslateUi(DataPrepWindow)

        QMetaObject.connectSlotsByName(DataPrepWindow)
    # setupUi

    def retranslateUi(self, DataPrepWindow):
        DataPrepWindow.setWindowTitle(QCoreApplication.translate("DataPrepWindow", u"Data Preparation", None))
        self.groupRows.setTitle(QCoreApplication.translate("DataPrepWindow", u"Rows", None))
        self.labelEveryNthRow.setText(QCoreApplication.translate("DataPrepWindow", u"Every Nth Row:", None))
        self.labelShiftRow.setText(QCoreApplication.translate("DataPrepWindow", u"Shift by:", None))
        self.groupCols.setTitle(QCoreApplication.translate("DataPrepWindow", u"Columns", None))
        self.labelEveryNthCol.setText(QCoreApplication.translate("DataPrepWindow", u"Every Nth Column:", None))
        self.labelShiftCol.setText(QCoreApplication.translate("DataPrepWindow", u"Shift by:", None))
        self.groupMode.setTitle(QCoreApplication.translate("DataPrepWindow", u"Selection Mode", None))
        self.labelMode.setText(QCoreApplication.translate("DataPrepWindow", u"Mode:", None))
        self.comboMode.setItemText(0, QCoreApplication.translate("DataPrepWindow", u"AND", None))
        self.comboMode.setItemText(1, QCoreApplication.translate("DataPrepWindow", u"OR", None))

        self.btnReset.setText(QCoreApplication.translate("DataPrepWindow", u"Reset", None))
        self.btnApply.setText(QCoreApplication.translate("DataPrepWindow", u"Apply", None))
        self.btnTranspose.setText(QCoreApplication.translate("DataPrepWindow", u"Transpose", None))
        self.btnExportCsv.setText(QCoreApplication.translate("DataPrepWindow", u"Export CSV", None))
        self.btnExportExcel.setText(QCoreApplication.translate("DataPrepWindow", u"Export Excel", None))
        self.btnUndo.setText(QCoreApplication.translate("DataPrepWindow", u"Undo", None))
        self.btnRedo.setText(QCoreApplication.translate("DataPrepWindow", u"Redo", None))
    # retranslateUi

