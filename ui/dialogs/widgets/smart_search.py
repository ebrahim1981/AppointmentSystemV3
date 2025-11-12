# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QLabel, QHBoxLayout, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import re
import logging

class SmartSearchComboBox(QWidget):
    """مربع بحث ذكي محسّن - إصدار مضغوط"""
    selection_changed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.selected_item = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.current_search_type = "smart"
        
        self.setup_compact_ui()
    
    def setup_compact_ui(self):
        """إعداد واجهة مضغوطة"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # تقليل الهوامش
        layout.setSpacing(4)  # تقليل المسافات
        
        # شريط البحث المضغوط
        search_layout = QHBoxLayout()
        
        # حقل البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم المريض...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """)
        
        # زر المسح
        self.clear_button = QLabel("🗑️")
        self.clear_button.setToolTip("مسح البحث")
        self.clear_button.setStyleSheet("""
            QLabel {
                padding: 4px 6px;
                background-color: #95A5A6;
                color: white;
                border-radius: 3px;
                font-size: 10px;
                min-width: 20px;
                max-width: 20px;
            }
            QLabel:hover {
                background-color: #7F8C8D;
            }
        """)
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.mousePressEvent = lambda e: self.clear()
        
        # خيارات البحث
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItem("ذكي", "smart")
        self.search_mode_combo.addItem("دقيق", "exact")
        self.search_mode_combo.addItem("هاتف", "phone")
        self.search_mode_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 6px;
                border: 1px solid #BDC3C7;
                border-radius: 3px;
                font-size: 11px;
                max-width: 70px;
                min-height: 20px;
            }
        """)
        self.search_mode_combo.currentTextChanged.connect(self.on_search_mode_changed)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(self.search_mode_combo)
        layout.addLayout(search_layout)
        
        # تلميح البحث
        self.search_hints = QLabel("💡 اكتب حرفين للبحث")
        self.search_hints.setStyleSheet("color: #7F8C8D; font-size: 10px; padding: 1px;")
        self.search_hints.setVisible(False)
        layout.addWidget(self.search_hints)
        
        # قائمة النتائج المضغوطة
        self.results_list = QListWidget()
        self.results_list.setVisible(False)
        self.results_list.itemClicked.connect(self.on_item_selected)
        self.results_list.setMaximumHeight(120)  # تقليل الارتفاع
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 3px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid #ECF0F1;
                min-height: 18px;
            }
            QListWidget::item:hover {
                background-color: #3498DB;
                color: white;
            }
        """)
        layout.addWidget(self.results_list)
        
        # عد النتائج
        self.results_count = QLabel()
        self.results_count.setStyleSheet("color: #27AE60; font-size: 10px; padding: 2px;")
        self.results_count.setVisible(False)
        layout.addWidget(self.results_count)
        
        # عرض المريض المختار (مضغوط)
        self.selected_patient_frame = QWidget()
        self.selected_patient_frame.setVisible(False)
        self.selected_patient_frame.setStyleSheet("""
            QWidget {
                background-color: #E8F6F3;
                border: 1px solid #27AE60;
                border-radius: 3px;
                padding: 6px;
                margin-top: 2px;
            }
        """)
        
        selected_layout = QHBoxLayout(self.selected_patient_frame)  # تغيير إلى أفقي
        self.selected_title = QLabel("✅ مختار:")
        self.selected_title.setStyleSheet("font-weight: bold; color: #27AE60; font-size: 11px;")
        self.selected_info = QLabel()
        self.selected_info.setStyleSheet("color: #2C3E50; font-size: 11px;")
        selected_layout.addWidget(self.selected_title)
        selected_layout.addWidget(self.selected_info)
        selected_layout.addStretch()
        layout.addWidget(self.selected_patient_frame)

    def on_search_mode_changed(self):
        """عند تغيير نمط البحث"""
        self.current_search_type = self.search_mode_combo.currentData()
        placeholders = {
            "smart": "ابحث باسم المريض...",
            "exact": "الاسم الكامل...", 
            "phone": "رقم الهاتف..."
        }
        self.search_input.setPlaceholderText(placeholders.get(self.current_search_type, "ابحث..."))
        if self.search_input.text().strip():
            self.on_search_changed(self.search_input.text())
    
    def on_search_changed(self, text):
        """عند تغيير نص البحث"""
        text = text.strip()
        
        self.search_hints.setVisible(len(text) > 0 and len(text) < 3)
        
        if len(text) == 0:
            self.results_list.setVisible(False)
            self.results_count.setVisible(False)
            return
        
        if len(text) < 2:
            self.results_list.setVisible(False)
            return
        
        # تأخير البحث
        self.search_timer.stop()
        self.search_timer.start(300)  # تقليل وقت التأخير
    
    def perform_search(self):
        """تنفيذ البحث"""
        search_text = self.search_input.text().strip()
        if len(search_text) < 2:
            return
        
        results = []
        search_lower = search_text.lower()
        
        for item in self.items:
            if self.item_matches_search(item, search_lower, self.current_search_type):
                results.append(item)
        
        self.show_results(results, search_text)
    
    def item_matches_search(self, item, search_term, search_type):
        """التحقق من مطابقة العنصر للبحث"""
        name = item.get('name', '').lower()
        phone = item.get('phone', '').lower()
        
        clean_phone = re.sub(r'[\s\-+]', '', phone)
        clean_search = re.sub(r'[\s\-+]', '', search_term)
        
        if search_type == "exact":
            return search_term in name
            
        elif search_type == "phone":
            return (clean_phone.startswith(clean_search) or 
                   clean_search in clean_phone)
        
        else:  # smart
            return (search_term in name or
                   any(word.startswith(search_term) for word in name.split()) or
                   clean_phone.startswith(clean_search) or
                   clean_search in clean_phone)
    
    def show_results(self, results, search_text):
        """عرض نتائج البحث"""
        self.results_list.clear()
        
        # ترتيب النتائج
        sorted_results = self.sort_search_results(results, search_text)
        
        for item in sorted_results[:6]:  # تقليل عدد النتائج المعروضة
            display_text = f"{item['name']} - {item.get('phone', '')}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item)
            self.results_list.addItem(list_item)
        
        # عرض العد
        results_count = len(sorted_results)
        self.results_count.setText(f"🎯 {results_count} نتيجة")
        self.results_count.setVisible(True)
        
        self.results_list.setVisible(results_count > 0)
    
    def sort_search_results(self, results, search_text):
        """ترتيب نتائج البحث"""
        search_lower = search_text.lower()
        
        def sort_key(item):
            name = item.get('name', '').lower()
            phone = item.get('phone', '').lower()
            score = 0
            
            if name == search_lower:
                score += 100
            elif name.startswith(search_lower):
                score += 50
            elif any(word.startswith(search_lower) for word in name.split()):
                score += 40
            elif phone == search_lower:
                score += 30
            elif phone.startswith(search_lower):
                score += 20
            elif search_lower in name:
                score += 10
            
            return -score
            
        return sorted(results, key=sort_key)
    
    def on_item_selected(self, item):
        """عند اختيار عنصر من النتائج"""
        try:
            selected_data = item.data(Qt.UserRole)
            if selected_data and 'id' in selected_data and 'name' in selected_data:
                self.selected_item = selected_data
                
                # تحديث واجهة المستخدم
                display_text = f"{selected_data['name']} - {selected_data.get('phone', '')}"
                self.search_input.setText(display_text)
                self.results_list.setVisible(False)
                
                # عرض المريض المختار
                self.selected_info.setText(f"{selected_data['name']} - {selected_data.get('phone', 'لا يوجد')}")
                self.selected_patient_frame.setVisible(True)
                
                # إرسال إشارة الاختيار
                self.selection_changed.emit(selected_data)
                logging.info(f"✅ تم اختيار المريض: {selected_data['name']}")
            else:
                logging.error("❌ بيانات المريض المختار غير مكتملة")
                self.clear_selection()
        except Exception as e:
            logging.error(f"❌ خطأ في اختيار المريض: {e}")
            self.clear_selection()
    
    def set_items(self, items):
        """تعيين العناصر للبحث"""
        self.items = items
    
    def get_selected_data(self):
        """الحصول على البيانات المحددة"""
        return self.selected_item
    
    def clear(self):
        """مسح الحقل والاختيار"""
        self.search_input.clear()
        self.results_list.setVisible(False)
        self.results_count.setVisible(False)
        self.search_hints.setVisible(False)
        self.clear_selection()
    
    def clear_selection(self):
        """مسح الاختيار الحالي"""
        self.selected_item = None
        self.selected_patient_frame.setVisible(False)
        self.selection_changed.emit(None)
    
    def set_selected_patient(self, patient_data):
        """تعيين مريض محدد (للاستخدام في وضع التعديل)"""
        if patient_data and 'id' in patient_data and 'name' in patient_data:
            self.selected_item = patient_data
            display_text = f"{patient_data['name']} - {patient_data.get('phone', '')}"
            self.search_input.setText(display_text)
            self.selected_info.setText(f"{patient_data['name']} - {patient_data.get('phone', 'لا يوجد')}")
            self.selected_patient_frame.setVisible(True)