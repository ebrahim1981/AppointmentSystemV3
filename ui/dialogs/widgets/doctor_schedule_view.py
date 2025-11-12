# AppointmentSystem/ui/dialogs/widgets/doctor_schedule_view.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import logging
from datetime import datetime, timedelta

class DoctorScheduleView(QWidget):
    """عرض جدول الطبيب اليومي بشكل جدول منظم"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedule_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة عرض الجدول"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # عنوان الجدول
        self.title_label = QLabel("جدول الطبيب - اليوم")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #2C3E50;
                padding: 10px;
                background-color: #3498DB;
                color: white;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # إنشاء الجدول
        self.schedule_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.schedule_table)
        
        # معلومات سريعة
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #ECF0F1;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
                color: #2C3E50;
            }
        """)
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
    def setup_table(self):
        """إعداد الجدول"""
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels([
            "🕒 الوقت", 
            "👤 المريض", 
            "📞 الهاتف", 
            "📊 الحالة"
        ])
        
        # تنسيق الرأس
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # الوقت
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # المريض
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # الهاتف
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # الحالة
        
        # تنسيق الجدول
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #BDC3C7;
                background-color: white;
                alternate-background-color: #F8F9FA;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QTableWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setSortingEnabled(False)
        
    def display_schedule(self, schedule_data, date=None):
        """عرض جدول الطبيب"""
        try:
            self.schedule_data = schedule_data
            appointments = schedule_data.get('appointments', [])
            
            # تحديث العنوان
            if date:
                display_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
                self.title_label.setText(f"جدول الطبيب - {display_date}")
            
            # تحديث الجدول
            self.update_table(appointments)
            
            # تحديث الإحصائيات
            self.update_stats(appointments)
            
            logging.info(f"✅ تم عرض جدول الطبيب ({len(appointments)} موعد)")
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض الجدول: {e}")
            
    def update_table(self, appointments):
        """تحديث بيانات الجدول"""
        self.schedule_table.setRowCount(len(appointments))
        
        for row, appointment in enumerate(appointments):
            # الوقت
            time_item = QTableWidgetItem(appointment.get('appointment_time', ''))
            time_item.setTextAlignment(Qt.AlignCenter)
            
            # المريض
            patient_item = QTableWidgetItem(appointment.get('patient_name', 'غير معروف'))
            
            # الهاتف
            phone = appointment.get('patient_phone', '')
            country_code = appointment.get('patient_country_code', '+966')
            formatted_phone = f"{country_code} {phone}" if phone else "غير معروف"
            phone_item = QTableWidgetItem(formatted_phone)
            phone_item.setTextAlignment(Qt.AlignCenter)
            
            # الحالة مع التلوين
            status = appointment.get('status', 'مجدول')
            status_item = QTableWidgetItem(status)
            self.color_status_item(status_item, status)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # إضافة العناصر للجدول
            self.schedule_table.setItem(row, 0, time_item)
            self.schedule_table.setItem(row, 1, patient_item)
            self.schedule_table.setItem(row, 2, phone_item)
            self.schedule_table.setItem(row, 3, status_item)
            
    def color_status_item(self, item, status):
        """تلوين خلية الحالة"""
        colors = {
            'مجدول': {'bg': '#E3F2FD', 'text': '#1565C0'},
            'مؤكد': {'bg': '#E8F5E8', 'text': '#2E7D32'},
            'حاضر': {'bg': '#F3E5F5', 'text': '#7B1FA2'},
            'منتهي': {'bg': '#F5F5F5', 'text': '#424242'},
            'ملغى': {'bg': '#FFEBEE', 'text': '#C62828'}
        }
        
        color = colors.get(status, {'bg': '#95A5A6', 'text': '#000000'})
        item.setBackground(QColor(color['bg']))
        item.setForeground(QColor(color['text']))
        item.setFont(QFont("Arial", 10, QFont.Bold))
        
    def update_stats(self, appointments):
        """تحديث الإحصائيات"""
        try:
            total = len(appointments)
            confirmed = sum(1 for a in appointments if a.get('status') == 'مؤكد')
            attended = sum(1 for a in appointments if a.get('status') == 'حاضر')
            cancelled = sum(1 for a in appointments if a.get('status') == 'ملغى')
            
            stats_text = f"""
            📊 إحصائيات اليوم:
            • إجمالي المواعيد: {total}
            • ✅ مؤكدة: {confirmed}
            • 🙋 حاضر: {attended} 
            • ❌ ملغاة: {cancelled}
            • 📈 نسبة الحضور: {(attended/confirmed)*100 if confirmed > 0 else 0:.1f}%
            """
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
            self.stats_label.setText("❌ خطأ في تحميل الإحصائيات")
            
    def clear_schedule(self):
        """مسح الجدول"""
        self.schedule_table.setRowCount(0)
        self.title_label.setText("جدول الطبيب - اليوم")
        self.stats_label.setText("لا توجد بيانات للعرض")

# تصدير الفئة
__all__ = ['DoctorScheduleView']