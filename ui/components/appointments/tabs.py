# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QLabel, QGroupBox, QFrame,
                             QTabWidget, QProgressBar, QCheckBox, QTextEdit, 
                             QSpinBox, QTimeEdit, QGridLayout, QDateEdit)
from PyQt5.QtCore import Qt, QDate, QTimer, QDateTime
from PyQt5.QtGui import QFont, QColor
import logging
from datetime import datetime
import os
import sys

class TabManager:
    """مدير التبويبات الثلاثة"""
    
    def __init__(self):
        pass
    
    def setup_bulk_messaging_tab(self, parent):
        """إعداد تبويب الإرسال الجماعي"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # عنوان التبويب
            title = QLabel("📤 الإرسال الجماعي للرسائل")
            title.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2C3E50;
                    padding: 10px;
                    background-color: #F8F9FA;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title)
            
            # إعدادات الإرسال الجماعي
            bulk_settings_group = QGroupBox("⚙️ إعدادات الإرسال الجماعي")
            bulk_settings_layout = QGridLayout(bulk_settings_group)
            
            # اختيار نوع الرسالة
            bulk_settings_layout.addWidget(QLabel("نوع الرسالة:"), 0, 0)
            parent.bulk_message_type = QComboBox()
            parent.bulk_message_type.addItems([
                "ترحيب - إشعار بالموعد الجديد",
                "تذكير - قبل 24 ساعة", 
                "تذكير - قبل ساعتين",
                "متابعة - بعد انتهاء الموعد",
                "مخصص - رسالة مخصصة"
            ])
            bulk_settings_layout.addWidget(parent.bulk_message_type, 0, 1)
            
            # وقت الإرسال
            bulk_settings_layout.addWidget(QLabel("وقت الإرسال:"), 1, 0)
            parent.bulk_send_time = QTimeEdit()
            parent.bulk_send_time.setTime(datetime.now().time())
            bulk_settings_layout.addWidget(parent.bulk_send_time, 1, 1)
            
            # تأخير بين الرسائل
            bulk_settings_layout.addWidget(QLabel("التأخير بين الرسائل:"), 2, 0)
            parent.bulk_delay = QSpinBox()
            parent.bulk_delay.setRange(1, 60)
            parent.bulk_delay.setSuffix(" ثانية")
            parent.bulk_delay.setValue(5)
            bulk_settings_layout.addWidget(parent.bulk_delay, 2, 1)
            
            layout.addWidget(bulk_settings_group)
            
            # معاينة الرسالة
            preview_group = QGroupBox("👁️ معاينة الرسالة")
            preview_layout = QVBoxLayout(preview_group)
            
            parent.bulk_message_preview = QTextEdit()
            parent.bulk_message_preview.setPlaceholderText("سيظهر هنا معاينة الرسالة...")
            parent.bulk_message_preview.setMaximumHeight(150)
            preview_layout.addWidget(parent.bulk_message_preview)
            
            layout.addWidget(preview_group)
            
            # تقدم الإرسال
            progress_group = QGroupBox("📊 تقدم الإرسال")
            progress_layout = QVBoxLayout(progress_group)
            
            parent.bulk_progress = QProgressBar()
            parent.bulk_progress.setVisible(False)
            progress_layout.addWidget(parent.bulk_progress)
            
            parent.bulk_status = QLabel("جاهز للإرسال...")
            progress_layout.addWidget(parent.bulk_status)
            
            layout.addWidget(progress_group)
            
            # أزرار التحكم
            bulk_buttons_layout = QHBoxLayout()
            
            parent.bulk_send_btn = QPushButton("🚀 بدء الإرسال الجماعي")
            parent.bulk_send_btn.clicked.connect(parent.start_bulk_send)
            bulk_buttons_layout.addWidget(parent.bulk_send_btn)
            
            parent.bulk_stop_btn = QPushButton("⏹️ إيقاف الإرسال")
            parent.bulk_stop_btn.clicked.connect(parent.stop_bulk_send)
            parent.bulk_stop_btn.setEnabled(False)
            bulk_buttons_layout.addWidget(parent.bulk_stop_btn)
            
            bulk_buttons_layout.addStretch()
            layout.addLayout(bulk_buttons_layout)
            
            parent.tabs.addTab(tab, "📤 إرسال جماعي")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد تبويب الإرسال الجماعي: {e}")
    
    def setup_reports_tab(self, parent):
        """إعداد تبويب التقارير والإحصائيات"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # عنوان التبويب
            title = QLabel("📊 التقارير والإحصائيات المتقدمة")
            title.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2C3E50;
                    padding: 10px;
                    background-color: #F8F9FA;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title)
            
            # فلاتر التقارير
            report_filters_layout = QHBoxLayout()
            
            report_filters_layout.addWidget(QLabel("الفترة:"))
            parent.report_period = QComboBox()
            parent.report_period.addItems([
                "اليوم", "أمس", "الأسبوع الحالي", "الشهر الحالي", 
                "الأسبوع الماضي", "الشهر الماضي", "مخصص"
            ])
            parent.report_period.currentTextChanged.connect(parent.on_report_period_changed)
            report_filters_layout.addWidget(parent.report_period)
            
            parent.report_start_date = QDateEdit()
            parent.report_start_date.setDate(QDate.currentDate().addDays(-7))
            parent.report_start_date.setEnabled(False)
            report_filters_layout.addWidget(QLabel("من:"))
            report_filters_layout.addWidget(parent.report_start_date)
            
            parent.report_end_date = QDateEdit()
            parent.report_end_date.setDate(QDate.currentDate())
            parent.report_end_date.setEnabled(False)
            report_filters_layout.addWidget(QLabel("إلى:"))
            report_filters_layout.addWidget(parent.report_end_date)
            
            generate_report_btn = QPushButton("📈 توليد التقرير")
            generate_report_btn.clicked.connect(parent.generate_report)
            report_filters_layout.addWidget(generate_report_btn)
            
            report_filters_layout.addStretch()
            layout.addLayout(report_filters_layout)
            
            # إحصائيات سريعة
            quick_stats_layout = QHBoxLayout()
            
            stats_data = [
                ("المواعيد المجدولة", "0", "#3498DB"),
                ("المواعيد المؤكدة", "0", "#27AE60"),
                ("المواعيد المنتهية", "0", "#95A5A6"),
                ("الرسائل المرسلة", "0", "#9B59B6")
            ]
            
            for title, value, color in stats_data:
                stat_widget = self.create_stat_card(title, value, color)
                quick_stats_layout.addWidget(stat_widget)
            
            layout.addLayout(quick_stats_layout)
            
            # جدول التقارير
            parent.reports_table = QTableWidget()
            parent.reports_table.setColumnCount(6)
            parent.reports_table.setHorizontalHeaderLabels([
                "التاريخ", "عدد المواعيد", "المؤكدة", "الحاضرة", 
                "الملغاة", "نسبة النجاح"
            ])
            layout.addWidget(parent.reports_table)
            
            # أزرار التصدير
            export_layout = QHBoxLayout()
            
            export_excel_btn = QPushButton("📊 تصدير لإكسل")
            export_excel_btn.clicked.connect(parent.export_to_excel)
            export_layout.addWidget(export_excel_btn)
            
            export_pdf_btn = QPushButton("📄 تصدير لPDF")
            export_pdf_btn.clicked.connect(parent.export_to_pdf)
            export_layout.addWidget(export_pdf_btn)
            
            export_layout.addStretch()
            layout.addLayout(export_layout)
            
            parent.tabs.addTab(tab, "📊 تقارير")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد تبويب التقارير: {e}")
    
    def setup_settings_tab(self, parent):
        """إعداد تبويب الإعدادات مع معالجة المتغيرات الناقصة"""
        try:
            from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QHBoxLayout
            
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            title = QLabel("⚙️ الإعدادات المتقدمة")
            title.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #2C3E50;
                    padding: 10px;
                    background-color: #F8F9FA;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title)
            
            # 🔥 التحقق من وجود WHATSAPP_AVAILABLE بشكل آمن
            whatsapp_available = getattr(parent, 'WHATSAPP_AVAILABLE', False)
            whatsapp_settings_available = getattr(parent, 'WHATSAPP_SETTINGS_AVAILABLE', False)
            
            # إعدادات النظام
            system_group = QGroupBox("🖥️ إعدادات النظام")
            system_layout = QGridLayout(system_group)
            
            system_layout.addWidget(QLabel("التحديث التلقائي:"), 0, 0)
            parent.auto_refresh_check = QCheckBox("تفعيل التحديث كل 5 دقائق")
            parent.auto_refresh_check.setChecked(True)
            system_layout.addWidget(parent.auto_refresh_check, 0, 1)
            
            system_layout.addWidget(QLabel("النسخ الاحتياطي:"), 1, 0)
            backup_layout = QHBoxLayout()
            parent.auto_backup_check = QCheckBox("نسخ احتياطي تلقائي يومي")
            parent.auto_backup_check.setChecked(True)
            backup_layout.addWidget(parent.auto_backup_check)
            
            manual_backup_btn = QPushButton("نسخ احتياطي الآن")
            manual_backup_btn.clicked.connect(parent.create_manual_backup)
            backup_layout.addWidget(manual_backup_btn)
            
            system_layout.addLayout(backup_layout, 1, 1)
            
            system_layout.addWidget(QLabel("التذكيرات:"), 2, 0)
            parent.reminders_check = QCheckBox("تفعيل التذكيرات التلقائية")
            parent.reminders_check.setChecked(True)
            system_layout.addWidget(parent.reminders_check, 2, 1)
            
            layout.addWidget(system_group)
            
            # 🔥 إعدادات الواتساب - مع التحقق الآمن
            if whatsapp_available:
                whatsapp_group = QGroupBox("📱 إعدادات الواتساب")
                whatsapp_layout = QVBoxLayout(whatsapp_group)
                
                whatsapp_test_btn = QPushButton("اختبار اتصال الواتساب")
                whatsapp_test_btn.clicked.connect(parent.test_whatsapp_connection)
                whatsapp_layout.addWidget(whatsapp_test_btn)
                
                refresh_status_btn = QPushButton("🔄 تحديث حالة الواتساب")
                refresh_status_btn.clicked.connect(lambda: parent.update_whatsapp_status(force_check=True))
                whatsapp_layout.addWidget(refresh_status_btn)
                
                if whatsapp_settings_available:
                    whatsapp_settings_btn = QPushButton("فتح إعدادات الواتساب")
                    whatsapp_settings_btn.clicked.connect(parent.open_whatsapp_settings)
                    whatsapp_layout.addWidget(whatsapp_settings_btn)
                
                layout.addWidget(whatsapp_group)
            
            # إعدادات التقارير
            reports_group = QGroupBox("📊 إعدادات التقارير")
            reports_layout = QVBoxLayout(reports_group)
            
            parent.auto_report_check = QCheckBox("توليد تقرير يومي تلقائي")
            reports_layout.addWidget(parent.auto_report_check)
            
            report_time_layout = QHBoxLayout()
            report_time_layout.addWidget(QLabel("وقت التقرير اليومي:"))
            parent.report_time = QTimeEdit()
            parent.report_time.setTime(datetime.now().time())
            report_time_layout.addWidget(parent.report_time)
            report_time_layout.addStretch()
            reports_layout.addLayout(report_time_layout)
            
            layout.addWidget(reports_group)
            
            layout.addStretch()
            
            parent.tabs.addTab(tab, "⚙️ إعدادات")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد تبويب الإعدادات: {e}")
    
    def create_stat_card(self, title, value, color):
        """إنشاء بطاقة إحصائية محسنة"""
        try:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #FFFFFF;
                    border-radius: 8px;
                    border: 2px solid {color};
                    padding: 12px;
                    margin: 3px;
                    min-width: 120px;
                }}
            """)
            
            layout = QVBoxLayout(card)
            
            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {color};
                    text-align: center;
                }}
            """)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #2C3E50;
                    font-size: 12px;
                    font-weight: bold;
                    text-align: center;
                }
            """)
            
            layout.addWidget(value_label)
            layout.addWidget(title_label)
            
            return card
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء بطاقة إحصائية: {e}")
            return QFrame()