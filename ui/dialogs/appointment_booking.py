# appointment_booking.py
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLabel, QComboBox, QDateEdit, 
                             QMessageBox, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

class AppointmentBookingDialog(QDialog):
    """نافذة حجز المواعيد المتكاملة مع النظام الدوري"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_doctor_id = None
        self.selected_date = None
        self.selected_time = None
        
        self.setup_ui()
        self.setWindowTitle("نظام حجز المواعيد المتكامل")
        self.setMinimumSize(600, 500)
        
    def setup_ui(self):
        """إعداد واجهة الحجز"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # العنوان
        title = QLabel("📅 نظام حجز المواعيد المتكامل")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2980B9);
                color: white;
                border-radius: 8px;
            }
        """)
        layout.addWidget(title)
        
        # مجموعة بيانات الحجز
        booking_group = QGroupBox("معلومات الحجز")
        booking_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2C3E50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        booking_layout = QFormLayout(booking_group)
        booking_layout.setLabelAlignment(Qt.AlignRight)
        booking_layout.setVerticalSpacing(12)
        
        # اختيار الطبيب
        self.doctor_combo = QComboBox()
        self.doctor_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        self.load_doctors()
        self.doctor_combo.currentIndexChanged.connect(self.on_doctor_changed)
        
        # اختيار التاريخ
        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setMinimumDate(QDate.currentDate())
        self.date_selector.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        self.date_selector.dateChanged.connect(self.on_date_changed)
        
        # اختيار الوقت
        self.time_combo = QComboBox()
        self.time_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        
        booking_layout.addRow("الطبيب:", self.doctor_combo)
        booking_layout.addRow("التاريخ:", self.date_selector)
        booking_layout.addRow("الوقت:", self.time_combo)
        
        layout.addWidget(booking_group)
        
        # معلومات المريض
        patient_group = QGroupBox("معلومات المريض")
        patient_group.setStyleSheet(booking_group.styleSheet())
        patient_layout = QFormLayout(patient_group)
        patient_layout.setLabelAlignment(Qt.AlignRight)
        patient_layout.setVerticalSpacing(12)
        
        self.patient_name_input = QTextEdit()
        self.patient_name_input.setMaximumHeight(60)
        self.patient_name_input.setPlaceholderText("اسم المريض الكامل...")
        self.patient_name_input.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        
        self.patient_phone_input = QTextEdit()
        self.patient_phone_input.setMaximumHeight(60)
        self.patient_phone_input.setPlaceholderText("رقم هاتف المريض...")
        self.patient_phone_input.setStyleSheet(self.patient_name_input.styleSheet())
        
        patient_layout.addRow("اسم المريض:", self.patient_name_input)
        patient_layout.addRow("رقم الهاتف:", self.patient_phone_input)
        
        layout.addWidget(patient_group)
        
        # معلومات الحجز
        self.booking_info = QLabel("👈 اختر الطبيب والتاريخ والوقت المناسب")
        self.booking_info.setAlignment(Qt.AlignCenter)
        self.booking_info.setStyleSheet("""
            QLabel {
                padding: 20px;
                background-color: #F8F9FA;
                border: 2px dashed #BDC3C7;
                border-radius: 8px;
                color: #7F8C8D;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.booking_info)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        self.book_btn = QPushButton("✅ تأكيد الحجز")
        self.book_btn.clicked.connect(self.confirm_booking)
        self.book_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
                color: #7F8C8D;
            }
        """)
        self.book_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("❌ إلغاء")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.book_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def load_doctors(self):
        """تحميل قائمة الأطباء"""
        try:
            doctors = self.db_manager.get_doctors()
            self.doctor_combo.clear()
            self.doctor_combo.addItem("-- اختر الطبيب --", None)
            
            for doctor in doctors:
                if doctor.get('is_active', True):
                    self.doctor_combo.addItem(
                        f"د. {doctor['name']} - {doctor['specialty']}", 
                        doctor['id']
                    )
                    
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأطباء: {e}")
    
    def on_doctor_changed(self):
        """عند تغيير الطبيب"""
        self.selected_doctor_id = self.doctor_combo.currentData()
        self.update_available_times()
    
    def on_date_changed(self):
        """عند تغيير التاريخ"""
        self.selected_date = self.date_selector.date().toString('yyyy-MM-dd')
        self.update_available_times()
    
    def update_available_times(self):
        """تحديث الأوقات المتاحة"""
        if not self.selected_doctor_id or not self.selected_date:
            self.time_combo.clear()
            self.booking_info.setText("👈 اختر الطبيب والتاريخ أولاً")
            self.book_btn.setEnabled(False)
            return
        
        try:
            # الحصول على الجدول الدوري للتاريخ المحدد
            schedule_data = self.db_manager.get_periodic_schedule(
                self.selected_doctor_id, 
                self.selected_date, 
                self.selected_date
            )
            
            self.time_combo.clear()
            
            if self.selected_date in schedule_data:
                available_slots = [
                    slot for slot in schedule_data[self.selected_date]['slots']
                    if slot['status'] == 'available'
                ]
                
                if available_slots:
                    for slot in available_slots:
                        self.time_combo.addItem(slot['time'], slot['time'])
                    
                    doctor_name = self.doctor_combo.currentText().split(' - ')[0]
                    self.booking_info.setText(
                        f"✅ يوجد {len(available_slots)} موعد متاح\n"
                        f"الطبيب: {doctor_name}\n"
                        f"التاريخ: {self.selected_date}"
                    )
                    self.book_btn.setEnabled(True)
                else:
                    self.booking_info.setText(
                        "❌ لا توجد مواعيد متاحة في هذا التاريخ\n"
                        "يرجى اختيار تاريخ آخر"
                    )
                    self.book_btn.setEnabled(False)
            else:
                self.booking_info.setText(
                    "❌ لا يوجد جدول للطبيب في هذا التاريخ\n"
                    "يرجى التواصل مع الإدارة"
                )
                self.book_btn.setEnabled(False)
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الأوقات المتاحة: {e}")
            self.booking_info.setText("❌ حدث خطأ في تحميل البيانات")
            self.book_btn.setEnabled(False)
    
    def confirm_booking(self):
        """تأكيد الحجز"""
        try:
            if not all([
                self.selected_doctor_id,
                self.selected_date,
                self.time_combo.currentData(),
                self.patient_name_input.toPlainText().strip()
            ]):
                QMessageBox.warning(self, "بيانات ناقصة", "يرجى تعبئة جميع البيانات المطلوبة")
                return
            
            patient_name = self.patient_name_input.toPlainText().strip()
            patient_phone = self.patient_phone_input.toPlainText().strip()
            selected_time = self.time_combo.currentData()
            
            # تأكيد الحجز
            reply = QMessageBox.question(
                self,
                "تأكيد الحجز",
                f"هل تريد تأكيد حجز الموعد التالي؟\n\n"
                f"الطبيب: {self.doctor_combo.currentText()}\n"
                f"التاريخ: {self.selected_date}\n"
                f"الوقت: {selected_time}\n"
                f"المريض: {patient_name}",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # هنا سيتم إضافة الحجز الفعلي في قاعدة البيانات
                # هذا مثال توضيحي - تحتاج إلى تنفيذ الوظيفة الفعلية
                
                success = True  # سيتم استبدالها بالاستدعاء الفعلي
                
                if success:
                    QMessageBox.information(
                        self,
                        "تم الحجز",
                        f"✅ تم حجز الموعد بنجاح\n\n"
                        f"رقم الحجز: #12345\n"
                        f"يرجى الحضور قبل الموعد بـ 15 دقيقة"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "❌ فشل في حجز الموعد")
                    
        except Exception as e:
            logging.error(f"❌ خطأ في تأكيد الحجز: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء الحجز:\n{str(e)}")