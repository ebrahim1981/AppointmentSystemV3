# AppointmentSystem/ui/dialogs/widgets/smart_scheduler.py
# -*- coding: utf-8 -*-
"""
نظام الجدولة الذكي - متكامل مع النظام الحالي
يتم استدعاؤه مباشرة من appointment_dialog.py
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

class SmartScheduler(QObject):
    """نظام الجدولة الذكي البسيط والمتكامل"""
    
    # إشارات للتحديثات
    availability_calculated = pyqtSignal(dict)
    smart_suggestions_ready = pyqtSignal(list)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
    def get_doctor_availability(self, doctor_id, date):
        """
        الحصول على أوقات الطبيب المتاحة
        - يعتمد على db_manager الحالي
        - يتكامل مع البيانات الحقيقية
        - يرجع تنسيقاً بسيطاً للعرض
        """
        try:
            self.logger.info(f"🔍 حساب التوفر للطبيب {doctor_id} في {date}")
            
            # 1. جلب المواعيد الحالية من النظام الحالي
            appointments = self.db_manager.get_appointments(
                doctor_id=doctor_id,
                date=date
            )
            
            if appointments is None:
                appointments = []
            
            # 2. توليد الأوقات الأساسية (8 ص - 8 م)
            time_slots = self._generate_time_slots()
            
            # 3. تحديد الأوقات المشغولة
            booked_slots = self._get_booked_slots(appointments)
            
            # 4. تحليل الذكاء البسيط
            smart_analysis = self._analyze_availability_patterns(time_slots, booked_slots, appointments)
            
            result = {
                'success': True,
                'doctor_id': doctor_id,
                'date': date,
                'time_slots': time_slots,
                'booked_slots': booked_slots,
                'available_slots': [slot for slot in time_slots if slot not in booked_slots],
                'smart_analysis': smart_analysis,
                'total_appointments': len(appointments),
                'available_count': len([slot for slot in time_slots if slot not in booked_slots]),
                'booked_count': len(booked_slots)
            }
            
            self.logger.info(f"✅ تم حساب {result['available_count']} وقت متاح من أصل {len(time_slots)}")
            
            # إرسال الإشارة بالنتائج
            self.availability_calculated.emit(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حساب التوفر: {e}")
            return self._get_fallback_result(doctor_id, date)
    
    def _generate_time_slots(self):
        """توليد الأوقات من 8 صباحاً إلى 8 مساءً بفاصل 30 دقيقة"""
        slots = []
        for hour in range(8, 20):  # من 8 ص إلى 8 م
            for minute in ['00', '30']:
                slots.append(f"{hour:02d}:{minute}")
        return slots
    
    def _get_booked_slots(self, appointments):
        """استخراج الأوقات المشغولة من المواعيد"""
        booked_slots = []
        for appointment in appointments:
            status = appointment.get('status', '')
            appointment_time = appointment.get('appointment_time')
            
            # نعتبر الموعد مشغولاً إذا كان مؤكداً أو مجدولاً
            if appointment_time and status in ['مؤكد', 'مجدول', '✅ مؤكد', '🗓️ مجدول']:
                booked_slots.append(appointment_time)
        
        return booked_slots
    
    def _analyze_availability_patterns(self, time_slots, booked_slots, appointments):
        """تحليل بسيط لأنماط التوفر"""
        try:
            analysis = {
                'best_times': [],
                'busy_periods': [],
                'recommendations': []
            }
            
            # تحليل الأوقات المثالية (الأقل ازدحاماً)
            available_slots = [slot for slot in time_slots if slot not in booked_slots]
            
            if available_slots:
                # الأوقات الصباحية عادةً أقل ازدحاماً
                morning_slots = [slot for slot in available_slots if int(slot.split(':')[0]) < 12]
                if morning_slots:
                    analysis['best_times'] = morning_slots[:3]  # أفضل 3 أوقات صباحية
                else:
                    analysis['best_times'] = available_slots[:3]
            
            # تحديد فترات الذروة
            hour_counts = {}
            for slot in booked_slots:
                hour = slot.split(':')[0]
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # الفترات الأكثر ازدحاماً
            if hour_counts:
                busy_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:2]
                analysis['busy_periods'] = [f"{hour}:00-{hour}:59" for hour, count in busy_hours]
            
            # توصيات ذكية بسيطة
            available_count = len(available_slots)
            total_slots = len(time_slots)
            
            if available_count == 0:
                analysis['recommendations'].append("لا توجد أوقات متاحة. جرب تاريخاً آخر.")
            elif available_count <= 3:
                analysis['recommendations'].append("أوقات محدودة متاحة. نوصي بالحجز السريع.")
            elif available_count > total_slots * 0.7:
                analysis['recommendations'].append("أوقات ممتازة متاحة. اليوم هادئ نسبياً.")
            
            # اقتراح الأوقات المبكرة
            early_slots = [slot for slot in available_slots if int(slot.split(':')[0]) <= 10]
            if early_slots:
                analysis['recommendations'].append(f"الأوقات المبكرة ({early_slots[0]}) عادةً ما تكون أفضل.")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التحليل الذكي: {e}")
            return {
                'best_times': [],
                'busy_periods': [],
                'recommendations': ["جاري تحميل البيانات..."]
            }
    
    def _get_fallback_result(self, doctor_id, date):
        """نتيجة احتياطية في حالة الخطأ"""
        return {
            'success': False,
            'doctor_id': doctor_id,
            'date': date,
            'time_slots': [],
            'booked_slots': [],
            'available_slots': [],
            'smart_analysis': {
                'best_times': [],
                'busy_periods': [],
                'recommendations': ["تعذر تحميل البيانات. جرب تحديث الصفحة."]
            },
            'total_appointments': 0,
            'available_count': 0,
            'booked_count': 0
        }
    
    def get_smart_suggestions(self, doctor_id, date, patient_id=None):
        """الحصول على اقتراحات ذكية إضافية"""
        try:
            suggestions = []
            
            # اقتراح 1: بناءً على الوقت الحالي
            current_hour = datetime.now().hour
            if current_hour < 12:
                suggestions.append("⏰ الصباح الباكر أفضل للأوقات الهادئة")
            else:
                suggestions.append("🌅 فكر في مواعيد الصباح للغد")
            
            # اقتراح 2: بناءً على توفر المواعيد
            availability_data = self.get_doctor_availability(doctor_id, date)
            available_count = availability_data.get('available_count', 0)
            
            if available_count > 10:
                suggestions.append("✅ اليوم ممتاز - الكثير من الأوقات المتاحة")
            elif available_count > 5:
                suggestions.append("💡 اليوم جيد - أوقات متاحة مناسبة")
            else:
                suggestions.append("🎯 اليوم مزدحم - اختر الوقت بسرعة")
            
            # إرسال الإشارة بالاقتراحات
            self.smart_suggestions_ready.emit(suggestions)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الاقتراحات الذكية: {e}")
            return ["💡 اختر الوقت المناسب لجدولك"]
    
    def check_appointment_conflict(self, doctor_id, date, time, exclude_appointment_id=None):
        """
        التحقق من تضارب المواعيد
        - يستخدم db_manager الحالي
        - يتكامل مع النظام الحالي
        """
        try:
            appointments = self.db_manager.get_appointments(
                doctor_id=doctor_id,
                date=date
            )
            
            if not appointments:
                return {'conflict': False, 'conflicting_appointment': None}
            
            for appointment in appointments:
                # تخطي الموعد الحالي إذا كان تعديلاً
                if (exclude_appointment_id and 
                    appointment.get('id') == exclude_appointment_id):
                    continue
                
                # التحقق من التضارب في الوقت
                if (appointment.get('appointment_time') == time and 
                    appointment.get('status') in ['مؤكد', 'مجدول', '✅ مؤكد']):
                    
                    return {
                        'conflict': True,
                        'conflicting_appointment': {
                            'id': appointment.get('id'),
                            'patient_name': appointment.get('patient_name', 'مريض'),
                            'patient_phone': appointment.get('patient_phone', ''),
                            'status': appointment.get('status', '')
                        }
                    }
            
            return {'conflict': False, 'conflicting_appointment': None}
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التحقق من التضارب: {e}")
            return {'conflict': False, 'conflicting_appointment': None}

# دالة مساعدة للاستخدام المباشر
def create_smart_scheduler(db_manager):
    """دالة لإنشاء مدير جدولة ذكي"""
    return SmartScheduler(db_manager)

# يمكن استدعاؤها مباشرة من appointment_dialog.py
__all__ = ['SmartScheduler', 'create_smart_scheduler']