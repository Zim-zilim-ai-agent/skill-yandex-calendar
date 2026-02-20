import datetime as dt
from unittest.mock import Mock

import pytest

from scripts import yacal


class FakeCalendar:
    def __init__(self, name="cal", url="https://x/cal"):
        self.name = name
        self.url = url
        self._events = []
        self._todos = []
        self.saved_payloads = []

    def date_search(self, start=None, end=None):
        return ["ok", start, end]

    def save_event(self, payload):
        self.saved_payloads.append(payload)
        return {"saved": True, "size": len(payload)}

    def events(self):
        return self._events

    def todos(self):
        return self._todos


class FakeEvent:
    def __init__(self, component):
        self.icalendar_component = component
        self.saved = False
        self.deleted = False

    def save(self):
        self.saved = True

    def delete(self):
        self.deleted = True


class V:
    def __init__(self, value):
        self.dt = value


class ICalComp(dict):
    name = "VEVENT"


def make_client() -> yacal.YandexCalendarClient:
    c = yacal.YandexCalendarClient(token="t")
    return c


def test_init_requires_auth():
    with pytest.raises(ValueError):
        yacal.YandexCalendarClient()


def test_get_calendar_by_name_and_default():
    c = make_client()
    c.get_calendars = Mock(return_value=[FakeCalendar("a"), FakeCalendar("b")])

    assert c.get_calendar().name == "a"
    assert c.get_calendar("b").name == "b"
    assert c.get_calendar("missing") is None


def test_get_todo_calendar_by_url_suffix():
    c = make_client()
    c.get_calendars = Mock(return_value=[FakeCalendar(url="https://x/1"), FakeCalendar(url="https://x/todos/2")])
    assert c.get_todo_calendar().url.endswith("/2")


def test_get_events_handles_missing_calendar():
    c = make_client()
    c.get_calendar = Mock(return_value=None)
    assert c.get_events() == []


def test_get_events_searches_with_range():
    c = make_client()
    cal = FakeCalendar()
    start = dt.datetime(2026, 1, 1)
    end = dt.datetime(2026, 1, 2)
    out = c.get_events(calendar=cal, start=start, end=end)
    assert out[0] == "ok"
    assert out[1] == start
    assert out[2] == end


def test_create_event_minimal_and_with_rrule_and_alarm():
    c = make_client()
    cal = FakeCalendar()
    start = dt.datetime(2026, 1, 1, 10, 0, 0)
    end = dt.datetime(2026, 1, 1, 11, 0, 0)

    out = c.create_event(
        title="Demo",
        description="D",
        location="L",
        start=start,
        end=end,
        reminder_minutes=15,
        rrule="FREQ=WEEKLY;BYDAY=WE",
        calendar=cal,
    )
    assert out["saved"] is True
    assert cal.saved_payloads and isinstance(cal.saved_payloads[0], (bytes, bytearray))


def test_update_event_and_not_found():
    c = make_client()
    cal = FakeCalendar()
    comp = ICalComp(uid="u1", summary="old")
    ev = FakeEvent(comp)
    cal._events = [ev]

    got = c.update_event("u1", title="new", calendar=cal)
    assert got is ev
    assert ev.saved is True
    assert comp["summary"] == "new"

    assert c.update_event("x", title="new", calendar=cal) is None


def test_delete_event_true_false():
    c = make_client()
    cal = FakeCalendar()
    comp = ICalComp(uid="u1")
    ev = FakeEvent(comp)
    cal._events = [ev]

    assert c.delete_event("u1", calendar=cal) is True
    assert ev.deleted is True
    assert c.delete_event("u2", calendar=cal) is False


def test_search_events_case_insensitive():
    c = make_client()
    cal = FakeCalendar()
    ev1 = FakeEvent(ICalComp(uid="1", summary="Alpha", description="Beta", location="Gamma"))
    ev2 = FakeEvent(ICalComp(uid="2", summary="Other", description="text", location="place"))
    cal._events = [ev1, ev2]
    res = c.search_events("alp", calendar=cal)
    assert res == [ev1]


def test_get_todos_none_and_fallback_events_scan():
    c = make_client()
    c.get_todo_calendar = Mock(return_value=None)
    assert c.get_todos() == []

    class NoTodosCalendar(FakeCalendar):
        def todos(self):
            raise AttributeError

    tcal = NoTodosCalendar()
    t = ICalComp(uid="t1")
    t.name = "VTODO"
    e = ICalComp(uid="e1")
    e.name = "VEVENT"
    tcal._events = [FakeEvent(t), FakeEvent(e)]
    todos = c.get_todos(todo_calendar=tcal)
    assert len(todos) == 1


def test_create_complete_delete_todo_flow():
    c = make_client()
    cal = FakeCalendar(url="https://x/todos")

    saved = c.create_todo("Task", description="D", tags=["x"], priority=2, due=dt.datetime(2026, 1, 1), todo_calendar=cal)
    assert saved["saved"] is True

    comp = ICalComp(uid="todo1", status="NEEDS-ACTION")
    todo = FakeEvent(comp)
    cal._todos = [todo]
    c.get_todos = Mock(return_value=[todo])

    assert c.complete_todo("todo1", todo_calendar=cal) is True
    assert comp["status"] == "COMPLETED"
    assert todo.saved is True

    assert c.delete_todo("todo1", todo_calendar=cal) is True
    assert todo.deleted is True


def test_create_todo_no_calendar_returns_none():
    c = make_client()
    c.get_todo_calendar = Mock(return_value=None)
    assert c.create_todo("x") is None


def test_parse_date():
    d = yacal.parse_date("2026-02-20T12:34:56")
    assert d.year == 2026


def test_event_to_dict_rrule_and_defaults():
    comp = ICalComp(
        uid="u",
        summary="s",
        description="d",
        location="l",
        dtstart=V(dt.datetime(2026, 1, 1, 1, 0, 0)),
        dtend=V(dt.datetime(2026, 1, 1, 2, 0, 0)),
        **{"last-modified": "lm", "created": "cr", "rrule": "FREQ=DAILY"},
    )
    ev = FakeEvent(comp)
    out = yacal.event_to_dict(ev)
    assert out["uid"] == "u"
    assert out["rrule"]


def test_todo_to_dict():
    comp = ICalComp(
        uid="t",
        summary="title",
        description="desc",
        categories=["a", "b"],
        priority=3,
        status="NEEDS-ACTION",
        due=V(dt.datetime(2026, 1, 2, 3, 4, 5)),
        created="x",
        completed=V(dt.datetime(2026, 1, 3, 3, 4, 5)),
    )
    t = FakeEvent(comp)
    out = yacal.todo_to_dict(t)
    assert out["tags"] == ["a", "b"]
    assert out["priority"] == 3


def test_get_principal_and_get_calendars_delegate():
    c = make_client()
    principal = Mock()
    principal.calendars.return_value = ["c1"]
    c.client.principal = Mock(return_value=principal)
    assert c.get_principal() is principal
    assert c.get_calendars() == ["c1"]
