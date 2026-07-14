class HospitalDatabaseRouter:
    """
    A router to control distributed database operations across 
    the Core Accounts Engine and the Technician/Laboratory Engine.
    """
    route_app_labels = {'laboratory'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow laboratory models ONLY on lab_db
        if app_label in self.route_app_labels:
            return db == 'lab_db'
        
        # FIX: Allow core auth/accounts models to exist on BOTH databases 
        # so SQLite can run direct JOIN commands locally without cross-file limits.
        if app_label in {'accounts', 'auth', 'contenttypes'}:
            return True
            
        return db == 'default'