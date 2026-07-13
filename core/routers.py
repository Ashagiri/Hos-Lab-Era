class HospitalDatabaseRouter:
    """
    A router to control all distributed database operations 
    across the Primary cluster and Technician Replicas.
    """
    def db_for_read(self, model, **hints):
        # Route reading operations to the replica node to save bandwidth
        return 'technician_read'

    def db_for_write(self, model, **hints):
        # All data commits (saving test entries) go exclusively to primary
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True