"""
Formable
Copyright (c) 2025 Juan-Pablo Scaletti
"""

import pytest

import formidable as f
from formidable import errors as err


def test_formset_field():
    class SkillForm(f.Form):
        name = f.TextField()
        level = f.IntegerField(default=1)

    class TestForm(f.Form):
        skills = f.FormSet(SkillForm)

    form = TestForm(
        {
            "skills[0][name]": ["Python"],
            "skills[0][level]": ["5"],
            "skills[1][name]": ["JavaScript"],
            "skills[1][level]": ["3"],
        }
    )


    assert form.skills.new_form.name.name == "skills[NEW_RECORD][name]"  # type: ignore
    assert form.skills.new_form.level.name == "skills[NEW_RECORD][level]"  # type: ignore

    assert form.skills.forms[0].name.name == "skills[0][name]"
    assert form.skills.forms[0].name.value == "Python"

    assert form.skills.forms[0].level.name == "skills[0][level]"
    assert form.skills.forms[0].level.value == 5

    assert form.skills.forms[1].name.name == "skills[1][name]"
    assert form.skills.forms[1].name.value == "JavaScript"

    assert form.skills.forms[1].level.name == "skills[1][level]"
    assert form.skills.forms[1].level.value == 3

    data = form.save()
    print(data)
    assert data == {
        "skills": [
            {"name": "Python", "level": 5},
            {"name": "JavaScript", "level": 3},
        ]
    }


def test_formset_field_object():
    class SkillForm(f.Form):
        name = f.TextField()
        level = f.IntegerField(default=1)

    class TestForm(f.Form):
        skills = f.FormSet(SkillForm)

    form = TestForm(
        object={
            "skills": [
                {"id": 5, "name": "Python", "level": 5},
                {"id": 7, "name": "JavaScript", "level": 3},
            ]
        }
    )

    assert form.skills.new_form.name.name == "skills[NEW_RECORD][name]"  # type: ignore
    assert form.skills.new_form.level.name == "skills[NEW_RECORD][level]"  # type: ignore

    assert form.skills.forms[0].name.name == "skills[5][name]"
    assert form.skills.forms[0].name.value == "Python"

    assert form.skills.forms[0].level.name == "skills[5][level]"
    assert form.skills.forms[0].level.value == 5

    assert form.skills.forms[0]._delete.name == f"skills[5][{f.DELETED}]"
    assert form.skills.forms[0]._destroy.name == f"skills[5][{f.DELETED}]"
    assert form.skills.forms[0]._delete.value is None

    assert form.skills.forms[1].name.name == "skills[7][name]"
    assert form.skills.forms[1].name.value == "JavaScript"

    assert form.skills.forms[1].level.name == "skills[7][level]"
    assert form.skills.forms[1].level.value == 3

    assert form.skills.forms[1]._delete.name == f"skills[7][{f.DELETED}]"
    assert form.skills.forms[1]._destroy.name == f"skills[7][{f.DELETED}]"
    assert form.skills.forms[1]._delete.value is None

    data = form.save()
    print(data)
    assert data == {
        "skills": [
            {"id": 5, "name": "Python", "level": 5},
            {"id": 7, "name": "JavaScript", "level": 3},
        ]
    }


def test_formset_field_object_updated():
    class SkillForm(f.Form):
        name = f.TextField()
        level = f.IntegerField(default=1)

    class TestForm(f.Form):
        skills = f.FormSet(SkillForm)

    form = TestForm(
        {
            "skills[7][name]": ["Go"],
            "skills[7][level]": ["2"],
        },
        object={
            "skills": [
                {"id": 5, "name": "Python", "level": 5},
                {"id": 7, "name": "JavaScript", "level": 3},
            ]
        }
    )

    assert form.skills.new_form.name.name == "skills[NEW_RECORD][name]"  # type: ignore
    assert form.skills.new_form.level.name == "skills[NEW_RECORD][level]"  # type: ignore

    assert form.skills.forms[0].name.name == "skills[7][name]"
    assert form.skills.forms[0].name.value == "Go"

    assert form.skills.forms[0].level.name == "skills[7][level]"
    assert form.skills.forms[0].level.value == 2

    assert form.skills.forms[1].name.name == "skills[5][name]"
    assert form.skills.forms[1].name.value == "Python"

    assert form.skills.forms[1].level.name == "skills[5][level]"
    assert form.skills.forms[1].level.value == 5

    data = form.save()
    print(data)
    assert data == {
        "skills": [
            {"id": 7, "name": "Go", "level": 2},
            {"id": 5, "name": "Python", "level": 5},
        ]
    }


