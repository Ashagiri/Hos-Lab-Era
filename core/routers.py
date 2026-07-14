class HospitalDatabaseRouter:
    """
    A router to control distributed database operations across 
    the Core Accounts Engine and the Technician/Laboratory Engine.
    """
    route_app_labels = {'laboratory'}

    def db_for_read(self, model, **hints):
        """
        Directs read queries for laboratory models to the laboratory database.
        All other queries route to the default database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Directs write queries for laboratory models to the laboratory database.
        All other writes route to the default database.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allows database relations between models, enabling cross-database
        ForeignKeys (e.g., linking a User to an Appointment).
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Controls where migrations are allowed to run.
        - Laboratory app migrations are isolated STRICTLY to 'lab_db'.
        - Core authorization, content types, and user accounts are allowed on BOTH
          databases so SQLite can perform local tables JOINs cleanly.
        - Everything else goes exclusively to the 'default' database.
        """
        # 1. Isolate laboratory app entirely to lab_db
        if app_label in self.route_app_labels:
            return db == 'lab_db'
        
        # 2. Allow core tables on BOTH databases to resolve SQLite JOIN limitations
        if app_label in {'accounts', 'auth', 'contenttypes'}:
            return True
            
        # 3. Default fallback for admin, sessions, and other system tables
        return db == 'default'