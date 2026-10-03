from app.models.apps import APPS
from app.models.watchlists import WATCHLISTS


def _is_sentence_case(name: str) -> bool:
    return name == name[:1].upper() + name[1:].lower()


def test_sidebar_names_are_sentence_case():
    names = [app.name for app in APPS]
    names += [section.name for app in APPS for section in app.sections]
    names += [watchlist.name for watchlist in WATCHLISTS]
    assert [n for n in names if not _is_sentence_case(n)] == []
