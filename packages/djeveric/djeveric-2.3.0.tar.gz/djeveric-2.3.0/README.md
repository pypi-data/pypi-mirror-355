# djeveric

Simple email confirmation for django model instances with 
[Django Rest Framework](https://www.django-rest-framework.org/).

## Usage

### Create a model

Create a model class inheriting from `ConfirmableModelMixin` with a `ConfirmationField` and refer to a 
`ConfirmationEmail` class like this:

```python
from django.conf import settings
from django.db import models

from djeveric.emails import ConfirmationEmail
from djeveric.fields import ConfirmationField
from djeveric.models import ConfirmableModelMixin

class MyModelConfirmationEmail(ConfirmationEmail):
    subject = "Please confirm"
    
    def get_body(self, context):
        return f"Use this link to confirm: http://my-frontend/confirm/{self.token}"
    
    def get_recipient(self) -> str:
        return self.instance.owner.email

class MyModel(ConfirmableModelMixin, models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_confirmed = ConfirmationField(email_class=MyModelConfirmationEmail)
```

When unconfirmed instances of the model are saved, djeveric sends a confirmation email to the specified address.


### Create a ViewSet

To actually confirm a viewset, your backend needs a view set using the `ConfirmModelMixin`:

```python
from rest_framework import viewsets

from djeveric.views import ConfirmModelMixin


class MyModelViewSet(ConfirmModelMixin, viewsets.GenericViewSet):
    queryset = MyModel.objects
```

On a `POST /api/my-models/{pk}/confirm/` with `{"token": "THE TOKEN"}` as data the model instance will be confirmed.
