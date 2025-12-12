from enum import Enum


class FolderType(str, Enum):
    """
    Type of special folder.
    """
    HOME = "home"
    INBOX = "inbox"


class OwnerType(str, Enum):
    """
    Type of owner for a special folder.

    Special folders can be owned by either individual users or groups.
    """
    USER = "user"
    GROUP = "group"
