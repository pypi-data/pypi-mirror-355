# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'export_window.ui'
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_ExportWindow(object):
    def setupUi(self, ExportWindow):
        if not ExportWindow.objectName():
            ExportWindow.setObjectName(u"ExportWindow")
        ExportWindow.resize(800, 800)
        self.verticalLayout = QVBoxLayout(ExportWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_title = QLabel(ExportWindow)
        self.label_title.setObjectName(u"label_title")
        self.label_title.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_title)

        self.group_data = QGroupBox(ExportWindow)
        self.group_data.setObjectName(u"group_data")
        self.layoutCsv = QFormLayout(self.group_data)
        self.layoutCsv.setObjectName(u"layoutCsv")
        self.layoutCsv.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label = QLabel(self.group_data)
        self.label.setObjectName(u"label")

        self.layoutCsv.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.combo_id = QComboBox(self.group_data)
        self.combo_id.setObjectName(u"combo_id")

        self.layoutCsv.setWidget(0, QFormLayout.ItemRole.FieldRole, self.combo_id)

        self.label1 = QLabel(self.group_data)
        self.label1.setObjectName(u"label1")

        self.layoutCsv.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label1)

        self.combo_val = QComboBox(self.group_data)
        self.combo_val.setObjectName(u"combo_val")

        self.layoutCsv.setWidget(1, QFormLayout.ItemRole.FieldRole, self.combo_val)


        self.verticalLayout.addWidget(self.group_data)

        self.group_metadata = QGroupBox(ExportWindow)
        self.group_metadata.setObjectName(u"group_metadata")
        self.formLayout_2 = QFormLayout(self.group_metadata)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label_name = QLabel(self.group_metadata)
        self.label_name.setObjectName(u"label_name")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_name)

        self.edit_name = QLineEdit(self.group_metadata)
        self.edit_name.setObjectName(u"edit_name")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edit_name)

        self.label_description = QLabel(self.group_metadata)
        self.label_description.setObjectName(u"label_description")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_description)

        self.edit_description = QTextEdit(self.group_metadata)
        self.edit_description.setObjectName(u"edit_description")
        self.edit_description.setMaximumSize(QSize(16777215, 100))

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.edit_description)

        self.label_source = QLabel(self.group_metadata)
        self.label_source.setObjectName(u"label_source")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_source)

        self.edit_source = QLineEdit(self.group_metadata)
        self.edit_source.setObjectName(u"edit_source")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.edit_source)

        self.label_year = QLabel(self.group_metadata)
        self.label_year.setObjectName(u"label_year")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_year)

        self.spin_year = QSpinBox(self.group_metadata)
        self.spin_year.setObjectName(u"spin_year")
        self.spin_year.setMinimum(1900)
        self.spin_year.setMaximum(2100)
        self.spin_year.setValue(2024)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.spin_year)

        self.label_type = QLabel(self.group_metadata)
        self.label_type.setObjectName(u"label_type")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_type)

        self.combo_type = QComboBox(self.group_metadata)
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.setObjectName(u"combo_type")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.combo_type)


        self.verticalLayout.addWidget(self.group_metadata)

        self.btn_export = QPushButton(ExportWindow)
        self.btn_export.setObjectName(u"btn_export")

        self.verticalLayout.addWidget(self.btn_export)

        self.label_status = QLabel(ExportWindow)
        self.label_status.setObjectName(u"label_status")
        self.label_status.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_status)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(ExportWindow)

        QMetaObject.connectSlotsByName(ExportWindow)
    # setupUi

    def retranslateUi(self, ExportWindow):
        ExportWindow.setWindowTitle(QCoreApplication.translate("ExportWindow", u"Export Data", None))
        self.label_title.setText(QCoreApplication.translate("ExportWindow", u"Export Data and Metadata", None))
        self.group_data.setTitle(QCoreApplication.translate("ExportWindow", u"CSV columns", None))
        self.label.setText(QCoreApplication.translate("ExportWindow", u"ID column:", None))
        self.label1.setText(QCoreApplication.translate("ExportWindow", u"Value column:", None))
        self.group_metadata.setTitle(QCoreApplication.translate("ExportWindow", u"Metadata", None))
        self.label_name.setText(QCoreApplication.translate("ExportWindow", u"Name:", None))
        self.label_description.setText(QCoreApplication.translate("ExportWindow", u"Description:", None))
        self.label_source.setText(QCoreApplication.translate("ExportWindow", u"Source:", None))
        self.label_year.setText(QCoreApplication.translate("ExportWindow", u"Year:", None))
        self.label_type.setText(QCoreApplication.translate("ExportWindow", u"Type:", None))
        self.combo_type.setItemText(0, QCoreApplication.translate("ExportWindow", u"Indicator", None))
        self.combo_type.setItemText(1, QCoreApplication.translate("ExportWindow", u"Index", None))
        self.combo_type.setItemText(2, QCoreApplication.translate("ExportWindow", u"Other", None))

        self.btn_export.setText(QCoreApplication.translate("ExportWindow", u"Export as ZIP", None))
        self.label_status.setText(QCoreApplication.translate("ExportWindow", u"Ready to export", None))
    # retranslateUi

