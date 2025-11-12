# ui/components/appointments/actions.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QInputDialog, QMessageBox, QMenu, QDialog)
from PyQt5.QtCore import Qt
import logging
from datetime import datetime

class AppointmentsActions:
    """مدير إجراءات المواعد"""
    
    def __init__(self, main_app):
        self.main = main_app
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        self.main.shortcuts = {
            Qt.CTRL + Qt.Key_N: self.main.add_appointment,
            Qt.CTRL + Qt.Key_E: self.main.edit_appointment,
            Qt.CTRL + Qt.Key_R: self.main.load_appointments,
            Qt.CTRL + Qt.Key_F: lambda: self.main.search_input.setFocus(),
        }
    
    def add_appointment(self):
        """إضافة موعد جديد"""
        try:
            from ui.dialogs.appointment_dialog import AppointmentDialog
            
            dialog = AppointmentDialog(self.main.db_manager, self.main.whatsapp_manager, self.main)
            
            if dialog.exec_() == QDialog.Accepted:
                self.main.load_appointments()
                self.main.data_updated.emit()
                QMessageBox.information(self.main, "✅ نجاح", "تم إضافة الموعد الجديد بنجاح!")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة الموعد: {e}")
            QMessageBox.critical(self.main, "❌ خطأ", f"فشل في إضافة الموعد: {e}")
    
    def edit_appointment(self):
        """تعديل بيانات الموعد المحدد"""
        try:
            appointment = self.main.get_selected_appointment()
            if not appointment:
                QMessageBox.warning(self.main, "⚠️ تحذير", "يرجى اختيار موعد من الجدول للتعديل")
                return
            
            from ui.dialogs.appointment_dialog import AppointmentDialog
            
            dialog = AppointmentDialog(self.main.db_manager, self.main.whatsapp_manager, self.main, appointment)
            
            if dialog.exec_() == QDialog.Accepted:
                self.main.load_appointments()
                self.main.data_updated.emit()
                QMessageBox.information(self.main, "✅ نجاح", "تم تحديث بيانات الموعد بنجاح")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تعديل الموعد: {e}")
            QMessageBox.critical(self.main, "❌ خطأ", f"فشل في تعديل الموعد: {e}")
    
    def confirm_appointment(self):
        """تأكيد الموعد المحدد"""
        appointment = self.main.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self.main, "⚠️ تحذير", "يرجى اختيار موعد للتأكيد")
            return
        
        if appointment.get('status') == '✅ مؤكد':
            QMessageBox.information(self.main, "ℹ️ معلومة", "هذا الموعد ✅ مؤكد بالفعل")
            return
        
        reply = QMessageBox.question(
            self.main, 
            "✅ تأكيد الموعد", 
            f"""هل تريد تأكيد الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.main.db_manager.update_appointment_status(appointment['id'], '✅ مؤكد')
                if success:
                    self.main.load_appointments()
                    self.main.data_updated.emit()
                    QMessageBox.information(self.main, "✅ نجاح", "تم تأكيد الموعد بنجاح!")
                else:
                    QMessageBox.critical(self.main, "❌ خطأ", "فشل في تأكيد الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في تأكيد الموعد: {e}")
                QMessageBox.critical(self.main, "❌ خطأ", f"فشل في تأكيد الموعد: {e}")
    
    def mark_as_completed(self):
        """تعليم الموعد كمكتمل"""
        appointment = self.main.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self.main, "⚠️ تحذير", "يرجى اختيار موعد للتأكيد")
            return
        
        reply = QMessageBox.question(
            self.main, 
            "✅ تأكيد الحضور", 
            f"""هل تريد تأكيد حضور الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.main.db_manager.update_appointment_status(appointment['id'], 'حاضر')
                if success:
                    self.main.load_appointments()
                    self.main.data_updated.emit()
                    QMessageBox.information(self.main, "✅ نجاح", "تم تأكيد حضور الموعد بنجاح")
                else:
                    QMessageBox.critical(self.main, "❌ خطأ", "فشل في تأكيد حضور الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في تأكيد حضور الموعد: {e}")
                QMessageBox.critical(self.main, "❌ خطأ", f"فشل في تأكيد حضور الموعد: {e}")
    
    def cancel_appointment(self):
        """إلغاء الموعد المحدد"""
        appointment = self.main.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self.main, "⚠️ تحذير", "يرجى اختيار موعد للإلغاء")
            return
        
        if appointment.get('status') == 'ملغى':
            QMessageBox.information(self.main, "ℹ️ معلومة", "هذا الموعد ملغي بالفعل")
            return
        
        reply = QMessageBox.question(
            self.main, 
            "🗑️ إلغاء الموعد", 
            f"""هل تريد إلغاء الموعد التالي?

👤 المريض: {appointment.get('patient_name', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.main.db_manager.update_appointment_status(appointment['id'], 'ملغى')
                if success:
                    self.main.load_appointments()
                    self.main.data_updated.emit()
                    QMessageBox.information(self.main, "✅ نجاح", "تم إلغاء الموعد بنجاح")
                else:
                    QMessageBox.critical(self.main, "❌ خطأ", "فشل في إلغاء الموعد")
                    
            except Exception as e:
                logging.error(f"❌ خطأ في إلغاء الموعد: {e}")
                QMessageBox.critical(self.main, "❌ خطأ", f"فشل في إلغاء الموعد: {e}")
    
    def show_enhanced_context_menu(self, position):
        """إصلاح ربط الأزرار بشكل مباشر وصحيح"""
        try:
            logging.info("🖱️ فتح القائمة المنبثقة...")
            
            # التحقق من وجود الجدول
            if not hasattr(self.main, 'appointments_table') or not self.main.appointments_table:
                logging.error("❌ الجدول غير متوفر للقائمة المنبثقة")
                return

            menu = QMenu(self.main.appointments_table)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 2px solid #007BFF;
                    border-radius: 8px;
                    padding: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QMenu::item {
                    padding: 10px 30px;
                    border-bottom: 1px solid #F0F0F0;
                }
                QMenu::item:selected {
                    background-color: #007BFF;
                    color: white;
                    border-radius: 5px;
                }
                QMenu::item:disabled {
                    color: #999;
                }
            """)
            
            # الحصول على الموعد المحدد
            selected_appointment = self.main.get_selected_appointment()
            
            if not selected_appointment:
                no_item = menu.addAction("❌ لم يتم اختيار موعد")
                no_item.setEnabled(False)
                menu.exec_(self.main.appointments_table.viewport().mapToGlobal(position))
                return
            
            # معلومات الموعد المحدد
            patient_name = selected_appointment.get('patient_name', 'غير معروف')
            status = selected_appointment.get('status', 'مجدول')
            
            # إضافة عنوان للموعد المحدد
            title_action = menu.addAction(f"📋 {patient_name} - {status}")
            title_action.setEnabled(False)
            menu.addSeparator()
            
            # الإجراءات الأساسية
            menu.addAction("📋 عرض التفاصيل الكاملة", self.view_appointment_details)
            menu.addAction("✏️ تعديل البيانات", self.main.edit_appointment)
            menu.addSeparator()
            
            # إجراءات حسب الحالة
            if status == 'مجدول':
                menu.addAction("✅ تأكيد الموعد", self.main.confirm_appointment)
            elif status == '✅ مؤكد':
                menu.addAction("📝 تم الحضور", self.main.mark_as_completed)
            
            menu.addSeparator()
            
            # إصلاح ربط إجراءات الواتساب - استخدام الدالة الجديدة
            whatsapp_submenu = menu.addMenu("📱 إرسال عبر واتساب")
            
            # استخدام الدالة الجديدة للإرسال المباشر
            whatsapp_submenu.addAction("🎉 رسالة ترحيب", 
                                     lambda: self.send_whatsapp_direct('welcome'))
            whatsapp_submenu.addAction("⏰ تذكير قبل 24 ساعة", 
                                     lambda: self.send_whatsapp_direct('reminder_24h'))
            whatsapp_submenu.addAction("🕒 تذكير قبل ساعتين", 
                                     lambda: self.send_whatsapp_direct('reminder_2h'))
            whatsapp_submenu.addAction("📝 رسالة مخصصة", 
                                     lambda: self.send_whatsapp_direct('custom'))
            
            menu.addSeparator()
            
            # إجراءات متقدمة
            menu.addAction("📊 تغيير الحالة", self.change_status)
            menu.addAction("🗑️ إلغاء الموعد", self.main.cancel_appointment)
            
            # عرض القائمة
            menu.exec_(self.main.appointments_table.viewport().mapToGlobal(position))
            logging.info("✅ تم عرض القائمة المنبثقة بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ فادح في عرض القائمة المنبثقة: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في عرض القائمة: {str(e)}")
    
    def send_whatsapp_direct(self, template_type):
        """إرسال مباشر ومضمون للواتساب"""
        try:
            logging.info(f"🎯 محاولة إرسال مباشر: {template_type}")
            
            # التحقق المباشر من الواتساب
            if not self.main.whatsapp_manager:
                logging.error("❌ لا يوجد whatsapp_manager")
                QMessageBox.warning(self.main, "خطأ", "نظام الواتساب غير متوفر")
                return False
            
            # إذا كان المدير لديه is_connected وتحققنا منه
            if hasattr(self.main.whatsapp_manager, 'is_connected'):
                if not self.main.whatsapp_manager.is_connected:
                    logging.warning("⚠️ المدير يظهر غير متصل - محاولة إرسال رغم ذلك")
                    # جرب الإرسال رغم ظهور عدم الاتصال
            
            # استخدام WhatsAppHandler للإرسال
            if hasattr(self.main, 'whatsapp') and self.main.whatsapp:
                success = self.main.whatsapp.send_template_message(template_type)
                if success:
                    logging.info(f"✅ الإرسال المباشر نجح: {template_type}")
                    return True
                else:
                    logging.error(f"❌ الإرسال المباشر فشل: {template_type}")
                    return False
            else:
                logging.error("❌ whatsapp handler غير متوفر")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في الإرسال المباشر: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في الإرسال: {e}")
            return False
    
    def view_appointment_details(self):
        """عرض تفاصيل الموعد"""
        appointment = self.main.get_selected_appointment()
        if not appointment:
            QMessageBox.warning(self.main, "⚠️ تحذير", "يرجى اختيار موعد لعرض التفاصيل")
            return
        
        details = f"""
🏥 التفاصيل الكاملة للموعد
{'='*50}

🆔 رقم الموعد: {appointment.get('id', '')}
👤 المريض: {appointment.get('patient_name', 'غير معروف')}
📞 الهاتف: {appointment.get('patient_phone', 'غير معروف')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', 'غير معروف')}

🏥 العيادة: {appointment.get('clinic_name', 'غير معروف')}
🏥 القسم: {appointment.get('department_name', 'غير معروف')}

📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}
🎯 النوع: {appointment.get('type', 'روتيني')}
📊 الحالة: {appointment.get('status', '')}

📝 الملاحظات:
{appointment.get('notes', 'لا توجد ملاحظات')}

⏰ آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        QMessageBox.information(self.main, f"📋 تفاصيل الموعد - {appointment.get('id', '')}", details)
    
    def change_status(self):
        """تغيير حالة الموعد"""
        appointment = self.main.get_selected_appointment()
        if not appointment:
            return
        
        statuses = ["🗓️ مجدول", "✅ مؤكد", "🕓 منتهي", "❌ ملغى", "🙋‍♂️ حاضر"]
        current_status = appointment.get('status', '🗓️ مجدول')
        current_index = statuses.index(current_status) if current_status in statuses else 0
        
        new_status, ok = QInputDialog.getItem(
            self.main, "تغيير الحالة", "اختر الحالة الجديدة:", statuses, current_index, False
        )
        
        if ok and new_status:
            try:
                success = self.main.db_manager.update_appointment_status(appointment['id'], new_status)
                if success:
                    self.main.load_appointments()
                    self.main.data_updated.emit()
                    QMessageBox.information(self.main, "✅ نجاح", f"تم تغيير الحالة إلى: {new_status}")
            except Exception as e:
                logging.error(f"❌ خطأ في تغيير الحالة: {e}")
    
    def show_advanced_search(self):
        """عرض نافذة البحث المتقدم"""
        try:
            search_text, ok = QInputDialog.getText(self.main, "بحث متقدم", "أدخل نص البحث:")
            if ok and search_text:
                self.main.quick_search(search_text)
        except Exception as e:
            logging.error(f"❌ خطأ في فتح البحث المتقدم: {e}")
    
    def quick_call(self):
        """اتصال سريع"""
        appointment = self.main.get_selected_appointment()
        if appointment:
            phone = appointment.get('patient_phone', '')
            if phone:
                try:
                    # فتح تطبيق الاتصال
                    import os, sys
                    if sys.platform == "win32":
                        os.system(f'start "" "tel:{phone}"')
                    elif sys.platform == "darwin":
                        os.system(f'open "tel:{phone}"')
                    else:
                        os.system(f'xdg-open "tel:{phone}"')
                except Exception as e:
                    logging.error(f"❌ خطأ في فتح الاتصال: {e}")
                    QMessageBox.information(self.main, "اتصال", f"جاري الاتصال بـ {phone}")
            else:
                QMessageBox.warning(self.main, "تحذير", "⚠️ لا يوجد رقم هاتف للمريض")
    
    def quick_message(self):
        """رسالة سريعة"""
        self.main.send_whatsapp_message()
    
    def quick_email(self):
        """بريد إلكتروني سريع"""
        appointment = self.main.get_selected_appointment()
        if appointment:
            patient_name = appointment.get('patient_name', '')
            subject = f"موعد - {patient_name}"
            body = f"""عزيزي/عزيزتي {patient_name},

بخصوص موعدكم المحدد:
📅 التاريخ: {appointment.get('appointment_date', '')}
🕒 الوقت: {appointment.get('appointment_time', '')}
👨‍⚕️ الطبيب: {appointment.get('doctor_name', '')}

مع تحيات العيادة"""
            
            try:
                # فتح عميل البريد
                import webbrowser
                from urllib.parse import quote
                email_url = f"mailto:?subject={quote(subject)}&body={quote(body)}"
                webbrowser.open(email_url)
            except Exception as e:
                logging.error(f"❌ خطأ في فتح البريد: {e}")
                QMessageBox.information(self.main, "بريد", "جاري فتح نافذة البريد الإلكتروني")
    
    def quick_reschedule(self):
        """إعادة جدولة سريعة"""
        appointment = self.main.get_selected_appointment()
        if appointment:
            self.main.edit_appointment()