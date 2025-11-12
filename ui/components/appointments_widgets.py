# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QDate
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtPrintSupport import QPrinter
import logging
from datetime import datetime, timedelta
import os
import shutil
import csv

class BackupManager:
    """مدير النسخ الاحتياطي"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.last_backup = None
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            # نسخ قاعدة البيانات
            if os.path.exists(self.db_manager.db_path):
                shutil.copy2(self.db_manager.db_path, backup_file)
                logging.info(f"✅ تم إنشاء نسخة احتياطية: {backup_file}")
                return True
            return False
        except Exception as e:
            logging.error(f"❌ خطأ في النسخ الاحتياطي: {e}")
            return False
    
    def auto_backup(self):
        """نسخ احتياطي تلقائي"""
        if self.last_backup:
            # نسخ احتياطي مرة واحدة يومياً
            if (datetime.now() - self.last_backup).days < 1:
                return
        self.create_backup()
        self.last_backup = datetime.now()

class NotificationManager:
    """مدير الإشعارات والتذكيرات"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.tray_icon = None
        self.setup_tray_icon()
    
    def setup_tray_icon(self):
        """إعداد أيقونة النظام"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setIcon(QApplication.windowIcon())
            self.tray_icon.show()
    
    def show_notification(self, title, message, timeout=5000):
        """عرض إشعار"""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, timeout)
        else:
            logging.info(f"📢 {title}: {message}")
    
    def check_reminders(self):
        """التحقق من التذكيرات"""
        try:
            # مواعيد اليوم
            today = QDate.currentDate().toString("yyyy-MM-dd")
            appointments = self.db_manager.get_appointments(date=today, status="✅ مؤكد")
            
            for appointment in appointments:
                # تذكير قبل ساعتين
                appointment_time = datetime.strptime(appointment.get('appointment_time', '00:00'), '%H:%M')
                reminder_time = appointment_time - timedelta(hours=2)
                current_time = datetime.now().time()
                
                if (reminder_time.time() <= current_time <= appointment_time.time() and 
                    not appointment.get('reminder_sent', False)):
                    
                    patient_name = appointment.get('patient_name', '')
                    self.show_notification(
                        "⏰ تذكير موعد",
                        f"موعد مع {patient_name} بعد ساعتين الساعة {appointment.get('appointment_time', '')}"
                    )
                    
                    # تحديث حالة التذكير
                    self.db_manager.update_appointment_reminder(appointment['id'], True)
            
        except Exception as e:
            logging.error(f"❌ خطأ في التحقق من التذكيرات: {e}")

class ExportWorker(QThread):
    """عامل التصدير في خلفية"""
    progress_updated = pyqtSignal(int)
    export_finished = pyqtSignal(str, bool)
    
    def __init__(self, data, export_type, filename):
        super().__init__()
        self.data = data
        self.export_type = export_type
        self.filename = filename
    
    def run(self):
        """تنفيذ التصدير"""
        try:
            if self.export_type == "excel":
                success = self.export_to_excel()
            else:
                success = self.export_to_pdf()
            
            self.export_finished.emit(self.filename, success)
        except Exception as e:
            logging.error(f"❌ خطأ في التصدير: {e}")
            self.export_finished.emit(str(e), False)
    
    def export_to_excel(self):
        """التصدير لإكسل"""
        try:
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # كتابة العناوين
                headers = ["ID", "المريض", "الهاتف", "الطبيب", "التاريخ", "الوقت", "الحالة", "الملاحظات"]
                writer.writerow(headers)
                
                # كتابة البيانات
                for i, row in enumerate(self.data):
                    writer.writerow([
                        row.get('id', ''),
                        row.get('patient_name', ''),
                        row.get('patient_phone', ''),
                        row.get('doctor_name', ''),
                        row.get('appointment_date', ''),
                        row.get('appointment_time', ''),
                        row.get('status', ''),
                        row.get('notes', '')
                    ])
                    self.progress_updated.emit(int((i + 1) / len(self.data) * 100))
            
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في التصدير لإكسل: {e}")
            return False
    
    def export_to_pdf(self):
        """التصدير لPDF"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(self.filename)
            
            # بدء الطباعة
            painter = QPainter()
            if painter.begin(printer):
                # رسم المحتوى (مبسط)
                painter.drawText(100, 100, "تقرير المواعيد")
                y = 150
                for appointment in self.data:
                    text = f"{appointment.get('patient_name', '')} - {appointment.get('appointment_date', '')}"
                    painter.drawText(100, y, text)
                    y += 30
                    if y > 700:  # صفحة جديدة
                        printer.newPage()
                        y = 100
                
                painter.end()
            
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في التصدير لPDF: {e}")
            return False

