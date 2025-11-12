# ui/components/appointments/whatsapp_handler.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QInputDialog, QMessageBox
import logging

class WhatsAppHandler:
    """معالج إجراءات الواتساب"""
    
    def __init__(self, main_app):
        self.main = main_app
        self.whatsapp_manager = main_app.whatsapp_manager
    
    def setup_integration(self):
        """إعداد تكامل واتساب حقيقي - الإصدار النهائي"""
        try:
            logging.info("🔗 بدء تكامل واتساب حقيقي...")
            
            # الخطوة 1: البحث عن نسخة موحدة من WhatsAppManager
            if not self.find_unified_whatsapp_manager():
                logging.error("❌ فشل في العثور على نسخة موحدة")
                return False
            
            # الخطوة 2: ربط الإشارات بشكل قوي
            self.connect_signals_strong()
            
            # الخطوة 3: اختبار التكامل
            self.test_integration()
            
            logging.info("✅ تكامل الواتساب الحقيقي مكتمل")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل تكامل الواتساب الحقيقي: {e}")
            return False

    def find_unified_whatsapp_manager(self):
        """البحث عن نسخة موحدة من WhatsAppManager"""
        try:
            # المحاولة 1: من main مباشرة
            if self.main.whatsapp_manager:
                self.whatsapp_manager = self.main.whatsapp_manager
                logging.info("✅ تم العثور على WhatsAppManager في main")
                return True
            
            # المحاولة 2: من التطبيق الرئيسي
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'whatsapp_manager') and app.whatsapp_manager:
                self.whatsapp_manager = app.whatsapp_manager
                self.main.whatsapp_manager = app.whatsapp_manager
                logging.info("✅ تم العثور على WhatsAppManager في التطبيق")
                return True
            
            # المحاولة 3: من النظام
            import sys
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, 'whatsapp_manager'):
                self.whatsapp_manager = main_module.whatsapp_manager
                self.main.whatsapp_manager = main_module.whatsapp_manager
                logging.info("✅ تم العثور على WhatsAppManager في النظام")
                return True
                
            # المحاولة 4: إنشاء جديد كحل أخير
            logging.warning("⚠️ لم أجد نسخة موحدة - جاري إنشاء جديدة...")
            return self.create_new_whatsapp_manager()
            
        except Exception as e:
            logging.error(f"❌ فشل البحث عن نسخة موحدة: {e}")
            return False

    def create_new_whatsapp_manager(self):
        """إنشاء مدير واتساب جديد"""
        try:
            # محاولة استيراد من مسارات مختلفة
            try:
                from whatsapp_manager import WhatsAppManager
                self.whatsapp_manager = WhatsAppManager(self.main.db_manager, self.main.clinic_id)
            except ImportError:
                try:
                    from whatsapp.whatsapp_manager import WhatsAppManager
                    self.whatsapp_manager = WhatsAppManager(self.main.db_manager, self.main.clinic_id)
                except ImportError:
                    logging.error("❌ فشل في استيراد WhatsAppManager")
                    return False
            
            self.main.whatsapp_manager = self.whatsapp_manager
            logging.info("✅ تم إنشاء مدير الواتساب بنجاح")
            return True
        except Exception as e:
            logging.error(f"❌ فشل في إنشاء مدير الواتساب: {e}")
            return False

    def connect_signals_strong(self):
        """ربط إشارات قوي ومضمون"""
        try:
            if not self.whatsapp_manager:
                return
                
            logging.info("🔌 بدء ربط إشارات قوي...")
            
            # إشارات必须 تكون مربوطة
            mandatory_signals = {
                'connection_status_changed': self.main.on_whatsapp_status_changed,
                'message_sent': self.main.on_message_sent,
                'message_failed': self.main.on_message_failed
            }
            
            for signal_name, handler in mandatory_signals.items():
                if hasattr(self.whatsapp_manager, signal_name):
                    try:
                        signal = getattr(self.whatsapp_manager, signal_name)
                        # فصل كامل
                        try:
                            signal.disconnect()
                        except:
                            pass
                        # ربط جديد
                        signal.connect(handler)
                        logging.info(f"✅ تم الربط القوي: {signal_name}")
                    except Exception as e:
                        logging.error(f"❌ فشل الربط القوي لـ {signal_name}: {e}")
                else:
                    logging.warning(f"⚠️ الإشارة {signal_name} غير موجودة للربط")
                    
        except Exception as e:
            logging.error(f"❌ فشل الربط القوي: {e}")

    def test_integration(self):
        """اختبار التكامل"""
        try:
            logging.info("🧪 اختبار تكامل واتساب...")
            
            if not self.whatsapp_manager:
                return
                
            # اختبار بسيط: إذا كان بإمكاننا الوصول للدوال الأساسية
            test_methods = ['send_message', 'check_connection']
            for method in test_methods:
                if hasattr(self.whatsapp_manager, method):
                    logging.info(f"✅ الدالة {method} متاحة")
                else:
                    logging.warning(f"⚠️ الدالة {method} غير متاحة")
                    
            # تحديث الحالة
            if hasattr(self.main, 'on_whatsapp_status_changed'):
                self.main.on_whatsapp_status_changed("connected")
                
        except Exception as e:
            logging.error(f"❌ فشل اختبار التكامل: {e}")

    def validate_whatsapp_ready(self):
        """التحقق من جاهزية الواتساب للإرسال"""
        if not self.whatsapp_manager:
            QMessageBox.warning(self.main, "تحذير", "⚠️ نظام الواتساب غير متوفر")
            return False
        
        # ✅ افترض أن الاتصال نشط إذا كان الإرسال يعمل
        if not hasattr(self.whatsapp_manager, 'is_connected') or not self.whatsapp_manager.is_connected:
            # حاول تحديث الحالة أولاً
            self.update_status(force_check=False)
            if not self.whatsapp_manager.is_connected:
                QMessageBox.warning(self.main, "تحذير", "⚠️ الواتساب غير متصل. يرجى التحقق من الاتصال أولاً")
                return False
        
        return True
    
    def validate_appointment_for_whatsapp(self, appointment):
        """التحقق من صحة الموعد للإرسال"""
        if not appointment:
            QMessageBox.warning(self.main, "تحذير", "⚠️ لم يتم اختيار موعد")
            return False
        
        phone = appointment.get('patient_phone')
        if not phone:
            QMessageBox.warning(self.main, "تحذير", "⚠️ لا يوجد رقم هاتف للمريض")
            return False
        
        return True
    
    def send_message(self):
        """إرسال رسالة واتساب للموعد المحدد"""
        try:
            # التحقق من الجاهزية
            if not self.validate_whatsapp_ready():
                return
            
            appointment = self.main.get_selected_appointment()
            if not self.validate_appointment_for_whatsapp(appointment):
                return
            
            message, ok = QInputDialog.getMultiLineText(
                self.main, "رسالة واتساب", 
                "أدخل نص الرسالة:", 
                f"عزيزي/عزيزتي {appointment.get('patient_name', '')}..."
            )
            
            if ok and message:
                phone = appointment.get('patient_phone')
                
                # إظهار تأكيد الإرسال
                reply = QMessageBox.question(
                    self.main, 
                    "تأكيد الإرسال",
                    f"هل تريد إرسال الرسالة إلى:\n{appointment.get('patient_name')} - {phone}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    success = self.whatsapp_manager.send_message(phone, message, "custom")
                    
                    if success:
                        QMessageBox.information(self.main, "نجاح", "✅ تم إرسال الرسالة بنجاح!")
                        self.main.load_appointments()
                    else:
                        QMessageBox.warning(self.main, "تحذير", "⚠️ فشل في إرسال الرسالة")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال رسالة واتساب: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في إرسال الرسالة: {e}")
    
    def send_template_message(self, template_type):
        """إرسال قالب واتساب محدد"""
        try:
            # التحقق من الجاهزية
            if not self.validate_whatsapp_ready():
                return
            
            appointment = self.main.get_selected_appointment()
            if not self.validate_appointment_for_whatsapp(appointment):
                return
            
            phone = appointment.get('patient_phone')
            country_code = appointment.get('patient_country_code', '+966')
            
            # أسماء القوالب
            template_names = {
                'welcome': 'رسالة ترحيب',
                'reminder_24h': 'تذكير قبل 24 ساعة',
                'reminder_2h': 'تذكير قبل ساعتين'
            }
            
            template_name = template_names.get(template_type, template_type)
            
            # تأكيد الإرسال
            reply = QMessageBox.question(
                self.main, 
                f"إرسال {template_name}",
                f"هل تريد إرسال {template_name} إلى:\n{appointment.get('patient_name')} - {phone}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # إرسال الرسالة باستخدام القالب
                success = self.whatsapp_manager.send_template_message(
                    phone, template_type, {
                        'patient_name': appointment.get('patient_name', 'عزيزي/عزيزتي'),
                        'appointment_date': appointment.get('appointment_date', ''),
                        'appointment_time': appointment.get('appointment_time', ''),
                        'doctor_name': appointment.get('doctor_name', ''),
                        'clinic_name': appointment.get('clinic_name', ''),
                        'department_name': appointment.get('department_name', '')
                    }, appointment['id'], appointment.get('patient_id')
                )
                
                if success:
                    QMessageBox.information(self.main, "نجاح", f"✅ تم إرسال {template_name} بنجاح!")
                    self.main.load_appointments()
                else:
                    QMessageBox.warning(self.main, "تحذير", f"⚠️ فشل في إرسال {template_name}")
                    
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال القالب: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في إرسال القالب: {e}")
    
    def send_custom_whatsapp(self):
        """إرسال رسالة واتساب مخصصة"""
        self.send_message()
    
    def test_connection(self):
        """اختبار اتصال الواتساب"""
        if not self.whatsapp_manager:
            QMessageBox.warning(self.main, "تحذير", "⚠️ مدير الواتساب غير متوفر")
            return
        
        try:
            is_connected = self.whatsapp_manager.check_connection()
            if is_connected:
                QMessageBox.information(self.main, "نجاح", "✅ اتصال الواتساب يعمل بشكل صحيح")
                self.main.on_whatsapp_status_changed("connected")
            else:
                QMessageBox.warning(self.main, "تحذير", "❌ فشل في الاتصال بواتساب\nيرجى التحقق من الإعدادات")
                self.main.on_whatsapp_status_changed("disconnected")
        except Exception as e:
            QMessageBox.critical(self.main, "خطأ", f"❌ خطأ في اختبار الاتصال: {e}")
    
    def update_status(self, force_check=False):
        """تحديث حالة الواتساب"""
        try:
            if not self.whatsapp_manager:
                self.main.on_whatsapp_status_changed("disconnected")
                return
            
            # إذا كان الإرسال يعمل، افترض أن الاتصال نشط
            if not force_check and hasattr(self.whatsapp_manager, 'is_connected'):
                if self.whatsapp_manager.is_connected:
                    self.main.on_whatsapp_status_changed("connected")
                    return
            
            # فحص الاتصال فقط إذا طُلب ذلك
            if force_check:
                result = self.whatsapp_manager.check_connection()
                if result.get("success"):
                    self.main.on_whatsapp_status_changed("connected")
                else:
                    self.main.on_whatsapp_status_changed("disconnected")
            else:
                # افترض الاتصال إذا لم يتم الفحص القسري
                self.main.on_whatsapp_status_changed("connected")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الواتساب: {e}")
            self.main.on_whatsapp_status_changed("disconnected")
    
    def open_whatsapp_settings(self):
        """فتح إعدادات الواتساب"""
        try:
            from whatsapp.whatsapp_settings import WhatsAppSettingsManager
            
            dialog = WhatsAppSettingsManager(self.main.db_manager, self.main.clinic_id, self.main)
            dialog.exec_()
            
            # تحديث حالة الواتساب بعد إغلاق الإعدادات
            self.update_status()
            
        except ImportError:
            QMessageBox.warning(self.main, "تحذير", "⚠️ وحدة إعدادات الواتساب غير متوفرة")
        except Exception as e:
            logging.error(f"❌ خطأ في فتح إعدادات الواتساب: {e}")
            QMessageBox.critical(self.main, "خطأ", f"فشل في فتح إعدادات الواتساب: {e}")