class ChildForm(f.Form):
    meh = f.TextField(required=False)


def test_empty_formset():
    class TestForm(f.Form):
        items = f.FormSet(ChildForm)

    form = TestForm()
    data = form.save()
    print(data)
    assert data == {"items": []}


def test_validate_min_items():
    field = f.FormSet(ChildForm, min_items=3)

    field.set({
        "0": {"meh": "1"},
        "1": {"meh": "2"},
    })
    field.validate()
    assert field.error == err.MIN_ITEMS
    assert field.error_args == {"min_items": 3}

    field.set({
        "0": {"meh": "1"},
        "1": {"meh": "2"},
        "2": {"meh": "3"},
    })
    field.validate()
    assert field.error is None


def test_validate_mixed_min_items():
    field = f.FormSet(ChildForm, min_items=3)

    field.set(
        {
            "0": {"meh": "1"},
        },
        [
            {"id": 1, "meh": "2"},
        ]
    )
    field.validate()
    assert field.error == err.MIN_ITEMS
    assert field.error_args == {"min_items": 3}

    field.set(
        {
            "0": {"meh": "1"},
        },
        [
            {"id": 1, "meh": "2"},
            {"id": 2, "meh": "3"},
        ],
    )
    field.validate()
    assert field.error is None

    field.set(
        {
            "1": {"meh": "1"},  # update object
        },
        [
            {"id": 1, "meh": "2"},
            {"id": 2, "meh": "3"},
        ],
    )
    field.validate()
    assert field.error == err.MIN_ITEMS
    assert field.error_args == {"min_items": 3}


def test_invalid_min_items():
    with pytest.raises(ValueError):
        f.FormSet(ChildForm, min_items="not an int")  # type: ignore


def test_validate_max_items():
    field = f.FormSet(ChildForm, max_items=3)

    field.set({
        "0": {"meh": "1"},
        "1": {"meh": "2"},
        "2": {"meh": "3"},
        "3": {"meh": "4"},
    })
    field.validate()
    assert field.error == err.MAX_ITEMS
    assert field.error_args == {"max_items": 3}

    field.set({
        "0": {"meh": "1"},
        "1": {"meh": "2"},
        "2": {"meh": "3"},
    })
    field.validate()
    assert field.error is None

    field.set({})
    field.validate()
    assert field.error is None


def test_validate_mixed_max_items():
    field = f.FormSet(ChildForm, max_items=3)

    field.set(
        {
            "0": {"meh": "1"},
        },
        [
            {"id": 1, "meh": "2"},
            {"id": 2, "meh": "3"},
            {"id": 3, "meh": "4"},
        ],
    )
    field.validate()
    assert field.error == err.MAX_ITEMS
    assert field.error_args == {"max_items": 3}

    field.set(
        {
            "1": {"meh": "1"},  # update object
        },
        [
            {"id": 1, "meh": "2"},
            {"id": 2, "meh": "3"},
            {"id": 3, "meh": "4"},
        ],
    )
    field.validate()
    assert field.error is None

    field.set(
        {},
        [
            {"id": 1, "meh": "2"},
            {"id": 2, "meh": "3"},
            {"id": 3, "meh": "4"},
        ],
    )
    field.validate()
    assert field.error is None

    field.set({})
    field.validate()
    assert field.error is None


def test_invalid_max_items():
    with pytest.raises(ValueError):
        f.FormSet(ChildForm, max_items="not an int")  # type: ignore
