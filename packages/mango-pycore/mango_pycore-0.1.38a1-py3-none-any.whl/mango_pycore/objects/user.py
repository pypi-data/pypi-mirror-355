class User:
    def __init__(self, username):
        self._username = username
        self._email = ""
        self._full_name = ""
        self._root = False
        self._groups = []
        self.metadata: dict = {}

    def __str__(self):
        return self.username

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        self._full_name = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, value):
        self._root = value

    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name
        }

    def is_anonymous(self):
        return self._username == ''
