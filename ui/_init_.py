def __init__(self, db_manager, config_manager=None):  # ⭐⭐ تعديل هنا ⭐⭐
    super().__init__()
    self.db_manager = db_manager
    self.config_manager = config_manager  # ⭐⭐ إضافة config_manager ⭐⭐
    self.current_clinic = None
    self.setup_ui()
    self.setup_connections()
    self.load_initial_data()
    self.start_background_services()
    
    # ⭐⭐ تهيئة مدير الواتساب إذا كان config_manager متوفراً ⭐⭐
    if self.config_manager:
        self.initialize_whatsapp_manager(self.config_manager)