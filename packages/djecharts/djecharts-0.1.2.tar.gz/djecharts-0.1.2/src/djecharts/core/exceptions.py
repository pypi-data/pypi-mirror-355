class InvalidFormError(Exception):
    def __init__(self, form):
        self.form = form
