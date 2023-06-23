class User:


    def __init__(self, name, password):
        self.authenticated = False
        self.name = name
        self.password = password


    def is_authenticated(self):
        return self.authenticated


    def is_active(self):
        return True


    def is_anonymous(self):
        return False


    def get_id(self):
        return self.name
