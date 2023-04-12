from gitlab.base import RequiredOptional, RESTManager, RESTObject
from gitlab.mixins import CRUDMixin, ObjectDeleteMixin, SaveMixin

__all__ = [
    "BroadcastMessage",
    "BroadcastMessageManager",
]


class BroadcastMessage(SaveMixin, ObjectDeleteMixin, RESTObject):
    pass


class BroadcastMessageManager(CRUDMixin, RESTManager):
    _path = "/broadcast_messages"
    _obj_cls = BroadcastMessage

    _create_attrs = RequiredOptional(
        required=("message",), optional=("starts_at", "ends_at", "color", "font")
    )
    _update_attrs = RequiredOptional(
        optional=("message", "starts_at", "ends_at", "color", "font")
    )
