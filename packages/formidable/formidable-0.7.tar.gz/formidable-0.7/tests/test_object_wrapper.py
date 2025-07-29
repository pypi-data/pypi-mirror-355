"""
Formable
Copyright (c) 2025 Juan-Pablo Scaletti
"""

from unittest.mock import MagicMock

import formidable as f


class Object:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.delete_instance = MagicMock(return_value=None)

    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)


def test_create_object():
    class ProductForm(f.Form):
        class Meta:
            orm_cls = Object

        name = f.TextField()
        price = f.FloatField(gt=0)


    form = ProductForm({
        "name": ["Test Product"],
        "price": ["10.0"],
    })

    form.validate()
    assert form.is_valid
    obj = form.save()

    assert isinstance(obj, Object)
    assert obj.name == "Test Product"  # type: ignore
    assert obj.price == 10.0  # type: ignore


def test_update_object():
    class ProductForm(f.Form):
        name = f.TextField()
        price = f.FloatField(gt=0)


    existing_obj = Object(name="Old Product", price=5.0)
    form = ProductForm(
        {
            "name": ["Updated Product"],
            "price": ["15.0"],
        },
        object=existing_obj
    )

    form.validate()
    assert form.is_valid
    updated_obj = form.save()

    assert updated_obj is existing_obj
    assert updated_obj.name == "Updated Product"
    assert updated_obj.price == 15.0


def test_delete_object():
    class ChildForm(f.Form):
        class Meta:
            orm_cls = Object

        name = f.TextField()

    class ProductForm(f.Form):
        tags = f.FormSet(ChildForm)

    tag1 = Object(id=3, name="cool")
    tag2 = Object(id=6, name="new")
    tag3 = Object(id=9, name="awesome")
    existing_obj = Object(name="Test Product", tags=[tag1, tag2, tag3])

    form = ProductForm(
        {
            "tags[3][name]": ["cool"],
            f"tags[6][{f.DELETED}]": ["1"],
            "tags[6][name]": ["meh"],
            "tags[9][name]": ["awesome"],
        },
        object=existing_obj
    )

    form.validate()
    assert form.is_valid
    updated_obj = form.save()

    tag2.delete_instance.assert_called_once()
    print(updated_obj.tags)
    assert updated_obj.tags == [tag1, tag3]


def test_delete_not_allowed():
    class ChildForm(f.Form):
        name = f.TextField()

    class ProductForm(f.Form):
        tags = f.FormSet(ChildForm, allow_delete=False)

    tag1 = Object(id=3, name="cool")
    tag2 = Object(id=6, name="new")
    tag3 = Object(id=9, name="awesome")
    existing_obj = Object(name="Test Product", tags=[tag1, tag2, tag3])

    form = ProductForm(
        {
            "tags[3][name]": ["cool"],
            f"tags[6][{f.DELETED}]": ["1"],
            "tags[6][name]": ["meh"],
            "tags[9][name]": ["awesome"],
        },
        object=existing_obj
    )

    form.validate()
    assert form.is_valid
    updated_obj = form.save()

    tag2.delete_instance.assert_not_called()
    print(updated_obj.tags)
    assert updated_obj.tags == [tag1, tag2, tag3]


def test_empty_delete_field_is_no_delete():
    class ChildForm(f.Form):
        name = f.TextField()

    class ProductForm(f.Form):
        tags = f.FormSet(ChildForm, allow_delete=False)

    tag1 = Object(id=3, name="cool")
    tag2 = Object(id=6, name="new")
    tag3 = Object(id=9, name="awesome")
    existing_obj = Object(name="Test Product", tags=[tag1, tag2, tag3])

    form = ProductForm(
        {
            "tags[3][name]": ["cool"],
            f"tags[6][{f.DELETED}]": [""],
            "tags[6][name]": ["meh"],
            "tags[9][name]": ["awesome"],
        },
        object=existing_obj
    )

    form.validate()
    assert form.is_valid
    updated_obj = form.save()

    tag2.delete_instance.assert_not_called()
    print(updated_obj.tags)
    assert updated_obj.tags == [tag1, tag2, tag3]


def test_delete_without_object():
    class ChildForm(f.Form):
        name = f.TextField()

    class ProductForm(f.Form):
        tags = f.FormSet(ChildForm)

    existing_obj = Object(name="Test Product", tags=[])

    form = ProductForm(
        {
            f"tags[6][{f.DELETED}]": ["1"],
            "tags[6][name]": ["meh"],
        },
        object=existing_obj
    )

    form.validate()
    assert form.is_valid
    updated_obj = form.save()
    assert updated_obj.tags == []
