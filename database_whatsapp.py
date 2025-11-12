# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

class WhatsAppMixin:
    """ميكسین إدارة إعدادات الواتساب والرسائل"""
    
    def get_whatsapp_settings(self, clinic_id):
        """الحصول على إعدادات الواتساب للعيادة"""
        try:
            query = 'SELECT * FROM whatsapp_settings WHERE clinic_id = ? AND is_active = 1'
            cursor = self.conn.cursor()
            cursor.execute(query, (clinic_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إعدادات الواتساب: {e}")
            return None
    
    def save_whatsapp_settings(self, clinic_id, settings_data):
        """حفظ إعدادات الواتساب"""
        try:
            # تعطيل الإعدادات القديمة
            cursor = self.conn.cursor()
            cursor.execute('UPDATE whatsapp_settings SET is_active = 0 WHERE clinic_id = ?', (clinic_id,))
            
            # حفظ الإعدادات الجديدة
            query = '''
                INSERT INTO whatsapp_settings 
                (clinic_id, provider_type, api_key, api_secret, phone_number, country_code, smartwats_template_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            '''
            params = (
                clinic_id,
                settings_data['provider_type'],
                settings_data.get('api_key', ''),
                settings_data.get('api_secret', ''),
                settings_data.get('phone_number', ''),
                settings_data.get('country_code', '+966'),
                settings_data.get('smartwats_template_id', '')
            )
            
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ إعدادات الواتساب: {e}")
            self.conn.rollback()
            return False

    def get_message_templates(self, clinic_id, template_type=None):
        """الحصول على قوالب الرسائل"""
        try:
            if template_type:
                query = 'SELECT * FROM message_templates WHERE clinic_id = ? AND template_type = ? AND is_active = 1 ORDER BY template_name'
                params = (clinic_id, template_type)
            else:
                query = 'SELECT * FROM message_templates WHERE clinic_id = ? AND is_active = 1 ORDER BY template_type, template_name'
                params = (clinic_id,)
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            templates = []
            for row in rows:
                template = dict(row)
                # تحويل variables من JSON إلى list
                if template.get('variables'):
                    try:
                        template['variables'] = json.loads(template['variables'])
                    except:
                        template['variables'] = []
                else:
                    template['variables'] = []
                templates.append(template)
            
            return templates
        except Exception as e:
            logging.error(f"❌ خطأ في جلب القوالب: {e}")
            return []
    
    def save_message_template(self, clinic_id, template_data):
        """حفظ قالب رسالة"""
        try:
            query = '''
                INSERT OR REPLACE INTO message_templates 
                (clinic_id, template_name, template_type, template_content, variables, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            # تحويل variables إلى JSON
            variables_json = json.dumps(template_data.get('variables', []))
            
            params = (
                clinic_id,
                template_data['template_name'],
                template_data['template_type'],
                template_data['template_content'],
                variables_json,
                1
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ القالب: {e}")
            self.conn.rollback()
            return None

    def log_message_stat(self, clinic_id, stat_data):
        """تسجيل إحصائية رسالة"""
        try:
            query = '''
                INSERT INTO message_stats 
                (clinic_id, patient_id, appointment_id, message_type, phone_number, country_code, status, provider, error_message, sent_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                clinic_id,
                stat_data.get('patient_id'),
                stat_data.get('appointment_id'),
                stat_data.get('message_type'),
                stat_data.get('phone_number'),
                stat_data.get('country_code'),
                stat_data.get('status'),
                stat_data.get('provider'),
                stat_data.get('error_message', ''),
                stat_data.get('sent_at', datetime.now()),
                datetime.now()
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في تسجيل الإحصائية: {e}")
            return False
    
    def get_message_stats(self, clinic_id, days=30):
        """الحصول على إحصائيات الرسائل - مصححة"""
        try:
            query = '''
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_messages,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_messages,
                    provider,
                    message_type
                FROM message_stats 
                WHERE clinic_id = ? AND date(created_at) >= date('now', ?)
                GROUP BY provider, message_type
            '''
            params = (clinic_id, f'-{days} days')
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            stats = {
                'total_messages': 0,
                'sent_messages': 0,
                'failed_messages': 0,
                'providers': {},
                'types': {}
            }
            
            for row in rows:
                row_dict = dict(row)
                stats['total_messages'] += row_dict['total_messages']
                stats['sent_messages'] += row_dict['sent_messages']
                stats['failed_messages'] += row_dict['failed_messages']
                
                provider = row_dict['provider'] or 'unknown'
                message_type = row_dict['message_type'] or 'unknown'
                
                if provider not in stats['providers']:
                    stats['providers'][provider] = 0
                stats['providers'][provider] += row_dict['total_messages']
                
                if message_type not in stats['types']:
                    stats['types'][message_type] = 0
                stats['types'][message_type] += row_dict['total_messages']
            
            return stats
        except Exception as e:
            logging.error(f"❌ خطأ في جلب الإحصائيات: {e}")
            return None