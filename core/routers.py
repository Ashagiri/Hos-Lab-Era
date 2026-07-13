class HospitalDatabaseRouter:
    """
    A router to control distributed database operations across 
    the Core Accounts Engine and the Technician/Laboratory Engine.
    """
    route_app_labels = {'laboratory'}

    def db_for_read(self, model, **hints):
        # Send laboratory data queries to the specialized laboratory database node
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def db_for_write(self, model, **hints):
        # Direct technician and test inputs straight into laboratory storage
        if model._meta.app_label in self.route_app_labels:
            return 'lab_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow cross-node connections between users and lab results
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Isolate database migration states to their respective node assignments
        if app_label in self.route_app_labels:
            return db == 'lab_db'
        return db == 'default'