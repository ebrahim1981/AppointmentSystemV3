# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject
import json

class MessageTemplates(QObject):
    """نظام قوالب الرسائل - للإضافة المستقبلية فقط"""
    
    def __init__(self, db_path, clinic_id):
        super().__init__()
        self.db_path = db_path
        self.clinic_id = clinic_id
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """تحميل القوالب من قاعدة البيانات"""
        # هذه مجرد هيكلة أساسية للقوالب
        self.templates = {
            'appointment_confirmation': {
                'clinic': "تأكيد موعد - {clinic_name}\n{patient_name} موعدك بتاريخ {date} الساعة {time}",
                'department': "تأكيد موعد - {department_name}\n{patient_name} موعدك بتاريخ {date} الساعة {time}",
                'doctor': "تأكيد موعد - د. {doctor_name}\n{patient_name} موعدك بتاريخ {date} الساعة {time}"
            },
            'reminder_24h': {
                'clinic': "تذكير موعد - {clinic_name}\n{patient_name} موعدك غداً {date} الساعة {time}",
                'department': "تذكير موعد - {department_name}\n{patient_name} موعدك غداً {date} الساعة {time}", 
                'doctor': "تذكير موعد - د. {doctor_name}\n{patient_name} موعدك غداً {date} الساعة {time}"
            },
            'reminder_2h': {
                'clinic': "تذكير - {clinic_name}\n{patient_name} موعدك بعد ساعتين الساعة {time}",
                'department': "تذكير - {department_name}\n{patient_name} موعدك بعد ساعتين الساعة {time}",
                'doctor': "تذكير - د. {doctor_name}\n{patient_name} موعدك بعد ساعتين الساعة {time}"
            }
        }
    
    def get_template(self, template_type, level='clinic'):
        """الحصول على قالب محدد"""
        return self.templates.get(template_type, {}).get(level, "")
    
    def apply_template(self, template_type, level, variables):
        """تطبيق القالب مع المتغيرات"""
        template = self.get_template(template_type, level)
        try:
            return template.format(**variables)
        except:
            return template