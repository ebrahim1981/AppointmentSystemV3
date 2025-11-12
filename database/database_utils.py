# -*- coding: utf-8 -*-
import logging
import sqlite3

class DatabaseUtilsMixin:
    """ميكسین الأدوات المساعدة لقاعدة البيانات"""
    
    def clean_phone_number(self, phone, country_code='+966'):
        """تنظيف وتنسيق رقم الهاتف مع رمز الدولة"""
        try:
            # إزالة جميع الأحرف غير الرقمية
            cleaned = ''.join(filter(str.isdigit, str(phone)))
            
            if not cleaned:
                return None
            
            # إذا بدأ الرقم بـ 0، نزيله ونضيف رمز الدولة
            if cleaned.startswith('0'):
                cleaned = cleaned[1:]
            
            # إذا الرقم لا يحتوي على رمز الدولة، نضيفه
            if not cleaned.startswith(country_code.replace('+', '')):
                cleaned = country_code.replace('+', '') + cleaned
            
            return '+' + cleaned
        except Exception as e:
            logging.error(f"❌ خطأ في تنظيف الرقم: {e}")
            return None
    
    def get_country_codes(self):
        """الحصول على رموز الدول المدعومة"""
        return {
            '+966': '🇸🇦 السعودية',
            '+971': '🇦🇪 الإمارات',
            '+973': '🇧🇭 البحرين',
            '+974': '🇶🇦 قطر',
            '+968': '🇴🇲 عمان',
            '+965': '🇰🇼 الكويت',
            '+20': '🇪🇬 مصر',
            '+963': '🇸🇾 سوريا',
            '+962': '🇯🇴 الأردن',
            '+961': '🇱🇧 لبنان',
            '+213': '🇩🇿 الجزائر',
            '+212': '🇲🇦 المغرب',
            '+216': '🇹🇳 تونس',
            '+218': '🇱🇾 ليبيا'
        }

    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn