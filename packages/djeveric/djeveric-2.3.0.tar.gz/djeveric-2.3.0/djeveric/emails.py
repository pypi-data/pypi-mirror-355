from django.core.mail import send_mail


class TokenizedModelEmailMixin:
    def __init__(self, *args, initializes_token=True, **kwargs):
        super().__init__(*args, **kwargs)
        if initializes_token:
            self.token = self.get_token()

    def get_token(self):
        return self.instance.make_confirmation_token()


class ModelEmail:
    """
    A confirmation email message
    """

    subject = ""

    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.kwargs = kwargs

    def get_body(self, **kwargs) -> str:
        """Returns the body of the email message.

        @param kwargs: contains at least the key "token"
        @return: a string with the body of the email message
        """
        return ""

    def get_recipient(self) -> str:
        return self.instance.email

    def get_subject(self):
        return self.subject

    def send(self, **kwargs):
        send_mail(
            self.get_subject(),
            self.get_body(**kwargs),
            from_email=None,
            recipient_list=[self.get_recipient()],
        )


class ConfirmationEmail(TokenizedModelEmailMixin, ModelEmail):
    pass
