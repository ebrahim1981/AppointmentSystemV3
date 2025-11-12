# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QTextEdit, 
                             QPushButton, QMessageBox, QGroupBox, QDateEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QScrollArea, QFrame, QSplitter,
                             QToolBar, QAction, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPalette, QColor

class PatientCard(QWidget):
    """بطاقة المريض الذكية - الواجهة المتكاملة"""
    
    def __init__(self, db_path, clinic_id, patient_id=None, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.clinic_id = clinic_id
        self.patient_id = patient_id
        self.current_patient = None
        self.setup_ui()
        if patient_id:
            self.load_patient_data()
        
    def setup_ui(self):
        """إعداد واجهة بطاقة المريض"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط العنوان والأدوات
        self.setup_header_toolbar(main_layout)
        
        # منطقة البحث السريع
        self.setup_quick_search(main_layout)
        
        # تقسيم المنطقة الرئيسية
        splitter = QSplitter(Qt.Horizontal)
        
        # الجانب الأيسر: المعلومات الأساسية والملخص
        self.setup_left_panel(splitter)
        
        # الجانب الأيمن: الخط الزمني والتفاصيل
        self.setup_right_panel(splitter)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
    def setup_header_toolbar(self, layout):
        """إعداد شريط العنوان والأدوات"""
        header_layout = QHBoxLayout()
        
        # معلومات المريض
        self.patient_header = QLabel("بطاقة المريض - اختر مريضاً")
        self.patient_header.setFont(QFont("Arial", 14, QFont.Bold))
        self.patient_header.setStyleSheet("color: #2C3E50; padding: 10px;")
        header_layout.addWidget(self.patient_header)
        
        header_layout.addStretch()
        
        # أزرار الأدوات
        tools_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("✏️ تعديل البيانات")
        self.edit_btn.clicked.connect(self.edit_patient)
        self.edit_btn.setEnabled(False)
        tools_layout.addWidget(self.edit_btn)
        
        self.new_appointment_btn = QPushButton("📅 موعد جديد")
        self.new_appointment_btn.clicked.connect(self.new_appointment)
        self.new_appointment_btn.setEnabled(False)
        tools_layout.addWidget(self.new_appointment_btn)
        
        self.send_message_btn = QPushButton("📨 إرسال رسالة")
        self.send_message_btn.clicked.connect(self.send_message)
        self.send_message_btn.setEnabled(False)
        tools_layout.addWidget(self.send_message_btn)
        
        header_layout.addLayout(tools_layout)
        layout.addLayout(header_layout)
        
    def setup_quick_search(self, layout):
        """إعداد منطقة البحث السريع"""
        search_group = QGroupBox("الببحث السريع للاستقبال")
        search_layout = QHBoxLayout(search_group)
        
        # البحث بالجوال
        search_layout.addWidget(QLabel("رقم الجوال:"))
        self.phone_search = QLineEdit()
        self.phone_search.setPlaceholderText("أدخل رقم الجوال للبحث...")
        self.phone_search.textChanged.connect(self.quick_search_by_phone)
        search_layout.addWidget(self.phone_search)
        
        # البحث بالاسم
        search_layout.addWidget(QLabel("أو بالاسم:"))
        self.name_search = QLineEdit()
        self.name_search.setPlaceholderText("بحث بالاسم...")
        self.name_search.textChanged.connect(self.quick_search_by_name)
        search_layout.addWidget(self.name_search)
        
        # زر بحث متقدم
        self.advanced_search_btn = QPushButton("🔍 بحث متقدم")
        self.advanced_search_btn.clicked.connect(self.advanced_search)
        search_layout.addWidget(self.advanced_search_btn)
        
        layout.addWidget(search_group)
        
    def setup_left_panel(self, splitter):
        """إعداد اللوحة اليسرى (المعلومات الأساسية)"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # المعلومات الشخصية
        self.setup_personal_info(left_layout)
        
        # الملخص الذكي للأقسام
        self.setup_departments_summary(left_layout)
        
        # الملاحظات السريعة
        self.setup_quick_notes(left_layout)
        
        splitter.addWidget(left_widget)
        
    def setup_right_panel(self, splitter):
        """إعداد اللوحة اليمنى (الخط الزمني)"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # عنوان الخط الزمني
        timeline_title = QLabel("📊 الخط الزمني للزيارات")
        timeline_title.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(timeline_title)
        
        # فلاتر الخط الزمني
        self.setup_timeline_filters(right_layout)
        
        # جدول الزيارات
        self.setup_visits_timeline(right_layout)
        
        splitter.addWidget(right_widget)
        
    def setup_personal_info(self, layout):
        """إعداد قسم المعلومات الشخصية"""
        info_group = QGroupBox("المعلومات الشخصية")
        info_layout = QFormLayout(info_group)
        
        self.info_labels = {}
        personal_fields = [
            ("الاسم الكامل", "name"),
            ("رقم الجوال", "phone"), 
            ("البريد الإلكتروني", "email"),
            ("الجنس", "gender"),
            ("تاريخ الميلاد", "birth_date"),
            ("العمر", "age")
        ]
        
        for label_text, key in personal_fields:
            value_label = QLabel("---")
            value_label.setStyleSheet("padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
            info_layout.addRow(f"{label_text}:", value_label)
            self.info_labels[key] = value_label
            
        layout.addWidget(info_group)
        
    def setup_departments_summary(self, layout):
        """إعداد الملخص الذكي للأقسام"""
        summary_group = QGroupBox("🔄 الملخص الذكي للأقسام")
        summary_layout = QVBoxLayout(summary_group)
        
        self.departments_list = QListWidget()
        summary_layout.addWidget(self.departments_list)
        
        layout.addWidget(summary_group)
        
    def setup_quick_notes(self, layout):
        """إعداد الملاحظات السريعة"""
        notes_group = QGroupBox("ملاحظات سريعة")
        notes_layout = QVBoxLayout(notes_group)
        
        self.quick_notes_input = QTextEdit()
        self.quick_notes_input.setMaximumHeight(100)
        self.quick_notes_input.setPlaceholderText("أضف ملاحظات سريعة هنا...")
        notes_layout.addWidget(self.quick_notes_input)
        
        save_notes_btn = QPushButton("💾 حفظ الملاحظات")
        save_notes_btn.clicked.connect(self.save_quick_notes)
        notes_layout.addWidget(save_notes_btn)
        
        layout.addWidget(notes_group)
        
    def setup_timeline_filters(self, layout):
        """إعداد فلاتر الخط الزمني"""
        filters_layout = QHBoxLayout()
        
        # فلترة بالقسم
        filters_layout.addWidget(QLabel("القسم:"))
        self.department_filter = QComboBox()
        self.department_filter.addItem("الكل")
        filters_layout.addWidget(self.department_filter)
        
        # فلترة بالطبيب
        filters_layout.addWidget(QLabel("الطبيب:"))
        self.doctor_filter = QComboBox()
        self.doctor_filter.addItem("الكل")
        filters_layout.addWidget(self.doctor_filter)
        
        # فلترة بالحالة
        filters_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "مكتمل", "ملغي", "مجدول", "تم التأكيد"])
        filters_layout.addWidget(self.status_filter)
        
        # زر تطبيق الفلتر
        apply_filter_btn = QPushButton("تطبيق الفلتر")
        apply_filter_btn.clicked.connect(self.apply_timeline_filters)
        filters_layout.addWidget(apply_filter_btn)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
    def setup_visits_timeline(self, layout):
        """إعداد جدول الخط الزمني للزيارات"""
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(6)
        self.timeline_table.setHorizontalHeaderLabels([
            "التاريخ", "القسم", "الطبيب", "الحالة", "الوقت", "ملاحظات"
        ])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timeline_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.timeline_table)
        
    def quick_search_by_phone(self):
        """بحث سريع برقم الجوال"""
        phone = self.phone_search.text().strip()
        if len(phone) >= 3:  # بحث عند إدخال 3 أرقام على الأقل
            self.search_patient_by_phone(phone)
            
    def quick_search_by_name(self):
        """بحث سريع بالاسم"""
        name = self.name_search.text().strip()
        if len(name) >= 2:  # بحث عند إدخال حرفين على الأقل
            self.search_patient_by_name(name)
            
    def search_patient_by_phone(self, phone):
        """بحث المريض برقم الجوال"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, phone FROM patients 
                WHERE clinic_id = ? AND phone LIKE ?
                ORDER BY name
            ''', (self.clinic_id, f'%{phone}%'))
            
            patients = cursor.fetchall()
            conn.close()
            
            if patients:
                if len(patients) == 1:
                    # تحميل المريض مباشرة إذا كان هناك تطابق واحد
                    self.load_patient_data(patients[0][0])
                else:
                    # عرض قائمة التطابقات
                    self.show_search_results(patients, "phone")
            else:
                self.show_no_results_dialog(phone)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في البحث: {str(e)}")
            
    def search_patient_by_name(self, name):
        """بحث المريض بالاسم"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, phone FROM patients 
                WHERE clinic_id = ? AND name LIKE ?
                ORDER BY name
            ''', (self.clinic_id, f'%{name}%'))
            
            patients = cursor.fetchall()
            conn.close()
            
            if patients:
                if len(patients) == 1:
                    self.load_patient_data(patients[0][0])
                else:
                    self.show_search_results(patients, "name")
            else:
                self.show_no_results_dialog(name)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في البحث: {str(e)}")
            
    def show_search_results(self, patients, search_type):
        """عرض نتائج البحث"""
        from PyQt5.QtWidgets import QDialog, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("نتائج البحث")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel(f"تم العثور على {len(patients)} نتيجة:")
        layout.addWidget(title)
        
        list_widget = QListWidget()
        for patient_id, name, phone in patients:
            list_widget.addItem(f"{name} - {phone}")
        layout.addWidget(list_widget)
        
        buttons_layout = QHBoxLayout()
        
        select_btn = QPushButton("اختيار المريض")
        select_btn.clicked.connect(lambda: self.on_patient_selected(list_widget, patients, dialog))
        buttons_layout.addWidget(select_btn)
        
        new_btn = QPushButton("مريض جديد")
        new_btn.clicked.connect(lambda: self.create_new_patient(dialog))
        buttons_layout.addWidget(new_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        dialog.exec_()
        
    def on_patient_selected(self, list_widget, patients, dialog):
        """عند اختيار مريض من نتائج البحث"""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            patient_id = patients[current_row][0]
            dialog.accept()
            self.load_patient_data(patient_id)
            
    def show_no_results_dialog(self, search_term):
        """عرض نافذة عند عدم وجود نتائج"""
        reply = QMessageBox.question(
            self,
            "لا توجد نتائج",
            f"لم يتم العثور على مريض بـ '{search_term}'. هل تريد إنشاء مريض جديد؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.create_new_patient()
            
    def create_new_patient(self, parent_dialog=None):
        """إنشاء مريض جديد"""
        try:
            from .patient_dialog import PatientDialog
            dialog = PatientDialog(self.db_path, self.clinic_id, None, self)
            if dialog.exec_() == QDialog.Accepted:
                # إعادة البحث لتحميل المريض الجديد
                if parent_dialog:
                    parent_dialog.accept()
                self.load_patient_data(dialog.patient_id)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء المريض: {str(e)}")
            
    def load_patient_data(self, patient_id=None):
        """تحميل بيانات المريض"""
        if patient_id:
            self.patient_id = patient_id
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تحميل البيانات الأساسية
            cursor.execute('''
                SELECT name, phone, email, gender, date_of_birth, notes
                FROM patients WHERE id = ?
            ''', (self.patient_id,))
            
            patient_data = cursor.fetchone()
            if patient_data:
                name, phone, email, gender, birth_date, notes = patient_data
                self.current_patient = {
                    'name': name,
                    'phone': phone,
                    'email': email,
                    'gender': gender,
                    'birth_date': birth_date,
                    'notes': notes
                }
                
                # تحديث واجهة المستخدم
                self.update_patient_display()
                
                # تحميل البيانات الأخرى
                self.load_departments_summary()
                self.load_timeline_data()
                self.load_quick_notes()
                
                # تفعيل الأزرار
                self.edit_btn.setEnabled(True)
                self.new_appointment_btn.setEnabled(True)
                self.send_message_btn.setEnabled(True)
                
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المريض: {str(e)}")
            
    def update_patient_display(self):
        """تحديث عرض بيانات المريض"""
        if self.current_patient:
            # تحديث العنوان
            self.patient_header.setText(
                f"بطاقة المريض - {self.current_patient['name']} ({self.current_patient['phone']})"
            )
            
            # تحديث المعلومات الشخصية
            self.info_labels['name'].setText(self.current_patient['name'])
            self.info_labels['phone'].setText(self.current_patient['phone'])
            self.info_labels['email'].setText(self.current_patient['email'] or "---")
            self.info_labels['gender'].setText(self.current_patient['gender'] or "---")
            self.info_labels['birth_date'].setText(self.current_patient['birth_date'] or "---")
            
            # حساب العمر
            if self.current_patient['birth_date']:
                try:
                    birth_date = datetime.strptime(self.current_patient['birth_date'], '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                    self.info_labels['age'].setText(f"{age} سنة")
                except:
                    self.info_labels['age'].setText("---")
            else:
                self.info_labels['age'].setText("---")
                
    def load_departments_summary(self):
        """تحميل الملخص الذكي للأقسام"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT d.specialty, MAX(a.appointment_date), d.name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = ?
                GROUP BY d.specialty
                ORDER BY MAX(a.appointment_date) DESC
            ''', (self.patient_id,))
            
            departments = cursor.fetchall()
            
            self.departments_list.clear()
            for specialty, last_visit, doctor_name in departments:
                item_text = f"🏥 {specialty}\nآخر زيارة: {last_visit}\nآخر طبيب: {doctor_name}"
                item = QListWidgetItem(item_text)
                self.departments_list.addItem(item)
                
            conn.close()
            
        except Exception as e:
            print(f"خطأ في تحميل ملخص الأقسام: {e}")
            
    def load_timeline_data(self):
        """تحميل بيانات الخط الزمني"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.appointment_date, d.specialty, d.name, a.status, a.appointment_time, a.notes
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            ''', (self.patient_id,))
            
            appointments = cursor.fetchall()
            
            # تحديث الجدول
            self.timeline_table.setRowCount(len(appointments))
            for row, appointment in enumerate(appointments):
                for col, value in enumerate(appointment):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    
                    # تلوين حسب الحالة
                    if col == 3:  # عمود الحالة
                        if value == 'تم الحضور':
                            item.setBackground(QColor(39, 174, 96, 100))
                        elif value == 'ملغي':
                            item.setBackground(QColor(231, 76, 60, 100))
                        elif value == 'مجدول':
                            item.setBackground(QColor(243, 156, 18, 100))
                            
                    self.timeline_table.setItem(row, col, item)
                    
            conn.close()
            
        except Exception as e:
            print(f"خطأ في تحميل الخط الزمني: {e}")
            
    def load_quick_notes(self):
        """تحميل الملاحظات السريعة"""
        if self.current_patient and self.current_patient['notes']:
            self.quick_notes_input.setPlainText(self.current_patient['notes'])
            
    def save_quick_notes(self):
        """حفظ الملاحظات السريعة"""
        if not self.patient_id:
            return
            
        try:
            notes = self.quick_notes_input.toPlainText()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE patients SET notes = ? WHERE id = ?
            ''', (notes, self.patient_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تم حفظ الملاحظات بنجاح")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الملاحظات: {str(e)}")
            
    def apply_timeline_filters(self):
        """تطبيق فلاتر الخط الزمني"""
        # سيتم تنفيذ المنطق الكامل في التحديثات القادمة
        self.load_timeline_data()
        
    def edit_patient(self):
        """تعديل بيانات المريض"""
        if not self.patient_id:
            return
            
        try:
            from .patient_dialog import PatientDialog
            
            # تحميل بيانات المريض الحالية
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patients WHERE id = ?', (self.patient_id,))
            patient_data = cursor.fetchone()
            conn.close()
            
            if patient_data:
                # تحويل إلى قاموس
                columns = [description[0] for description in cursor.description]
                patient_dict = dict(zip(columns, patient_data))
                
                dialog = PatientDialog(self.db_path, self.clinic_id, patient_dict, self)
                if dialog.exec_() == QDialog.Accepted:
                    self.load_patient_data()
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المريض: {str(e)}")
            
    def new_appointment(self):
        """إنشاء موعد جديد"""
        if not self.patient_id:
            return
            
        try:
            from .appointment_dialog import AppointmentDialog
            
            # تحضير بيانات الموعد
            appointment_data = {
                'patient_id': self.patient_id,
                'patient_name': self.current_patient['name'],
                'patient_phone': self.current_patient['phone']
            }
            
            dialog = AppointmentDialog(self.db_path, self.clinic_id, appointment_data, self)
            if dialog.exec_() == QDialog.Accepted:
                # إعادة تحميل البيانات
                self.load_departments_summary()
                self.load_timeline_data()
                QMessageBox.information(self, "نجاح", "تم إنشاء الموعد بنجاح")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء الموعد: {str(e)}")
            
    def send_message(self):
        """إرسال رسالة للمريض"""
        if not self.patient_id:
            return
            
        QMessageBox.information(self, "إرسال رسالة", "نظام إرسال الرسائل قيد التطوير")
        
    def advanced_search(self):
        """البحث المتقدم"""
        QMessageBox.information(self, "بحث متقدم", "نظام البحث المتقدم قيد التطوير")

if __name__ == "__main__":
    # اختبار الوحدة
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = PatientCard("data/clinics.db", 1)
    window.show()
    sys.exit(app.exec_())