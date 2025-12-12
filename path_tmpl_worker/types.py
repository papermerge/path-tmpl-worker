from enum import Enum


class FolderType(str, Enum):
    """
    Type of special folder.
    """
    HOME = "home"
    INBOX = "inbox"

