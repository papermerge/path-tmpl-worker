import uuid

from path_tmpl_worker import get_evaluated_path

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
