import re
from typing import Self
from uuid import uuid4

from django import forms
from django.http import QueryDict
from djecharts.core.utils import class_property


class EChartsFilterForm(forms.Form):
    def __init__(self, *args, **kwargs) -> Self:
        if args and isinstance(args[0], QueryDict):
            for field in args[0]:
                prefixed_field_regex = r"([a-f0-9]{32}).*"
                if match := re.match(prefixed_field_regex, field):
                    self.prefix = match.group(1)

        if not self.prefix:
            # generate a random prefix
            # using uuid4 to avoid conflict.
            self.prefix = uuid4().hex

        super().__init__(*args, **kwargs)

    @class_property
    def id(cls):
        """Returns the form id."""

        return cls.__name__.lower()

    @classmethod
    def as_unique(cls):
        """Returns a new class with a unique id."""

        return type(uuid4().hex, (cls, object), {})

    def get(self, field_name: str):
        """Returns the cleaned value of the field with the provided name."""

        return self.cleaned_data[field_name]
