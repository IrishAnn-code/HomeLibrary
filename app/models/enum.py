from enum import Enum


class ReadStatus(str, Enum):
    NOT_READ = "not_read"
    READING = "reading"
    READ = "read"


class LibraryRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    GUEST = "guest"
