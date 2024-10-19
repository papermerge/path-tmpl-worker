import uuid
from datetime import date as Date

from path_tmpl_worker import get_evaluated_path
from path_tmpl_worker.models import CustomField


def test_get_evaluated_path_title():
    ev_path = get_evaluated_path(
        title="coco",
        id=uuid.uuid4(),
        path_template="/home/{{ document.title }}"
    )

    assert ev_path == "/home/coco"


def test_get_evaluated_path_id():
    id = uuid.uuid4()
    ev_path = get_evaluated_path(
        title="coco",
        id=id,
        path_template="/home/{{ document.title }}-{{ document.id }}"
    )

    assert ev_path == f"/home/coco-{id}"


def test_get_evaluated_path_with_all_cf_defined():
    path_tmpl = """
    {% if document.has_all_cf %}
        /home/Groceries/{{ document.cf['Shop'] }}-{{ document.cf['Effective Date'] }}-{{document.cf['Total']}}
    {% else %}
        /home/Groceries/{{ document.id }}
    {% endif %}
    """
    custom_fields = [
        CustomField(name="Shop", value="lidl"),
        CustomField(name="Total", value=10.34),
        CustomField(name="Effective Date", value=Date(2024, 12, 23))
    ]
    id = uuid.uuid4()
    ev_path = get_evaluated_path(
        title="coco",
        id=id,
        custom_fields=custom_fields,
        path_template=path_tmpl
    )
    assert ev_path == f"/home/Groceries/lidl-2024-12-23-10.34"


def test_get_evaluated_path_with_some_cf_missing():
    path_tmpl = """
    {% if document.has_all_cf %}
        /home/Groceries/{{ document.cf['Shop'] }}-{{ document.cf['Effective Date'] }}-{{document.cf['Total']}}
    {% else %}
        /home/Groceries/{{ document.id }}
    {% endif %}
    """
    custom_fields = [
        CustomField(name="Shop", value=None),  # !!! missing !!!
        CustomField(name="Total", value=10.34),
        CustomField(name="Effective Date", value=Date(2024, 12, 23))
    ]
    id = uuid.uuid4()
    ev_path = get_evaluated_path(
        title="coco",
        id=id,
        custom_fields=custom_fields,
        path_template=path_tmpl
    )
    assert ev_path == f"/home/Groceries/{id}"
