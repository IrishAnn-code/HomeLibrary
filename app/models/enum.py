from enum import Enum


class ReadStatus(str, Enum):
    NOT_READ = "not_read"
    READING = "reading"
    READ = "read"

    @property
    def russian_name(self):
        names = {
            ReadStatus.NOT_READ: "❌ Не прочитано",
            ReadStatus.READING: "📖 Читаю",
            ReadStatus.READ: "✅ Прочитано ",
        }
        return names[self]


class LibraryRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    GUEST = "guest"


class BookPermission(str, Enum):
    EDIT_FULL = "edit_full"
    EDIT_STATUS = "edit_status"
    EDIT_DESCRIPTION = "edit_description"
    DELETE = "delete"


class GenreStatus(str, Enum):
    ADVENTURE = "adventure"
    CHILDREN_S = "children's"
    CLASSICS = "classics"
    DETECTIVE = "detective"
    DRAMA = "drama"
    FANTASY = "fantasy"
    NOVEL = "novel"
    POETRY = "poetry"
    SCIENCE_FICTION = "science_fiction"
    OTHER = "other"

    @property
    def russian_name(self):
        names = {
            GenreStatus.DETECTIVE: "детектив",
            GenreStatus.CHILDREN_S: "детская литература",
            GenreStatus.DRAMA: "драма",
            GenreStatus.CLASSICS: "классика",
            GenreStatus.SCIENCE_FICTION: "научная фантастика",
            GenreStatus.POETRY: "поэзия",
            GenreStatus.ADVENTURE: "приключения",
            GenreStatus.NOVEL: "роман",
            GenreStatus.FANTASY: "фэнтези",
            GenreStatus.OTHER: "другое",
        }
        return names[self]
