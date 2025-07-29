"""
Formable
Copyright (c) 2025 Juan-Pablo Scaletti
"""

import typing as t
from collections.abc import Iterable

from .. import errors as err
from .base import Field


if t.TYPE_CHECKING:
    from ..form import Form


def get_pk(obj: t.Any, pk: str) -> t.Any:  # pragma: no cover
    """
    Helper function to get the primary key from an object.
    """
    if isinstance(obj, dict):
        value = obj.get(pk, None)
    else:
        value = getattr(obj, pk, None)
    if value is None:
        return None
    return str(value)


class FormSet(Field):
    def __init__(
        self,
        FormClass: "type[Form]",
        *,
        min_items: int | None = None,
        max_items: int | None = None,
        default: t.Any = None,
        allow_delete: bool = True,
    ):
        """
        A field that represents a set of forms, allowing for dynamic addition and removal of forms.

        Args:
            FormClass:
                The class of the form to be used as a sub-form.
            min_items:
                Minimum number of form in the set. Defaults to None (no minimum).
            max_items:
                Maximum number of form in the set. Defaults to None (no maximum).
            default:
                Default value for the field. Defaults to `None`.
            allow_delete:
                Whether the form allows deletion of objects.
                If set to `True`, the form will delete objects of form when the "_deleted"
                field is present. Defaults to `True`.

        """
        self.FormClass = FormClass
        self.new_form = FormClass()

        self.forms = []
        self.pk = getattr(self.new_form.Meta, "pk", "id")

        if min_items is not None and (not isinstance(min_items, int) or min_items < 0):
            raise ValueError("`min_items` must be a positive integer")
        self.min_items = min_items

        if max_items is not None and (not isinstance(max_items, int) or max_items < 0):
            raise ValueError("`max_items` must be a positive integer")
        self.max_items = max_items

        self.allow_delete = bool(allow_delete)

        super().__init__(
            required=bool(min_items),
            default=default,
            messages={**self.new_form._messages}
        )
        self.set_name_format(self.name_format)

    def set_name_format(self, name_format: str):
        self.name_format = f"{name_format}[NEW_RECORD]"
        self.sub_name_format = f"{self.name}[{{name}}]"
        self.new_form._set_name_format(self.sub_name_format)

    def set_messages(self, messages: dict[str, str]):
        super().set_messages(messages)
        self.new_form._set_messages(self.messages)

    def set(
        self,
        reqvalue: dict[str, t.Any] | None = None,
        objvalue: Iterable[t.Any] | None = None,
    ):
        self.error = None
        self.error_args = None

        reqvalue = reqvalue or {}
        assert isinstance(reqvalue, dict), "reqvalue must be a dictionary"
        objvalue = objvalue or []
        assert isinstance(objvalue, Iterable), "objvalue must be an iterable"
        if not (reqvalue or objvalue):
            reqvalue = self.default_value or {}

        self.forms = []
        pks_used = set()

        if reqvalue:
            objects = {get_pk(obj, self.pk): obj for obj in objvalue}
            for pk, data in reqvalue.items():
                name_format = self.sub_name_format.replace("NEW_RECORD", pk)
                form = self.FormClass(
                    data,
                    object=objects.get(pk),
                    name_format=name_format,
                    messages=self.messages,
                )
                form._allow_delete = self.allow_delete
                self.forms.append(form)
                pks_used.add(pk)

        if objvalue:
            for obj in objvalue:
                pk = get_pk(obj, self.pk)
                if pk in pks_used:
                    continue
                name_format = self.sub_name_format.replace("NEW_RECORD", str(pk))
                form = self.FormClass(
                    object=obj,
                    name_format=name_format,
                    messages=self.messages,
                )
                form._allow_delete = self.allow_delete
                self.forms.append(form)

    def save(self) -> list[t.Any]:
        """
        Save the forms in the formset and return a list of the results.
        """
        results = []
        for form in self.forms:
            result = form.save()
            if result is None:
                continue
            results.append(result)
        return results

    def validate_value(self) -> bool:
        """
        Validate the field value against the defined constraints.
        """
        if self.min_items is not None and len(self.forms) < self.min_items:
            self.error = err.MIN_ITEMS
            self.error_args = {"min_items": self.min_items}
            return False

        if self.max_items is not None and len(self.forms) > self.max_items:
            self.error = err.MAX_ITEMS
            self.error_args = {"max_items": self.max_items}
            return False

        return True
