
class Owner:

    def __init__(self, fname: str, lname: str, username: str, email: str, password: str):

        self.fname = fname
        self.lname = lname
        self.name = self.fname + " " + self.lname
        self.username = username
        self.email = email
        self.password = password

    def change_password(self, password: str):

        self.password = password

    def change_email(self, email: str):

        self.email = email

