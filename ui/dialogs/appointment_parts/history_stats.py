# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, 
                             QTimeEdit, QPushButton, QLabel, QGroupBox, QFrame, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont
import logging

class HistoryStats(QWidget):
    """السجل والإحصائيات - منفصل ومتكامل"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_patient_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة السجل والإحصائيات"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # سجل المواعيد السابقة
        self.setup_history_section(layout)
        
        # الإحصائيات السريعة
        self.setup_stats_section(layout)
        
    def setup_history_section(self, parent_layout):
        """إعداد قسم السجل"""
        history_group = QGroupBox("📋 سجل المواعيد السابقة")
        history_group.setStyleSheet(self.get_group_style())
        history_layout = QVBoxLayout(history_group)
        
        self.history_label = QLabel("سيظهر هنا سجل المواعيد السابقة للمريض...")
        self.history_label.setAlignment(Qt.AlignCenter)
        self.history_label.setStyleSheet("""
            QLabel {
                padding: 30px 20px;
                background-color: #F8F9FA;
                border: 1px dashed #BDC3C7;
                border-radius: 5px;
                color: #7F8C8D;
                font-size: 12px;
            }
        """)
        history_layout.addWidget(self.history_label)
        
        parent_layout.addWidget(history_group)
        
    def setup_stats_section(self, parent_layout):
        """إعداد قسم الإحصائيات"""
        stats_group = QGroupBox("📊 إحصائيات سريعة")
        stats_group.setStyleSheet(self.get_group_style())
        stats_layout = QGridLayout(stats_group)
        
        # عناوين الإحصائيات
        self.stats_titles = [
            ("🟡 المواعيد المجدولة", "scheduled"),
            ("🟢 المواعيد المؤكدة", "confirmed"), 
            ("🔵 المواعيد الحاضرة", "attended"),
            ("🟣 المواعيد المنتهية", "completed")
        ]
        
        self.stats_labels = {}
        
        for i, (title, key) in enumerate(self.stats_titles):
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 11px; color: #2C3E50;")
            
            value_label = QLabel("0")
            value_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 13px;
                    color: #2C3E50;
                    padding: 4px 8px;
                    background-color: #ECF0F1;
                    border-radius: 3px;
                    min-width: 40px;
                    text-align: center;
                }
            """)
            
            self.stats_labels[key] = value_label
            
            stats_layout.addWidget(title_label, i//2, (i%2)*2)
            stats_layout.addWidget(value_label, i//2, (i%2)*2+1)
        
        parent_layout.addWidget(stats_group)
        
    def set_patient_id(self, patient_id):
        """تعيين معرف المريض وتحديث البيانات"""
        self.current_patient_id = patient_id
        if patient_id:
            self.load_patient_history(patient_id)
            self.load_patient_stats(patient_id)
        else:
            self.clear_data()
    
    def load_patient_history(self, patient_id):
        """تحميل سجل المريض"""
        try:
            if self.db_manager:
                appointments = self.db_manager.get_patient_appointments(patient_id)
                if appointments:
                    self.display_appointments_history(appointments)
                else:
                    self.history_label.setText("لا توجد مواعيد سابقة لهذا المريض")
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل سجل المريض: {e}")
            self.history_label.setText("❌ خطأ في تحميل السجل")
    
    def load_patient_stats(self, patient_id):
        """تحميل إحصائيات المريض"""
        try:
            if self.db_manager:
                stats = self.db_manager.get_patient_appointment_stats(patient_id)
                self.update_stats_display(stats)
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الإحصائيات: {e}")
            self.update_stats_display({})
    
    def display_appointments_history(self, appointments):
        """عرض سجل المواعيد"""
        try:
            # تبسيط العرض للنموذج الأولي
            if appointments:
                latest = appointments[0]  # أحدث موعد
                history_text = f"""
                📅 آخر موعد: {latest.get('appointment_date', '--')}
                ⏰ الوقت: {latest.get('appointment_time', '--')}  
                👨‍⚕️ الطبيب: {latest.get('doctor_name', '--')}
                📊 الحالة: {latest.get('status', '--')}
                
                📋 إجمالي المواعيد: {len(appointments)}
                """
                self.history_label.setText(history_text)
            else:
                self.history_label.setText("لا توجد مواعيد سابقة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في عرض السجل: {e}")
    
    def update_stats_display(self, stats):
        """تحديث عرض الإحصائيات"""
        try:
            # القيم الافتراضية
            default_stats = {
                'scheduled': 0,
                'confirmed': 0, 
                'attended': 0,
                'completed': 0
            }
            
            # دمج الإحصائيات
            merged_stats = {**default_stats, **stats}
            
            # تحديث التسميات
            for key, label in self.stats_labels.items():
                label.setText(str(merged_stats.get(key, 0)))
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    def clear_data(self):
        """مسح البيانات"""
        self.history_label.setText("سيظهر هنا سجل المواعيد السابقة للمريض...")
        for label in self.stats_labels.values():
            label.setText("0")
    
    def get_group_style(self):
        """نمط المجموعات"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2C3E50;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px 0 6px;
                background-color: #3498DB;
                color: white;
                border-radius: 3px;
            }
        """