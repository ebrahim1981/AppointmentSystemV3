# ui/components/appointments/data_manager.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QDate, QTimer  # ⭐⭐ أضف Qt هنا ⭐⭐
from PyQt5.QtGui import QColor, QFont
import logging
from datetime import datetime

class AppointmentsDataManager:
    """مدير بيانات المواعيد"""
    
    def __init__(self, main_app):
        self.main = main_app
        self.db_manager = main_app.db_manager
    
    def load_appointments(self):
        """تحميل قائمة المواعيد"""
        try:
            if self.db_manager is None:
                logging.error("❌ db_manager is None في AppointmentsManager")
                return
            
            # تطبيق الفلاتر
            filters = self.get_current_filters()
            
            appointments = self.db_manager.get_appointments(**filters)
            self.main.all_appointments = appointments  # حفظ نسخة للإحصائيات
            
            self.main.appointments_table.setRowCount(len(appointments))
            self.main.appointments_table.setSortingEnabled(False)  # تعطيل الترتيب أثناء التحميل
            
            for row, appointment in enumerate(appointments):
                self.add_appointment_to_table(row, appointment)
            
            self.main.appointments_table.setSortingEnabled(True)  # إعادة تفعيل الترتيب
            
            # تحديث الإحصائيات
            self.update_enhanced_stats(appointments)
            
            # تحديث شريط الحالة
            self.update_status_bar(len(appointments))
            
            # تحديث المعلومات الجانبية
            self.update_sidebar_info()
            
            logging.info(f"✅ تم تحميل {len(appointments)} موعد")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل المواعيد: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في تحميل قائمة المواعيد: {str(e)}")
    
    def get_current_filters(self):
        """الحصول على الفلاتر الحالية"""
        filters = {}
        
        # فلتر التاريخ
        date_filter = self.main.date_filter.currentText()
        if date_filter == "اليوم":
            filters['date'] = QDate.currentDate().toString("yyyy-MM-dd")
        elif date_filter == "غداً":
            filters['date'] = QDate.currentDate().addDays(1).toString("yyyy-MM-dd")
        elif date_filter == "مخصص":
            filters['start_date'] = self.main.custom_date_start.date().toString("yyyy-MM-dd")
            filters['end_date'] = self.main.custom_date_end.date().toString("yyyy-MM-dd")
        
        # فلتر الحالة
        status_filter = self.main.status_filter.currentText()
        if status_filter != "جميع الحالات":
            filters['status'] = status_filter
        
        # فلتر الطبيب
        doctor_filter = self.main.doctor_filter.currentText()
        if doctor_filter != "جميع الأطباء":
            filters['doctor_name'] = doctor_filter
        
        return filters
    
    def add_appointment_to_table(self, row, appointment):
        """إضافة موعد إلى الجدول مع تحسينات"""
        try:
            # عمود الاختيار
            select_item = QTableWidgetItem()
            select_item.setCheckState(Qt.Unchecked)
            select_item.setTextAlignment(Qt.AlignCenter)
            
            # الرقم
            id_item = QTableWidgetItem(str(appointment.get('id', '')))
            id_item.setTextAlignment(Qt.AlignCenter)
            
            # المريض
            patient_item = QTableWidgetItem(appointment.get('patient_name', 'غير معروف'))
            
            # الهاتف مع تنسيق دولي
            phone = appointment.get('patient_phone', '')
            country_code = appointment.get('patient_country_code', '+966')
            formatted_phone = self.format_phone_display(phone, country_code)
            phone_item = QTableWidgetItem(formatted_phone)
            phone_item.setTextAlignment(Qt.AlignCenter)
            
            # الطبيب
            doctor_item = QTableWidgetItem(appointment.get('doctor_name', 'غير معروف'))
            
            # التاريخ
            date_item = QTableWidgetItem(appointment.get('appointment_date', ''))
            date_item.setTextAlignment(Qt.AlignCenter)
            
            # الوقت
            time_item = QTableWidgetItem(appointment.get('appointment_time', ''))
            time_item.setTextAlignment(Qt.AlignCenter)
            
            # الحالة مع التلوين
            status = appointment.get('status', 'مجدول')
            status_item = QTableWidgetItem(status)
            self.color_status_item(status_item, status)
            
            # حالة الواتساب
            whatsapp_sent = appointment.get('whatsapp_sent', False)
            whatsapp_item = QTableWidgetItem("✅تم الارسال" if whatsapp_sent else "❌")
            whatsapp_item.setTextAlignment(Qt.AlignCenter)
            
            # الملاحظات
            notes_item = QTableWidgetItem(appointment.get('notes', ''))
            
            # إضافة العناصر للجدول
            items = [select_item, id_item, patient_item, phone_item, doctor_item, 
                    date_item, time_item, status_item, whatsapp_item, notes_item]
            
            for col, item in enumerate(items):
                if item is not None:
                    self.main.appointments_table.setItem(row, col, item)
                    
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة موعد للجدول: {e}")
    
    def format_phone_display(self, phone, country_code):
        """تنسيق عرض رقم الهاتف"""
        if not phone:
            return ""
        
        if country_code == '+966':
            return f"🇸🇦 {phone}"
        elif country_code == '+963':
            return f"🇸🇾 {phone}"
        else:
            return f"{country_code} {phone}"
    
    def color_status_item(self, item, status):
        """تلوين خلية الحالة مع تحسينات"""
        colors = {
            'مجدول': {'bg': '#E3F2FD', 'text': '#1565C0', 'border': '#2196F3'},  # أزرق فاتح
            '✅ مؤكد': {'bg': '#E8F5E8', 'text': '#2E7D32', 'border': '#4CAF50'},   # أخضر فاتح
            'حاضر': {'bg': '#F3E5F5', 'text': '#7B1FA2', 'border': '#9C27B0'},   # بنفسجي فاتح
            'منتهي': {'bg': '#F5F5F5', 'text': '#424242', 'border': '#9E9E9E'},  # رمادي
            'ملغى': {'bg': '#FFEBEE', 'text': '#C62828', 'border': '#F44336'}    # أحمر فاتح
        }
        
        color = colors.get(status, {'bg': '#95A5A6', 'text': '#000000'})
        item.setBackground(QColor(color['bg']))
        item.setForeground(QColor(color['text']))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Arial", 10, QFont.Bold))
    
    def update_enhanced_stats(self, appointments):
        """تحديث الإحصائيات المحسنة"""
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            today_appointments = [app for app in appointments if app.get('appointment_date') == today]
            
            stats = {
                'مجدول': 0,
                '✅ مؤكد': 0,
                'حاضر': 0,
                'منتهي': 0,
                'ملغى': 0,
                'رسائل': sum(1 for app in appointments if app.get('whatsapp_sent', False))
            }
            
            for app in appointments:
                status = app.get('status', '')
                if status in stats:
                    stats[status] += 1
            
            # تحديث عناصر الإحصائيات
            for status, count in stats.items():
                if status in self.main.stats_widgets:
                    value_label = self.main.stats_widgets[status].layout().itemAt(0).widget()
                    if value_label:
                        value_label.setText(str(count))
            
            # تحديث إحصائيات الواتساب في الشريط الجانبي
            self.update_whatsapp_stats()
                        
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    def update_whatsapp_stats(self):
        """تحديث إحصائيات الواتساب"""
        try:
            if self.main.whatsapp_manager and hasattr(self.main.whatsapp_manager, 'get_delivery_report'):
                stats = self.main.whatsapp_manager.get_delivery_report(7)  # آخر 7 أيام
                if stats:
                    stats_text = f"""
                    📊 إحصائيات الأسبوع:
                    
                    • 📤 الرسائل المرسلة: {stats.get('sent_messages', 0)}
                    • ❌ الرسائل الفاشلة: {stats.get('failed_messages', 0)}
                    • 📈 نسبة النجاح: {stats.get('success_rate', '0%')}
                    
                    ⚡ المزود: {getattr(self.main.whatsapp_manager, 'current_provider', 'غير معروف')}
                    """
                    self.main.whatsapp_stats_info.setText(stats_text)
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث إحصائيات الواتساب: {e}")
    
    def update_status_bar(self, count):
        """تحديث شريط الحالة"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            self.main.results_count.setText(f"{count} موعد")
            self.main.last_update.setText(f"آخر تحديث: {current_time}")
            
            # تحديث حالة النظام
            if count > 0:
                self.main.system_status.setText("🟢 النظام يعمل بشكل طبيعي")
                self.main.system_status.setStyleSheet("color: #27AE60; font-weight: bold;")
            else:
                self.main.system_status.setText("🟡 لا توجد مواعيد للعرض")
                self.main.system_status.setStyleSheet("color: #F39C12; font-weight: bold;")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث شريط الحالة: {e}")
    
    def update_sidebar_info(self):
        """تحديث المعلومات في الشريط الجانبي"""
        try:
            selected_appointment = self.get_selected_appointment()
            if selected_appointment:
                info_text = f"""
                📋 الموعد #{selected_appointment.get('id', '')}
                
                👤 المريض: {selected_appointment.get('patient_name', '')}
                📞 الهاتف: {selected_appointment.get('patient_phone', '')}
                👨‍⚕️ الطبيب: {selected_appointment.get('doctor_name', '')}
                
                📅 {selected_appointment.get('appointment_date', '')}
                🕒 {selected_appointment.get('appointment_time', '')}
                📊 {selected_appointment.get('status', '')}
                
                💬 {selected_appointment.get('notes', 'لا توجد ملاحظات')}
                """
                self.main.selected_appointment_info.setText(info_text)
            else:
                self.main.selected_appointment_info.setText("لم يتم اختيار موعد")
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الشريط الجانبي: {e}")
    
    def get_selected_appointment_id(self):
        """الحصول على رقم الموعد المحدد"""
        try:
            selected_items = self.main.appointments_table.selectedItems()
            if not selected_items:
                return None
            
            # البحث عن عمود ID (العمود الثاني)
            for item in selected_items:
                if item.column() == 1:  # عمود ID
                    item_text = item.text()
                    if item_text and item_text != 'None' and item_text.strip():
                        return int(item_text)
            return None
        except (ValueError, TypeError) as e:
            logging.error(f"خطأ في تحويل ID الموعد: {e}")
            return None
    
    def get_selected_appointment(self):
        """الحصول على الموعد المحدد"""
        try:
            appointment_id = self.get_selected_appointment_id()
            if appointment_id is None:
                return None
            
            appointment = self.db_manager.get_appointment_by_id(appointment_id)
            return appointment
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على بيانات الموعد: {e}")
            return None
    
    def get_selected_appointments(self):
        """الحصول على المواعيد المحددة"""
        selected_appointments = []
        for row in range(self.main.appointments_table.rowCount()):
            item = self.main.appointments_table.item(row, 0)  # عمود الاختيار
            if item and item.checkState() == Qt.Checked:
                appointment_id = self.main.appointments_table.item(row, 1).text()
                appointment = self.db_manager.get_appointment_by_id(int(appointment_id))
                if appointment:
                    selected_appointments.append(appointment)
        return selected_appointments
    
    def quick_search(self, text):
        """بحث سريع في المواعيد"""
        try:
            for row in range(self.main.appointments_table.rowCount()):
                match = False
                for col in range(self.main.appointments_table.columnCount()):
                    item = self.main.appointments_table.item(row, col)
                    if item and text.lower() in item.text().lower():
                        match = True
                        break
                
                self.main.appointments_table.setRowHidden(row, not match)
        except Exception as e:
            logging.error(f"❌ خطأ في البحث السريع: {e}")
    
    def setup_timers(self):
        """إعداد المؤقتات"""
        # مؤقتات للتحديث التلقائي
        self.main.auto_refresh_timer = QTimer()
        self.main.auto_refresh_timer.timeout.connect(self.main.load_appointments)
        self.main.auto_refresh_timer.start(300000)  # 5 دقائق
        
        # مؤقت للنسخ الاحتياطي التلقائي (كل 24 ساعة)
        self.main.backup_timer = QTimer()
        self.main.backup_timer.timeout.connect(self.main.backup_manager.auto_backup)
        self.main.backup_timer.start(86400000)  # 24 ساعة
        
        # مؤقت للتحقق من التذكيرات (كل 30 دقيقة)
        self.main.reminder_timer = QTimer()
        self.main.reminder_timer.timeout.connect(self.main.notification_manager.check_reminders)
        self.main.reminder_timer.start(1800000)  # 30 دقيقة
    
    def get_today_appointments(self):
        """الحصول على مواعيد اليوم"""
        try:
            today = self.get_today_date()  # استخدام الدالة المساعدة
            return self.db_manager.get_appointments(date=today)
        except Exception as e:
            logging.error(f"❌ خطأ في جلب مواعيد اليوم: {e}")
            return []
    
    def get_today_date(self):
        """الحصول على تاريخ اليوم"""
        return QDate.currentDate().toString("yyyy-MM-dd")
    
    def get_current_time(self):
        """الحصول على الوقت الحالي"""
        return datetime.now().strftime('%H:%M')
    
    def get_current_date(self):
        """الحصول على التاريخ الحالي"""
        return QDate.currentDate()

    def load_doctors(self):
        """تحميل قائمة الأطباء من قاعدة البيانات - مع معالجة الأخطاء"""
        try:
            logging.info("👨‍⚕️ جاري تحميل قائمة الأطباء...")
            
            # التحقق من وجود عنصر doctor_filter
            if not hasattr(self.main, 'doctor_filter') or self.main.doctor_filter is None:
                logging.error("❌ عنصر doctor_filter غير متوفر")
                return
            
            doctors = self.db_manager.get_doctors()
            self.main.doctor_filter.clear()
            self.main.doctor_filter.addItem("جميع الأطباء")
            
            for doctor in doctors:
                doctor_name = doctor.get('name', '')
                if doctor_name:
                    self.main.doctor_filter.addItem(doctor_name)
            
            logging.info(f"✅ تم تحميل {len(doctors)} طبيب")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الأطباء: {e}")
            # محاولة بديلة
            self.fallback_load_doctors()

    def fallback_load_doctors(self):
        """تحميل احتياطي للأطباء"""
        try:
            if hasattr(self.main, 'doctor_filter'):
                self.main.doctor_filter.clear()
                self.main.doctor_filter.addItem("جميع الأطباء")
                self.main.doctor_filter.addItem("د. افتراضي")
        except Exception as e:
            logging.error(f"❌ فشل التحمل الاحتياطي للأطباء: {e}")