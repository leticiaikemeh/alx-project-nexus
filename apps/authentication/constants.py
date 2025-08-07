class Roles:
    ADMIN = 'admin'
    CUSTOMER = 'customer'
    WAREHOUSE = 'warehouse'
    VENDOR = 'vendor'
    STAFF = 'staff'

    @classmethod
    def all(cls):
        return [cls.ADMIN, cls.CUSTOMER, cls.WAREHOUSE, cls.VENDOR, cls.STAFF]

    @classmethod
    def privileged(cls):
        return [cls.ADMIN, cls.STAFF, cls.WAREHOUSE]
