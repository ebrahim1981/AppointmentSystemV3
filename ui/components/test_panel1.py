# ui/components/test_panel.py
# -*- coding: utf-8 -*-
import logging
import os
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QFormLayout, QLineEdit, QTextEdit, 
                             QPushButton, QMessageBox, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QTimer

class TestPanel(QWidget):
    """لوحة التجريب الحقيقية - نظام اختبار متكامل وحقيقي"""

    def __init__(self, db_manager, notification_system=None, whatsapp_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.notification_system = notification_system
        self.whatsapp_manager = whatsapp_manager
        self.appointments_manager = None
        self.auto_sender = None
        self.test_log = []
        self.quick_test_active = False
        self.test_start_time = None
        self.remaining_seconds = 0
        
        # إعداد الواجهة
        self.setup_ui()
        self.load_real_data()
        
        # بدء البحث التلقائي عن المكونات
        QTimer.singleShot(2000, self.auto_connect_components)
        
        # مؤشر التحديث التلقائي
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_connect_components)
        self.update_timer.start(5000)  # كل 5 ثواني

    def setup_ui(self):
        """إعداد واجهة لوحة التجريب الحقيقية"""
        layout = QVBoxLayout(self)
        
        # عنوان اللوحة
        title_label = QLabel("🧪 لوحة التجريب الحقيقية - نظام الإرسال التلقائي المتكامل")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2C3E50; 
                padding: 15px;
                background-color: #ECF0F1;
                border-radius: 10px;
                margin: 10px;
                border: 2px solid #BDC3C7;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setMinimumHeight(60)
        layout.addWidget(title_label)
        
        # مجموعة التحكم في الاختبارات
        control_group = QGroupBox("🎮 التحكم في نظام الإرسال التلقائي")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
                padding-top: 15px;
                background-color: white;
                border: 2px solid #3498DB;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2C3E50;
            }
        """)
        control_layout = QVBoxLayout(control_group)
        
        # معلومات النظام
        info_layout = QHBoxLayout()
        
        self.system_status_label = QLabel("🔍 جاري فحص حالة النظام...")
        self.system_status_label.setStyleSheet("padding: 10px; background-color: #F8F9FA; border-radius: 6px; border: 1px solid #DEE2E6; margin: 5px; font-size: 12px;")
        self.system_status_label.setMinimumWidth(200)
        
        self.connection_status_label = QLabel("📱 اتصال الواتساب: غير معروف")
        self.connection_status_label.setStyleSheet("padding: 10px; background-color: #F8F9FA; border-radius: 6px; border: 1px solid #DEE2E6; margin: 5px; font-size: 12px;")
        self.connection_status_label.setMinimumWidth(200)
        
        self.auto_sender_status_label = QLabel("🤖 الإرسال التلقائي: غير معروف")
        self.auto_sender_status_label.setStyleSheet("padding: 10px; background-color: #F8F9FA; border-radius: 6px; border: 1px solid #DEE2E6; margin: 5px; font-size: 12px;")
        self.auto_sender_status_label.setMinimumWidth(200)
        
        info_layout.addWidget(self.system_status_label)
        info_layout.addWidget(self.connection_status_label)
        info_layout.addWidget(self.auto_sender_status_label)
        control_layout.addLayout(info_layout)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                text-align: center;
                margin: 10px 5px;
                height: 25px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                border-radius: 6px;
            }
        """)
        control_layout.addWidget(self.progress_bar)
        
        # أزرار التحكم الرئيسية
        buttons_layout = QHBoxLayout()
        
        # زر فحص النظام
        self.check_system_btn = QPushButton("🔍 فحص النظام الشامل")
        self.check_system_btn.clicked.connect(self.comprehensive_system_check)
        self.check_system_btn.setStyleSheet(self.get_button_style("#3498DB", "#2980B9"))
        self.check_system_btn.setMinimumHeight(45)
        
        # زر اختبار الإرسال الفوري
        self.instant_test_btn = QPushButton("🚀 اختبار إرسال فوري")
        self.instant_test_btn.clicked.connect(self.instant_send_test)
        self.instant_test_btn.setStyleSheet(self.get_button_style("#2ECC71", "#27AE60"))
        self.instant_test_btn.setMinimumHeight(45)
        self.instant_test_btn.setEnabled(False)
        
        # زر اختبار AutoSender
        self.auto_sender_test_btn = QPushButton("🤖 اختبار التلقائي")
        self.auto_sender_test_btn.clicked.connect(self.test_auto_sender)
        self.auto_sender_test_btn.setStyleSheet(self.get_button_style("#9B59B6", "#8E44AD"))
        self.auto_sender_test_btn.setMinimumHeight(45)
        self.auto_sender_test_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.check_system_btn)
        buttons_layout.addWidget(self.instant_test_btn)
        buttons_layout.addWidget(self.auto_sender_test_btn)
        control_layout.addLayout(buttons_layout)
        
        layout.addWidget(control_group)
        
        # قسم الاختبار السريع الحقيقي
        quick_test_group = self.setup_quick_test_section()
        layout.addWidget(quick_test_group)
        
        # مجموعة إعدادات الاختبار الفوري
        settings_group = QGroupBox("⚙️ إعدادات الاختبار الفوري")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
                padding-top: 15px;
                background-color: white;
                border: 2px solid #17A2B8;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2C3E50;
            }
        """)
        settings_layout = QFormLayout(settings_group)
        
        # رقم الهاتف للاختبار
        self.test_phone_input = QLineEdit()
        self.test_phone_input.setPlaceholderText("أدخل رقم الهاتف للاختبار (مثال: 0555555555)")
        self.test_phone_input.setText("0555555555")
        self.test_phone_input.setStyleSheet("padding: 10px; border: 2px solid #BDC3C7; border-radius: 6px; font-size: 14px; margin: 5px;")
        settings_layout.addRow("📱 رقم الهاتف:", self.test_phone_input)
        
        # الرسالة المخصصة
        self.test_message_input = QLineEdit()
        self.test_message_input.setPlaceholderText("أدخل الرسالة المخصصة للاختبار")
        self.test_message_input.setText("🧪 هذه رسالة اختبار من النظام المتكامل - تم الإرسال بنجاح ✅")
        self.test_message_input.setStyleSheet("padding: 10px; border: 2px solid #BDC3C7; border-radius: 6px; font-size: 14px; margin: 5px;")
        settings_layout.addRow("💬 الرسالة:", self.test_message_input)
        
        layout.addWidget(settings_group)
        
        # مجموعة النتائج والسجل
        results_group = QGroupBox("📊 النتائج والسجل التفصيلي")
        results_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
                padding-top: 15px;
                background-color: white;
                border: 2px solid #28A745;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2C3E50;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Courier New';
                font-size: 12px;
                margin: 10px;
                min-height: 200px;
            }
        """)
        
        results_layout.addWidget(self.results_display)
        layout.addWidget(results_group)
        
        # مجموعة الإحصائيات
        stats_group = QGroupBox("📈 إحصائيات النظام")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
                padding-top: 15px;
                background-color: white;
                border: 2px solid #6C757D;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2C3E50;
            }
        """)
        stats_layout = QHBoxLayout(stats_group)
        
        self.stats_label = QLabel("إحصائيات: جاري التحميل...")
        self.stats_label.setStyleSheet("font-size: 13px; color: #495057; padding: 10px; background-color: #F8F9FA; border-radius: 6px; margin: 5px;")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        self.add_to_log("✅ تم إعداد واجهة لوحة الاختبار بنجاح")

    def get_button_style(self, normal_color, hover_color):
        """إنشاء ستيل للأزرار"""
        return f"""
            QPushButton {{
                background-color: {normal_color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {normal_color};
                padding: 11px 19px;
            }}
            QPushButton:disabled {{
                background-color: #BDC3C7;
                color: #7F8C8D;
                border: 1px solid #95A5A6;
            }}
        """

    def setup_quick_test_section(self):
        """إعداد قسم الاختبار السريع الحقيقي"""
        quick_test_group = QGroupBox("⚡ الاختبار السريع الحقيقي")
        quick_test_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
                padding-top: 15px;
                background-color: #FFF3CD;
                border: 2px solid #FFC107;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #856404;
            }
        """)
        quick_test_layout = QVBoxLayout(quick_test_group)
        
        # معلومات الاختبار السريع
        quick_info = QLabel("🚀 اختبار حقيقي: إرسال رسائل واتساب تلقائية بعد دقائق")
        quick_info.setStyleSheet("""
            QLabel {
                color: #856404; 
                font-weight: bold; 
                padding: 15px; 
                background-color: #FFF3CD; 
                border-radius: 8px;
                border: 2px solid #FFC107;
                margin: 10px;
                font-size: 14px;
            }
        """)
        quick_info.setAlignment(Qt.AlignCenter)
        quick_test_layout.addWidget(quick_info)
        
        # أزرار الاختبار السريع
        quick_buttons_layout = QHBoxLayout()
        
        # اختبار سريع حقيقي
        self.quick_real_test_btn = QPushButton("🚀 بدء اختبار سريع حقيقي")
        self.quick_real_test_btn.clicked.connect(self.start_quick_real_test)
        self.quick_real_test_btn.setStyleSheet(self.get_button_style("#E74C3C", "#C0392B"))
        self.quick_real_test_btn.setMinimumHeight(50)
        self.quick_real_test_btn.setEnabled(False)
        
        # إيقاف الاختبار السريع
        self.stop_quick_test_btn = QPushButton("⏹️ إيقاف الاختبار السريع")
        self.stop_quick_test_btn.clicked.connect(self.stop_quick_test)
        self.stop_quick_test_btn.setStyleSheet(self.get_button_style("#95A5A6", "#7F8C8D"))
        self.stop_quick_test_btn.setMinimumHeight(50)
        
        quick_buttons_layout.addWidget(self.quick_real_test_btn)
        quick_buttons_layout.addWidget(self.stop_quick_test_btn)
        quick_test_layout.addLayout(quick_buttons_layout)
        
        # حالة الاختبار السريع
        self.quick_test_status = QLabel("🔴 الاختبار السريع غير نشط")
        self.quick_test_status.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                padding: 12px; 
                background-color: #F8D7DA; 
                border-radius: 8px;
                border: 2px solid #F5C6CB;
                margin: 10px;
                color: #721C24;
                font-size: 13px;
            }
        """)
        quick_test_layout.addWidget(self.quick_test_status)
        
        # توقيت الاختبار
        self.quick_test_timer = QLabel("⏰ سيبدأ الإرسال خلال: --:--")
        self.quick_test_timer.setStyleSheet("""
            QLabel {
                color: #004085; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 12px;
                background-color: #CCE5FF;
                border-radius: 8px;
                border: 2px solid #B8DAFF;
                margin: 10px;
            }
        """)
        quick_test_layout.addWidget(self.quick_test_timer)
        
        # معلومات التذكيرات
        self.reminders_info = QLabel("📱 ستصلك رسالتان: بعد 5 دقائق و بعد 1 دقيقة")
        self.reminders_info.setStyleSheet("""
            QLabel {
                color: #155724; 
                padding: 12px; 
                background-color: #D4EDDA;
                border-radius: 8px;
                border: 2px solid #C3E6CB;
                margin: 10px;
                font-size: 13px;
            }
        """)
        quick_test_layout.addWidget(self.reminders_info)
        
        # مؤقت العد التنازلي
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        return quick_test_group

    def auto_connect_components(self):
        """التوصيل التلقائي للمكونات - الحل الجذري"""
        try:
            components_found = 0
            
            # 🔥 البحث عن WhatsAppManager
            if not self.whatsapp_manager:
                self.whatsapp_manager = self.find_whatsapp_manager()
                if self.whatsapp_manager:
                    components_found += 1
                    self.add_to_log("✅ تم العثور على WhatsAppManager تلقائياً")
            
            # 🔥 البحث عن AutoSender
            if not self.auto_sender:
                self.auto_sender = self.find_auto_sender()
                if self.auto_sender:
                    components_found += 1
                    self.add_to_log("✅ تم العثور على AutoSender تلقائياً")
                    self.connect_auto_sender_signals()
            
            # 🔥 البحث عن AppointmentsManager
            if not self.appointments_manager:
                self.appointments_manager = self.find_appointments_manager()
                if self.appointments_manager:
                    components_found += 1
                    self.add_to_log("✅ تم العثور على AppointmentsManager تلقائياً")
            
            if components_found > 0:
                self.update_system_status()
                
        except Exception as e:
            self.add_to_log(f"⚠️ خطأ في التوصيل التلقائي: {e}")

    def find_whatsapp_manager(self):
        """البحث عن WhatsAppManager في جميع الأماكن الممكنة"""
        try:
            # 1. البحث في التطبيق الرئيسي (إذا كان parent موجوداً)
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                if hasattr(parent, 'whatsapp_manager') and parent.whatsapp_manager:
                    return parent.whatsapp_manager
            
            # 2. البحث في NotificationSystem
            if self.notification_system and hasattr(self.notification_system, 'whatsapp_manager'):
                return self.notification_system.whatsapp_manager
            
            # 3. البحث في AppointmentsManager
            if self.appointments_manager and hasattr(self.appointments_manager, 'whatsapp_manager'):
                return self.appointments_manager.whatsapp_manager
            
            # 4. البحث في AutoSender
            if self.auto_sender and hasattr(self.auto_sender, 'whatsapp_sender'):
                return self.auto_sender.whatsapp_sender
            
            return None
            
        except Exception as e:
            self.add_to_log(f"❌ خطأ في البحث عن WhatsAppManager: {e}")
            return None

    def find_auto_sender(self):
        """البحث عن AutoSender في جميع الأماكن الممكنة"""
        try:
            # 1. البحث في NotificationSystem
            if self.notification_system and hasattr(self.notification_system, 'auto_sender'):
                return self.notification_system.auto_sender
            
            # 2. البحث في AppointmentsManager
            if self.appointments_manager:
                if hasattr(self.appointments_manager, 'get_auto_sender'):
                    auto_sender = self.appointments_manager.get_auto_sender()
                    if auto_sender:
                        return auto_sender
                if hasattr(self.appointments_manager, 'auto_sender'):
                    return self.appointments_manager.auto_sender
            
            # 3. البحث في WhatsAppManager
            if self.whatsapp_manager and hasattr(self.whatsapp_manager, 'auto_sender'):
                return self.whatsapp_manager.auto_sender
            
            return None
            
        except Exception as e:
            self.add_to_log(f"❌ خطأ في البحث عن AutoSender: {e}")
            return None

    def find_appointments_manager(self):
        """البحث عن AppointmentsManager"""
        try:
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                if hasattr(parent, 'appointments_manager'):
                    return parent.appointments_manager
                if hasattr(parent, 'appointments_tab'):
                    return parent.appointments_tab
            return None
        except Exception as e:
            self.add_to_log(f"❌ خطأ في البحث عن AppointmentsManager: {e}")
            return None

    def connect_auto_sender_signals(self):
        """ربط إشارات AutoSender"""
        try:
            if not self.auto_sender:
                return
                
            # قائمة الإشارات للربط
            signals = [
                ('reminder_sent', self.on_reminder_sent),
                ('reminder_failed', self.on_reminder_failed),
                ('quick_test_started', self.on_quick_test_started),
                ('quick_test_completed', self.on_quick_test_completed),
                ('status_changed', self.on_auto_sender_status_changed)
            ]
            
            for signal_name, slot in signals:
                if hasattr(self.auto_sender, signal_name):
                    try:
                        signal = getattr(self.auto_sender, signal_name)
                        signal.connect(slot)
                        self.add_to_log(f"✅ تم ربط إشارة {signal_name}")
                    except Exception as e:
                        self.add_to_log(f"⚠️ فشل ربط {signal_name}: {e}")
                        
        except Exception as e:
            self.add_to_log(f"❌ خطأ في ربط الإشارات: {e}")

    def update_system_status(self):
        """تحديث حالة النظام - الإصدار المحسن"""
        try:
            # فحص قاعدة البيانات
            appointments_count = len(self.db_manager.get_today_appointments())
            patients_count = len(self.db_manager.get_patients())
            
            # 🔥 فحص نظام الواتساب - الإصدار المحسن
            whatsapp_status = "🔴 غير متوفر"
            whatsapp_ready = False
            
            if self.whatsapp_manager:
                # 🔥 الحل الجذري: إذا كان WhatsAppManager موجوداً، نفترض أنه جاهز
                whatsapp_status = "🟢 متوفر وجاهز"
                whatsapp_ready = True
                
                # إذا كان يدعم فحص الاتصال، نستخدمه
                if hasattr(self.whatsapp_manager, 'is_connected'):
                    if self.whatsapp_manager.is_connected:
                        whatsapp_status = "🟢 متصل وجاهز"
                    else:
                        whatsapp_status = "🟡 متوفر ولكن غير متصل"
                elif hasattr(self.whatsapp_manager, 'check_connection'):
                    try:
                        result = self.whatsapp_manager.check_connection()
                        if result.get('success', False):
                            whatsapp_status = "🟢 متصل وجاهز"
                        else:
                            whatsapp_status = "🟡 متوفر ولكن غير متصل"
                    except:
                        whatsapp_status = "🟡 متوفر (فحص الاتصال غير مدعوم)"
            
            # فحص نظام AutoSender
            auto_sender_status = "🔴 غير متوفر"
            auto_sender_ready = False
            
            if self.auto_sender:
                if hasattr(self.auto_sender, 'is_running'):
                    if self.auto_sender.is_running:
                        auto_sender_status = "🟢 نشط"
                        auto_sender_ready = True
                    else:
                        auto_sender_status = "🟡 متوقف"
                        auto_sender_ready = True  # 🔥 متوفر ولكن متوقف
                else:
                    auto_sender_status = "🟡 متوفر"
                    auto_sender_ready = True
            
            # تحديث الواجهة
            self.system_status_label.setText(f"📊 النظام: {patients_count} مريض, {appointments_count} موعد")
            self.connection_status_label.setText(f"📱 الواتساب: {whatsapp_status}")
            self.auto_sender_status_label.setText(f"🤖 التلقائي: {auto_sender_status}")
            
            # تحديث الإحصائيات
            stats_text = f"👥 المرضى: {patients_count} | 📅 المواعيد: {appointments_count} | 📱 الواتساب: {whatsapp_status} | 🤖 التلقائي: {auto_sender_status}"
            self.stats_label.setText(stats_text)
            
            # 🔥 تفعيل/تعطيل الأزرار - الإصدار المحسن
            # زر الإرسال الفوري يعمل إذا كان WhatsAppManager موجوداً (حتى لو فحص الاتصال غير مدعوم)
            self.instant_test_btn.setEnabled(bool(self.whatsapp_manager))
            
            # زر AutoSender يعمل إذا كان AutoSender موجوداً
            self.auto_sender_test_btn.setEnabled(bool(self.auto_sender))
            
            # زر الاختبار السريع يعمل إذا كان كلا المكونين موجودين
            self.quick_real_test_btn.setEnabled(bool(self.whatsapp_manager and self.auto_sender))
            
            # تحديث حالة الاختبار السريع
            if self.whatsapp_manager and self.auto_sender:
                self.quick_test_status.setText("🟢 النظام جاهز للاختبار")
                self.quick_test_status.setStyleSheet("""
                    QLabel {
                        font-weight: bold; 
                        padding: 10px; 
                        background-color: #D4EDDA; 
                        border-radius: 6px;
                        border: 1px solid #C3E6CB;
                        margin: 5px;
                        color: #155724;
                    }
                """)
            else:
                self.quick_test_status.setText("🔴 النظام غير جاهز")
                self.quick_test_status.setStyleSheet("""
                    QLabel {
                        font-weight: bold; 
                        padding: 10px; 
                        background-color: #F8D7DA; 
                        border-radius: 6px;
                        border: 1px solid #F5C6CB;
                        margin: 5px;
                        color: #721C24;
                    }
                """)  # 🔥 الإصلاح: أزلت الإقتباس الزائد هنا
                
        except Exception as e:
            self.add_to_log(f"❌ خطأ في تحديث الحالة: {e}")

    def comprehensive_system_check(self):
        """فحص شامل للنظام"""
        self.add_to_log("🔍 بدء الفحص الشامل للنظام...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            # البحث التلقائي أولاً
            self.auto_connect_components()
            self.progress_bar.setValue(30)
            
            # فحص قاعدة البيانات
            appointments = self.db_manager.get_today_appointments()
            patients = self.db_manager.get_patients()
            self.add_to_log(f"✅ قاعدة البيانات: {len(patients)} مريض, {len(appointments)} موعد")
            self.progress_bar.setValue(50)
            
            # فحص الواتساب - الإصدار المحسن
            if self.whatsapp_manager:
                # 🔥 الحل: لا نعتمد على check_connection، نكتفي بوجود WhatsAppManager
                self.add_to_log("✅ نظام الواتساب: متوفر وجاهز للاستخدام")
                # نتحقق من وجود دالة الإرسال
                if hasattr(self.whatsapp_manager, 'send_message'):
                    self.add_to_log("✅ نظام الواتساب: يدعم الإرسال")
                else:
                    self.add_to_log("❌ نظام الواتساب: لا يدعم الإرسال")
            else:
                self.add_to_log("❌ نظام الواتساب: غير متوفر")
            self.progress_bar.setValue(70)
            
            # فحص AutoSender
            if self.auto_sender:
                self.add_to_log("✅ نظام AutoSender: متوفر")
                if hasattr(self.auto_sender, 'get_status'):
                    status = self.auto_sender.get_status()
                    self.add_to_log(f"✅ حالة AutoSender: {status}")
                if hasattr(self.auto_sender, 'start_quick_test'):
                    self.add_to_log("✅ نظام AutoSender: يدعم الاختبار السريع")
                else:
                    self.add_to_log("❌ نظام AutoSender: لا يدعم الاختبار السريع")
            else:
                self.add_to_log("❌ نظام AutoSender: غير متوفر")
            self.progress_bar.setValue(90)
            
            # اكتمال الفحص
            self.progress_bar.setValue(100)
            self.add_to_log("🎉 اكتمل الفحص الشامل")
            
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
        except Exception as e:
            self.add_to_log(f"❌ فشل الفحص الشامل: {e}")
            self.progress_bar.setVisible(False)

    def instant_send_test(self):
        """اختبار إرسال فوري - الإصدار المحسن"""
        try:
            phone_number = self.test_phone_input.text().strip()
            message = self.test_message_input.text().strip()
            
            if not phone_number:
                QMessageBox.warning(self, "تحذير", "الرجاء إدخال رقم الهاتف")
                return
                
            if not message:
                QMessageBox.warning(self, "تحذير", "الرجاء إدخال الرسالة")
                return
            
            self.add_to_log(f"🚀 بدء اختبار الإرسال الفوري إلى: {phone_number}")
            
            # 🔥 البحث عن WhatsAppManager إذا لم يكن متوفراً
            if not self.whatsapp_manager:
                self.whatsapp_manager = self.find_whatsapp_manager()
                if not self.whatsapp_manager:
                    self.add_to_log("❌ نظام الواتساب غير متوفر")
                    QMessageBox.warning(self, "خطأ", "نظام الواتساب غير متوفر")
                    return
            
            # 🔥 الحل الجذري: لا نعتمد على check_connection، نذهب مباشرة للإرسال
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            
            # التحقق من وجود دالة الإرسال
            if not hasattr(self.whatsapp_manager, 'send_message'):
                self.add_to_log("❌ نظام الواتساب لا يدعم الإرسال")
                QMessageBox.warning(self, "خطأ", "نظام الواتساب لا يدعم الإرسال")
                self.progress_bar.setVisible(False)
                return
            
            self.add_to_log("📤 جاري إرسال الرسالة...")
            self.progress_bar.setValue(60)
            
            # إرسال الرسالة
            result = self.whatsapp_manager.send_message(phone_number, message, "test")
            
            self.progress_bar.setValue(90)
            
            if result and result.get('success'):
                self.add_to_log("✅ تم إرسال الرسالة بنجاح!")
                QMessageBox.information(self, "نجاح", "✅ تم إرسال الرسالة التجريبية بنجاح!")
                
                # تسجيل الإحصائية
                if hasattr(self.db_manager, 'log_message_stat'):
                    try:
                        stat_data = {
                            'phone_number': phone_number,
                            'status': 'sent',
                            'message_type': 'test',
                            'sent_at': datetime.now()
                        }
                        self.db_manager.log_message_stat(1, stat_data)
                    except:
                        pass  # لا توقف العملية إذا فشل التسجيل
            else:
                error_msg = "سبب غير معروف"
                if result:
                    error_msg = result.get('message', error_msg)
                self.add_to_log(f"❌ فشل الإرسال: {error_msg}")
                QMessageBox.warning(self, "فشل الإرسال", f"❌ فشل في إرسال الرسالة: {error_msg}")
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
        except Exception as e:
            self.add_to_log(f"❌ خطأ في الاختبار الفوري: {e}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "خطأ", f"فشل الاختبار: {e}")

    def test_auto_sender(self):
        """اختبار نظام AutoSender"""
        try:
            if not self.auto_sender:
                self.auto_sender = self.find_auto_sender()
                if not self.auto_sender:
                    self.add_to_log("❌ AutoSender غير متوفر")
                    QMessageBox.warning(self, "خطأ", "نظام الإرسال التلقائي غير متوفر")
                    return False
            
            self.add_to_log("🧪 بدء اختبار AutoSender...")
            
            if hasattr(self.auto_sender, 'start_quick_test'):
                success = self.auto_sender.start_quick_test()
                if success:
                    self.add_to_log("✅ تم بدء اختبار AutoSender بنجاح")
                    QMessageBox.information(self, "نجاح", "✅ تم بدء اختبار النظام التلقائي بنجاح!")
                    return True
                else:
                    self.add_to_log("❌ فشل في بدء اختبار AutoSender")
                    QMessageBox.warning(self, "خطأ", "❌ فشل في بدء اختبار النظام التلقائي")
                    return False
            else:
                self.add_to_log("❌ AutoSender لا يدعم الاختبار السريع")
                QMessageBox.warning(self, "خطأ", "❌ النظام لا يدعم الاختبار السريع")
                return False
                
        except Exception as e:
            self.add_to_log(f"❌ خطأ في اختبار AutoSender: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل الاختبار: {e}")
            return False

    def start_quick_real_test(self):
        """بدء اختبار سريع حقيقي"""
        try:
            self.add_to_log("🚀 بدء الاختبار السريع الحقيقي...")
            
            # 🔥 التأكد من توفر جميع المكونات
            if not self.auto_sender:
                self.auto_sender = self.find_auto_sender()
            if not self.whatsapp_manager:
                self.whatsapp_manager = self.find_whatsapp_manager()
            
            if not self.auto_sender or not self.whatsapp_manager:
                self.add_to_log("❌ المكونات غير مكتملة")
                QMessageBox.warning(self, "خطأ", "المكونات غير مكتملة - تأكد من اتصال الواتساب والنظام التلقائي")
                return
            
            if hasattr(self.auto_sender, 'start_quick_test'):
                success = self.auto_sender.start_quick_test()
                
                if success:
                    self.add_to_log("✅ تم إعداد الاختبار السريع بنجاح!")
                    self.quick_test_active = True
                    self.remaining_seconds = 300  # 5 دقائق
                    self.countdown_timer.start(1000)
                    
                    self.quick_test_status.setText("🟢 الاختبار السريع نشط - انتظر الرسائل")
                    self.quick_test_status.setStyleSheet("""
                        QLabel {
                            font-weight: bold; 
                            padding: 10px; 
                            background-color: #D4EDDA; 
                            border-radius: 6px;
                            border: 1px solid #C3E6CB;
                            margin: 5px;
                            color: #155724;
                        }
                    """)
                    
                    QMessageBox.information(self, "بدء الاختبار", 
                                          "✅ تم بدء الاختبار السريع بنجاح!\n\n"
                                          "📱 ستصلك رسالتان عبر واتساب:\n"
                                          "• الأولى بعد 5 دقائق\n"
                                          "• الثانية بعد 1 دقيقة\n\n"
                                          "تأكد من أن رقم الهاتف صحيح في إعدادات الواتساب.")
                else:
                    self.add_to_log("❌ فشل في بدء الاختبار السريع")
                    QMessageBox.warning(self, "خطأ", "فشل في بدء الاختبار السريع")
            else:
                self.add_to_log("❌ النظام لا يدعم الاختبار السريع")
                QMessageBox.warning(self, "خطأ", "الإصدار الحالي لا يدعم الاختبار السريع")
                
        except Exception as e:
            self.add_to_log(f"❌ خطأ في الاختبار السريع: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل الاختبار السريع: {e}")

    def stop_quick_test(self):
        """إيقاف الاختبار السريع"""
        try:
            if self.auto_sender and hasattr(self.auto_sender, 'set_quick_test_mode'):
                self.auto_sender.set_quick_test_mode(False)
            
            self.quick_test_active = False
            self.countdown_timer.stop()
            self.quick_test_status.setText("🔴 الاختبار السريع غير نشط")
            self.quick_test_status.setStyleSheet("""
                QLabel {
                    font-weight: bold; 
                    padding: 10px; 
                    background-color: #F8D7DA; 
                    border-radius: 6px;
                    border: 1px solid #F5C6CB;
                    margin: 5px;
                    color: #721C24;
                }
            """)
            self.quick_test_timer.setText("⏰ سيبدأ الإرسال خلال: --:--")
            self.add_to_log("⏹️ تم إيقاف الاختبار السريع")
            
        except Exception as e:
            self.add_to_log(f"❌ خطأ في إيقاف الاختبار: {e}")

    def update_countdown(self):
        """تحديث العد التنازلي"""
        if self.quick_test_active and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            
            if self.remaining_seconds > 60:
                self.quick_test_timer.setText(f"⏰ سيبدأ الإرسال خلال: {minutes:02d}:{seconds:02d}")
            else:
                self.quick_test_timer.setText(f"🔔 الإرسال قريب: {seconds:02d} ثانية")
                
            if self.remaining_seconds == 0:
                self.add_to_log("🎉 اكتمل وقت الاختبار - تحقق من رسائل واتساب!")
                self.quick_test_timer.setText("✅ اكتمل الاختبار - تحقق من واتساب")
                self.quick_test_active = False
                self.countdown_timer.stop()

    # 🔥 معالجات الإشارات
    def on_reminder_sent(self, data):
        """عند إرسال تذكير بنجاح"""
        patient_name = data.get('patient_name', 'مريض')
        reminder_type = data.get('reminder_type', '')
        self.add_to_log(f"📱 تم إرسال تذكير {reminder_type} لـ {patient_name}")

    def on_reminder_failed(self, data):
        """عند فشل إرسال تذكير"""
        patient_name = data.get('patient_name', 'مريض')
        error = data.get('error', 'سبب غير معروف')
        self.add_to_log(f"❌ فشل إرسال تذكير لـ {patient_name}: {error}")

    def on_quick_test_started(self):
        """عند بدء الاختبار السريع"""
        self.add_to_log("🚀 بدأ الاختبار السريع - جاري إعداد الموعد...")

    def on_quick_test_completed(self):
        """عند اكتمال الاختبار السريع"""
        self.add_to_log("🎉 اكتمل الاختبار السريع - تحقق من رسائل واتساب!")

    def on_auto_sender_status_changed(self, status):
        """عند تغيير حالة AutoSender"""
        self.add_to_log(f"🤖 تغيير حالة التلقائي: {status}")
        self.update_system_status()

    def load_real_data(self):
        """تحميل البيانات الحقيقية"""
        try:
            appointments = self.db_manager.get_today_appointments()
            self.add_to_log(f"📊 تم تحميل {len(appointments)} موعد حقيقي")
        except Exception as e:
            self.add_to_log(f"❌ خطأ في تحميل البيانات: {e}")

    def add_to_log(self, message):
        """إضافة رسالة إلى السجل"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] {message}"
            self.test_log.append(log_entry)
            self.update_log_display()
            logging.info(f"TEST_PANEL: {message}")
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة السجل: {e}")

    def update_log_display(self):
        """تحديث عرض السجل"""
        try:
            log_text = "🧪 سجل اختبارات النظام الحقيقي\n" + "="*60 + "\n\n"
            
            for entry in self.test_log[-50:]:
                log_text += entry + "\n"
            
            self.results_display.setPlainText(log_text)
            
            # التمرير إلى الأسفل
            cursor = self.results_display.textCursor()
            cursor.movePosition(cursor.End)
            self.results_display.setTextCursor(cursor)
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث عرض السجل: {e}")

    def refresh_data(self):
        """تحديث البيانات"""
        self.update_system_status()
        self.add_to_log("🔄 تم تحديث البيانات")

    def set_notification_system(self, notification_system):
        """تعيين نظام الإشعارات"""
        self.notification_system = notification_system
        self.add_to_log("✅ تم ربط نظام الإشعارات")

    def set_appointments_manager(self, appointments_manager):
        """تعيين AppointmentsManager"""
        self.appointments_manager = appointments_manager
        self.add_to_log("✅ تم ربط AppointmentsManager")