class Helpers:
    """دوال المساعدة"""
    
    @staticmethod
    def darken_color(color, amount=20):
        """تغميق اللون"""
        try:
            color = QColor(color)
            return color.darker(100 + amount).name()
        except:
            return color
    
    @staticmethod
    def format_phone_display(phone, country_code):
        """تنسيق عرض رقم الهاتف"""
        try:
            if not phone:
                return "غير متوفر"
            
            # رموز الدول وأعلامها
            country_flags = {
                '+966': '🇸🇦',
                '+971': '🇦🇪', 
                '+973': '🇧🇭',
                '+974': '🇶🇦',
                '+968': '🇴🇲',
                '+965': '🇰🇼',
                '+20': '🇪🇬',
                '+963': '🇸🇾',
                '+962': '🇯🇴'
            }
            
            flag = country_flags.get(country_code, '🌐')
            return f"{flag} {phone}"
            
        except Exception as e:
            logging.error(f"❌ خطأ في تنسيق الرقم: {e}")
            return phone
    
    @staticmethod
    def create_manual_backup(parent):
        """إنشاء نسخة احتياطية يدوية"""
        try:
            success = parent.backup_manager.create_backup()
            if success:
                QMessageBox.information(parent, "نجاح", "✅ تم إنشاء نسخة احتياطية بنجاح")
            else:
                QMessageBox.warning(parent, "تحذير", "⚠️ فشل في إنشاء نسخة احتياطية")
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"❌ خطأ في النسخ الاحتياطي: {e}")
    
    @staticmethod
    def on_report_period_changed(parent, text):
        """عند تغيير فترة التقرير"""
        if text == "مخصص":
            parent.report_start_date.setEnabled(True)
            parent.report_end_date.setEnabled(True)
        else:
            parent.report_start_date.setEnabled(False)
            parent.report_end_date.setEnabled(False)
    
    @staticmethod
    def generate_report(parent):
        """توليد تقرير"""
        try:
            period = parent.report_period.currentText()
            start_date = parent.report_start_date.date().toString("yyyy-MM-dd")
            end_date = parent.report_end_date.date().toString("yyyy-MM-dd")
            
            # توليد التقرير
            appointments = parent.db_manager.get_appointments()
            report_data = []
            
            # تحليل البيانات الأساسية
            total = len(appointments)
            confirmed = len([a for a in appointments if a.get('status') == '✅ مؤكد'])
            completed = len([a for a in appointments if a.get('status') == 'حاضر'])
            cancelled = len([a for a in appointments if a.get('status') == 'ملغى'])
            
            success_rate = (completed / total * 100) if total > 0 else 0
            
            report_data.append([
                f"{start_date} إلى {end_date}",
                total,
                confirmed,
                completed,
                cancelled,
                f"{success_rate:.1f}%"
            ])
            
            Helpers.display_report(parent, report_data)
            
        except Exception as e:
            logging.error(f"❌ خطأ في توليد التقرير: {e}")
            QMessageBox.critical(parent, "خطأ", f"فشل في توليد التقرير: {e}")
    
    @staticmethod
    def display_report(parent, report_data):
        """عرض البيانات في جدول التقارير"""
        parent.reports_table.setRowCount(len(report_data))
        
        for row, data in enumerate(report_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                parent.reports_table.setItem(row, col, item)
    
    @staticmethod
    def export_to_excel(parent):
        """تصدير البيانات لإكسل"""
        try:
            if not parent.all_appointments:
                QMessageBox.warning(parent, "تحذير", "⚠️ لا توجد بيانات للتصدير")
                return
            
            filename, _ = QInputDialog.getText(parent, "تصدير لإكسل", "أدخل اسم الملف:", text="مواعيد.xlsx")
            if not filename:
                return
            
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # التصدير في خلفية
            parent.export_worker = ExportWorker(parent.all_appointments, "excel", filename)
            parent.export_worker.progress_updated.connect(parent.on_export_progress)
            parent.export_worker.export_finished.connect(parent.on_export_finished)
            parent.export_worker.start()
            
            QMessageBox.information(parent, "جاري التصدير", "📤 جاري تصدير البيانات لإكسل...")
            
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"❌ فشل في التصدير: {e}")
    
    @staticmethod
    def export_to_pdf(parent):
        """تصدير البيانات لPDF"""
        try:
            if not parent.all_appointments:
                QMessageBox.warning(parent, "تحذير", "⚠️ لا توجد بيانات للتصدير")
                return
            
            filename, _ = QInputDialog.getText(parent, "تصدير لPDF", "أدخل اسم الملف:", text="تقرير_المواعيد.pdf")
            if not filename:
                return
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # التصدير في خلفية
            parent.export_worker = ExportWorker(parent.all_appointments, "pdf", filename)
            parent.export_worker.progress_updated.connect(parent.on_export_progress)
            parent.export_worker.export_finished.connect(parent.on_export_finished)
            parent.export_worker.start()
            
            QMessageBox.information(parent, "جاري التصدير", "📄 جاري تصدير البيانات لPDF...")
            
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"❌ فشل في التصدير: {e}")