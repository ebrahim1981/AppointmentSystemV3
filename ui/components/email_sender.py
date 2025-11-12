# -*- coding: utf-8 -*-
import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from PyQt5.QtCore import QObject

class EmailSender(QObject):
    """مرسل الإيميلات التلقائية"""
    
    def __init__(self, db_manager, settings_manager):
        super().__init__()
        self.db_manager = db_manager
        self.settings_manager = settings_manager
        self.smtp_connection = None
        
        logging.info("✅ تم تهيئة مرسل الإيميلات")
    
    def get_email_settings(self):
        """الحصول على إعدادات الإيميل"""
        try:
            settings = self.settings_manager.get_system_settings()
            
            email_settings = {
                'smtp_server': settings.get('smtp_server', ''),
                'smtp_port': int(settings.get('smtp_port', 587)),
                'username': settings.get('smtp_username', ''),
                'password': settings.get('smtp_password', ''),
                'from_name': settings.get('smtp_from_name', ''),
                'use_tls': settings.get('smtp_use_tls', '1') == '1'
            }
            
            return email_settings
        except Exception as e:
            logging.error(f"❌ فشل في الحصول على إعدادات الإيميل: {e}")
            return {}
    
    def connect_to_smtp(self):
        """الاتصال بخادم SMTP"""
        try:
            settings = self.get_email_settings()
            
            if not all([settings.get('smtp_server'), settings.get('username'), settings.get('password')]):
                logging.error("❌ إعدادات الإيميل غير مكتملة")
                return False
            
            self.smtp_connection = smtplib.SMTP(settings['smtp_server'], settings['smtp_port'])
            
            if settings['use_tls']:
                self.smtp_connection.starttls()
            
            self.smtp_connection.login(settings['username'], settings['password'])
            logging.info("✅ تم الاتصال بخادم الإيميل بنجاح")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل في الاتصال بخادم الإيميل: {e}")
            self.smtp_connection = None
            return False
    
    def send_notification(self, patient, notification_type):
        """إرسال إشعار إيميل للمريض"""
        try:
            if not self.smtp_connection and not self.connect_to_smtp():
                return False
            
            # إنشاء الرسالة
            message = self.create_email_message(patient, notification_type)
            if not message:
                return False
            
            # إرسال الرسالة
            settings = self.get_email_settings()
            self.smtp_connection.send_message(message)
            
            logging.info(f"✅ تم إرسال إيميل {notification_type} للمريض {patient.get('name')}")
            return True
            
        except Exception as e:
            logging.error(f"❌ فشل في إرسال الإيميل: {e}")
            return False
    
    def create_email_message(self, patient, notification_type):
        """إنشاء رسالة إيميل"""
        try:
            settings = self.get_email_settings()
            patient_email = patient.get('email')
            
            if not patient_email:
                logging.error(f"❌ لا يوجد بريد إلكتروني للمريض {patient.get('name')}")
                return None
            
            # إنشاء الرسالة
            message = MimeMultipart()
            message['From'] = f"{settings['from_name']} <{settings['username']}>"
            message['To'] = patient_email
            message['Subject'] = self.get_email_subject(notification_type, patient)
            
            # إضافة محتوى الرسالة
            html_content = self.get_email_content(notification_type, patient)
            message.attach(MimeText(html_content, 'html', 'utf-8'))
            
            return message
            
        except Exception as e:
            logging.error(f"❌ فشل في إنشاء رسالة الإيميل: {e}")
            return None
    
    def get_email_subject(self, notification_type, patient):
        """الحصول على عنوان الإيميل حسب النوع"""
        subjects = {
            'welcome': f"مرحباً بك في {self.get_clinic_name()}",
            '24h_reminder': f"تذكير بموعدك في {self.get_clinic_name()}",
            '2h_reminder': f"تذكير بموعدك القريب في {self.get_clinic_name()}",
            'followup': f"متابعة بعد زيارتك لـ{self.get_clinic_name()}",
            'appointment_confirmation': f"تأكيد موعدك في {self.get_clinic_name()}"
        }
        
        return subjects.get(notification_type, f"إشعار من {self.get_clinic_name()}")
    
    def get_email_content(self, notification_type, patient):
        """الحصول على محتوى الإيميل حسب النوع"""
        try:
            # الحصول على بيانات إضافية إذا لزم الأمر
            appointment_data = self.get_patient_appointment_data(patient['id'])
            
            templates = {
                'welcome': self.get_welcome_template(patient),
                '24h_reminder': self.get_24h_reminder_template(patient, appointment_data),
                '2h_reminder': self.get_2h_reminder_template(patient, appointment_data),
                'followup': self.get_followup_template(patient),
                'appointment_confirmation': self.get_appointment_confirmation_template(patient, appointment_data)
            }
            
            template = templates.get(notification_type, self.get_default_template(patient))
            
            # إضافة تذييل الرسالة
            footer = self.get_email_footer()
            
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    {template}
                    {footer}
                </div>
            </body>
            </html>
            """
            
        except Exception as e:
            logging.error(f"❌ فشل في إنشاء محتوى الإيميل: {e}")
            return self.get_default_template(patient)
    
    def get_welcome_template(self, patient):
        """قالب رسالة الترحيب"""
        return f"""
        <h2 style="color: #2C3E50;">مرحباً بك {patient.get('name')} 👋</h2>
        <p>نشكرك على ثقتك بنا ونتطلع لتقديم أفضل الخدمات الطبية لك.</p>
        <p>يمكنك الآن حجز مواعيدك بسهولة ومتابعة حالتك الصحية معنا.</p>
        """
    
    def get_24h_reminder_template(self, patient, appointment_data):
        """قالب تذكير 24 ساعة"""
        return f"""
        <h2 style="color: #E67E22;">تذكير بموعدك ⏰</h2>
        <p>عزيزي/عزيزتي {patient.get('name')}</p>
        <p>نذكرك بموعدك المحدد لدينا:</p>
        <div style="background: #F8F9FA; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>📅 التاريخ:</strong> {appointment_data.get('date', '')}</p>
            <p><strong>🕒 الوقت:</strong> {appointment_data.get('time', '')}</p>
            <p><strong>👨‍⚕️ الطبيب:</strong> {appointment_data.get('doctor', '')}</p>
        </div>
        <p>نرجو منك التواجد قبل الموعد بـ 15 دقيقة.</p>
        """
    
    def get_2h_reminder_template(self, patient, appointment_data):
        """قالب تذكير ساعتين"""
        return f"""
        <h2 style="color: #E74C3C;">تذكير بموعدك القريب 🔔</h2>
        <p>عزيزي/عزيزتي {patient.get('name')}</p>
        <p>موعدك معنا بعد ساعتين:</p>
        <div style="background: #FFF3CD; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>🕒 الوقت:</strong> {appointment_data.get('time', '')}</p>
            <p><strong>👨‍⚕️ الطبيب:</strong> {appointment_data.get('doctor', '')}</p>
        </div>
        <p>نرجو منك التواجد في العيادة قبل الموعد.</p>
        """
    
    def get_followup_template(self, patient):
        """قالب متابعة بعد الزيارة"""
        return f"""
        <h2 style="color: #27AE60;">شكراً لزيارتك 🙏</h2>
        <p>عزيزي/عزيزتي {patient.get('name')}</p>
        <p>نشكرك على زيارتنا ونتمنى لك الشفاء العاجل.</p>
        <p>لا تتردد في التواصل معنا إذا كان لديك أي استفسارات.</p>
        """
    
    def get_appointment_confirmation_template(self, patient, appointment_data):
        """قالب تأكيد الموعد"""
        return f"""
        <h2 style="color: #2980B9;">تم تأكيد موعدك ✅</h2>
        <p>عزيزي/عزيزتي {patient.get('name')}</p>
        <p>تم تأكيد موعدك بنجاح:</p>
        <div style="background: #D4EDDA; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>📅 التاريخ:</strong> {appointment_data.get('date', '')}</p>
            <p><strong>🕒 الوقت:</strong> {appointment_data.get('time', '')}</p>
            <p><strong>👨‍⚕️ الطبيب:</strong> {appointment_data.get('doctor', '')}</p>
        </div>
        """
    
    def get_default_template(self, patient):
        """القالب الافتراضي"""
        return f"""
        <h2 style="color: #2C3E50;">إشعار من {self.get_clinic_name()}</h2>
        <p>عزيزي/عزيزتي {patient.get('name')}</p>
        <p>هذا إشعار مهم من العيادة.</p>
        """
    
    def get_email_footer(self):
        """تذييل رسالة الإيميل"""
        clinic_info = self.settings_manager.get_clinic_info()
        
        return f"""
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <div style="text-align: center; color: #7F8C8D; font-size: 14px;">
            <p><strong>{clinic_info.get('name', 'العيادة')}</strong></p>
            <p>{clinic_info.get('address', '')}</p>
            <p>هاتف: {clinic_info.get('phone', '')} | بريد إلكتروني: {clinic_info.get('email', '')}</p>
            <p>⏰ أوقات العمل: {clinic_info.get('working_hours', '')}</p>
        </div>
        """
    
    def get_clinic_name(self):
        """الحصول على اسم العيادة"""
        clinic_info = self.settings_manager.get_clinic_info()
        return clinic_info.get('name', 'العيادة')
    
    def get_patient_appointment_data(self, patient_id):
        """الحصول على بيانات موعد المريض"""
        try:
            # الحصول على أحدث موعد للمريض
            appointments = self.db_manager.get_patient_appointments(patient_id)
            if appointments:
                latest = appointments[0]
                return {
                    'date': latest.get('appointment_date', ''),
                    'time': latest.get('appointment_time', ''),
                    'doctor': latest.get('doctor_name', '')
                }
            return {}
        except Exception as e:
            logging.error(f"❌ فشل في الحصول على بيانات الموعد: {e}")
            return {}
    
    def test_connection(self):
        """اختبار اتصال الإيميل"""
        try:
            return self.connect_to_smtp()
        except Exception as e:
            logging.error(f"❌ فشل في اختبار اتصال الإيميل: {e}")
            return False
    
    def disconnect(self):
        """قطع الاتصال بخادم SMTP"""
        try:
            if self.smtp_connection:
                self.smtp_connection.quit()
                self.smtp_connection = None
                logging.info("✅ تم قطع الاتصال بخادم الإيميل")
        except Exception as e:
            logging.error(f"❌ فشل في قطع الاتصال: {e}")