class UserCancelled(Exception):
    def __init__(self, message: str = "User cancelled the operation"):
        super().__init__(message)
