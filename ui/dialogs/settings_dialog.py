# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QMessageBox, QTabWidget, QWidget, QLabel)
from PyQt5.QtCore import Qt
import logging
import os
import sys

# إضافة المسارات المطلوبة للاستيراد
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

# إضافة جميع المسارات المحتملة
paths_to_add = [
    current_dir,           # مجلد dialogs الحالي
    parent_dir,            # مجلد ui
    project_root,          # المجلد الجذر للمشروع
    os.path.join(project_root, "ui", "components"),  # مسار components المطلوب
    os.path.join(parent_dir, "components")           # مسار بديل
]

for path in paths_to_add:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)

class SettingsDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة إعدادات النظام"""
        self.setWindowTitle("⚙️ إعدادات النظام المتكاملة")
        self.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # تبويبات الإعدادات
        self.tabs = QTabWidget()
        
        # تحميل إدارة الإعدادات العامة
        self.settings_manager = self.load_settings_manager()
        
        if self.settings_manager:
            self.tabs.addTab(self.settings_manager, "⚙️ الإعدادات العامة")
        else:
            error_widget = self.create_fallback_settings("الإعدادات العامة")
            self.tabs.addTab(error_widget, "⚙️ الإعدادات العامة")
        
        # تحميل إعدادات الواتساب المتقدمة
        self.whatsapp_manager = self.load_whatsapp_manager()
        
        if self.whatsapp_manager:
            self.tabs.addTab(self.whatsapp_manager, "📱 إعدادات الواتساب")
        else:
            error_widget = self.create_fallback_settings("إعدادات الواتساب")
            self.tabs.addTab(error_widget, "📱 إعدادات الواتساب")
        
        layout.addWidget(self.tabs)
        
        # أزرار الحفظ والإلغاء
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 حفظ جميع الإعدادات")
        self.save_button.clicked.connect(self.save_all_settings)
        
        self.cancel_button = QPushButton("❌ إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def load_settings_manager(self):
        """تحميل إدارة الإعدادات العامة"""
        try:
            # المحاولة الأولى: من ui.components
            try:
                from ui.components.settings_manager import SettingsManager
                logging.info("✅ تم تحميل SettingsManager من ui.components")
            except ImportError:
                # المحاولة الثانية: من components مباشرة
                try:
                    from components.settings_manager import SettingsManager
                    logging.info("✅ تم تحميل SettingsManager من components")
                except ImportError as e:
                    logging.error(f"❌ فشل في تحميل SettingsManager: {e}")
                    return None
            
            clinics = self.db_manager.get_clinics()
            if clinics:
                clinic_id = clinics[0]['id']
                return SettingsManager(self.db_manager, clinic_id)
            else:
                logging.error("❌ لا توجد عيادات في قاعدة البيانات")
                return None
                
        except Exception as e:
            logging.error(f"❌ فشل في إنشاء SettingsManager: {e}")
            return None
    
    def load_whatsapp_manager(self):
        """تحميل إدارة إعدادات الواتساب"""
        try:
            # المحاولة الأولى: من ui.components
            try:
                from ui.components.whatsapp_settings import WhatsAppSettingsManager
                logging.info("✅ تم تحميل WhatsAppSettingsManager من ui.components")
            except ImportError:
                # المحاولة الثانية: من components مباشرة
                try:
                    from components.whatsapp_settings import WhatsAppSettingsManager
                    logging.info("✅ تم تحميل WhatsAppSettingsManager من components")
                except ImportError as e:
                    logging.error(f"❌ فشل في تحميل WhatsAppSettingsManager: {e}")
                    return None
            
            clinics = self.db_manager.get_clinics()
            if clinics:
                clinic_id = clinics[0]['id']
                return WhatsAppSettingsManager(self.db_manager, clinic_id)
            else:
                logging.error("❌ لا توجد عيادات في قاعدة البيانات")
                return None
                
        except Exception as e:
            logging.error(f"❌ فشل في إنشاء WhatsAppSettingsManager: {e}")
            return None
    
    def create_fallback_settings(self, tab_name):
        """إنشاء واجهة بديلة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        error_label = QLabel(
            f"❌ تعذر تحميل {tab_name}\n\n"
            "الأسباب المحتملة:\n"
            "• الملف المطلوب غير موجود\n"
            "• هناك خطأ في هيكل المشروع\n"
            "• هناك مشكلة في الاستيراد\n\n"
            "الحلول المقترحة:\n"
            "• تأكد من وجود الملفات المطلوبة\n"
            "• تحقق من هيكل المشروع\n"
            "• أعد تشغيل التطبيق"
        )
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #DC3545; font-size: 14px; padding: 20px;")
        
        layout.addWidget(error_label)
        
        return widget
    
    def save_all_settings(self):
        """حفظ جميع الإعدادات"""
        try:
            # حفظ الإعدادات العامة
            if hasattr(self, 'settings_manager') and self.settings_manager:
                if hasattr(self.settings_manager, 'save_all_settings'):
                    self.settings_manager.save_all_settings()
            
            # حفظ إعدادات الواتساب
            if hasattr(self, 'whatsapp_manager') and self.whatsapp_manager:
                if hasattr(self.whatsapp_manager, 'save_all_settings'):
                    self.whatsapp_manager.save_all_settings()
            
            QMessageBox.information(self, "نجاح", "✅ تم حفظ جميع الإعدادات بنجاح")
            self.accept()
                
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ الإعدادات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الإعدادات: {str(e)}")