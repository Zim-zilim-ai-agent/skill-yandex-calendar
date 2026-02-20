#!/usr/bin/env python3
"""
Yandex Calendar CLI via CalDAV.

Usage:
  yacal.py list-calendars
  yacal.py events [--today | --from DATE] [--to DATE] [--calendar NAME]
  yacal.py create --title TITLE [--description DESC] [--location LOC] [--start DATETIME] [--end DATETIME] [--reminder MINUTES]
  yacal.py update --uid UID [--title TITLE] [--description DESC] [--location LOC] [--start DATETIMЕ] [--end DATETIME]
  yacal.py delete --uid UID
  yacal.py search --query QUERY
  yacal.py list-todos
  yacal.py create-todo --title TITLE [--description DESC] [--tags TAGS] [--priority PRIORITY] [--due DATETIME]
  yacal.py complete-todo --uid UID
  yacal.py delete-todo --uid UID

Options:
  --token TOKEN        OAuth token (or set YANDEX_CALENDAR_OAUTH_TOKEN)
  --user-id ID         Yandex user ID (or set YANDEX_CALENDAR_USER_ID)
  --calendar NAME      Calendar name (default: first found)
  --today              Events for today
  --from DATE          Start date (YYYY-MM-DD)
  --to DATE            End date (YYYY-MM-DD)
  --title TITLE        Event/todo title
  --description DESC   Event/todo description
  --location LOC       Event location
  --start DATETIME     Start datetime (YYYY-MM-DDTHH:MM:SS)
  --end DATETIME       End datetime (YYYY-MM-DDTHH:MM:SS)
  --reminder MINUTES   Reminder before event in minutes
  --uid UID            Event/todo UID
  --query QUERY        Search query
  --tags TAGS          Todo tags (comma-separated)
  --priority PRIORITY  Todo priority (1-9, 1 highest)
  --due DATETIME       Todo due datetime (YYYY-MM-DDTHH:MM:SS)

Environment variables:
  YANDEX_CALENDAR_OAUTH_TOKEN   OAuth token
  YANDEX_CALENDAR_USER_ID       Yandex user ID (optional)

Date formats:
  DATE: YYYY-MM-DD
  DATETIME: YYYY-MM-DDTHH:MM:SS (24-hour)
"""

import os
import sys
import json
import datetime
import argparse
from typing import Optional, List, Dict, Any

from caldav import DAVClient, Principal, Calendar, Event
from icalendar import Calendar as ICalendar, Event as IEvent, Todo as VTodo, Alarm, vRecur
from dateutil import parser as date_parser


# Yandex CalDAV endpoint
YANDEX_CALDAV_URL = "https://caldav.yandex.ru/"


class YandexCalendarClient:
    """Client for Yandex Calendar via CalDAV."""
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None, user_id: Optional[str] = None):
        self.token = token
        self.username = username
        self.password = password
        self.user_id = user_id
        
        if token:
            # OAuth auth
            headers = {"Authorization": f"OAuth {token}"}
            self.client = DAVClient(
                url=YANDEX_CALDAV_URL,
                headers=headers
            )
        elif username and password:
            # Basic auth
            self.client = DAVClient(
                url=YANDEX_CALDAV_URL,
                username=username,
                password=password
            )
        else:
            raise ValueError("Either token or username/password must be provided")
    
    def get_principal(self) -> Principal:
        """Get CalDAV principal (user)."""
        return self.client.principal()
    
    def get_calendars(self) -> List[Calendar]:
        """Get all calendars."""
        principal = self.get_principal()
        return principal.calendars()
    
    def get_calendar(self, name: Optional[str] = None) -> Optional[Calendar]:
        """Get calendar by name (or first if name not specified)."""
        calendars = self.get_calendars()
        if not calendars:
            return None
        if name:
            for cal in calendars:
                if cal.name == name:
                    return cal
            return None
        return calendars[0]  # default: first calendar
    
    def get_todo_calendar(self) -> Optional[Calendar]:
        """Get todo calendar (named 'Не забыть')."""
        calendars = self.get_calendars()
        for cal in calendars:
            if 'todos' in str(cal.url):
                return cal
        return None
    
    def get_events(self, calendar: Optional[Calendar] = None,
                   start: Optional[datetime.datetime] = None,
                   end: Optional[datetime.datetime] = None) -> List[Event]:
        """Get events from calendar within date range."""
        if not calendar:
            calendar = self.get_calendar()
        if not calendar:
            return []
        return calendar.date_search(start=start, end=end)
    
    def create_event(self, title: str, description: str = "", location: str = "",
                     start: Optional[datetime.datetime] = None,
                     end: Optional[datetime.datetime] = None,
                     reminder_minutes: Optional[int] = None,
                     rrule: Optional[str] = None,
                     calendar: Optional[Calendar] = None) -> Event:
        """Create a new event."""
        if not calendar:
            calendar = self.get_calendar()
        
        cal = ICalendar()
        cal.add('prodid', '-//Yandex Calendar CLI//')
        cal.add('version', '2.0')
        
        event = IEvent()
        event.add('summary', title)
        if description:
            event.add('description', description)
        if location:
            event.add('location', location)
        
        if not start:
            start = datetime.datetime.now()
        if not end:
            end = start + datetime.timedelta(hours=1)
        
        event.add('dtstart', start)
        event.add('dtend', end)
        event.add('dtstamp', datetime.datetime.now())
        
        if reminder_minutes:
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Напоминание: {title}')
            alarm.add('trigger', datetime.timedelta(minutes=-reminder_minutes))
            event.add_component(alarm)
        
        if rrule:
            # Parse RRULE string to vRecur object
            rrule_obj = vRecur.from_ical(rrule)
            event.add('rrule', rrule_obj)
        
        cal.add_component(event)
        ical_data = cal.to_ical()
        return calendar.save_event(ical_data)
    
    def update_event(self, uid: str, title: Optional[str] = None,
                     description: Optional[str] = None,
                     location: Optional[str] = None,
                     start: Optional[datetime.datetime] = None,
                     end: Optional[datetime.datetime] = None,
                     calendar: Optional[Calendar] = None) -> Optional[Event]:
        """Update an existing event."""
        if not calendar:
            calendar = self.get_calendar()
        
        events = calendar.events()
        for event in events:
            ical = event.icalendar_component
            if str(ical.get('uid')) == uid:
                if title:
                    ical['summary'] = title
                if description:
                    ical['description'] = description
                if location:
                    ical['location'] = location
                if start:
                    ical['dtstart'] = start
                if end:
                    ical['dtend'] = end
                
                event.save()
                return event
        return None
    
    def delete_event(self, uid: str, calendar: Optional[Calendar] = None) -> bool:
        """Delete an event by UID."""
        if not calendar:
            calendar = self.get_calendar()
        
        events = calendar.events()
        for event in events:
            ical = event.icalendar_component
            if str(ical.get('uid')) == uid:
                event.delete()
                return True
        return False
    
    def search_events(self, query: str, calendar: Optional[Calendar] = None) -> List[Event]:
        """Search events by text (title, description, location)."""
        if not calendar:
            calendar = self.get_calendar()
        
        results = []
        events = calendar.events()
        for event in events:
            ical = event.icalendar_component
            text = (str(ical.get('summary', '')) + 
                    str(ical.get('description', '')) + 
                    str(ical.get('location', ''))).lower()
            if query.lower() in text:
                results.append(event)
        return results
    
    def get_todos(self, todo_calendar: Optional[Calendar] = None) -> List[Any]:
        """Get all todos (VTODO)."""
        if not todo_calendar:
            todo_calendar = self.get_todo_calendar()
        if not todo_calendar:
            return []
        try:
            return todo_calendar.todos()
        except AttributeError:
            # fallback: search for VTODO components
            todos = []
            for event in todo_calendar.events():
                ical = event.icalendar_component
                if ical.name == 'VTODO':
                    todos.append(event)
            return todos
    
    def create_todo(self, title: str, description: str = "", tags: Optional[List[str]] = None,
                    priority: int = 5, due: Optional[datetime.datetime] = None,
                    todo_calendar: Optional[Calendar] = None) -> Optional[Any]:
        """Create a new todo (VTODO)."""
        if not todo_calendar:
            todo_calendar = self.get_todo_calendar()
        if not todo_calendar:
            return None
        
        cal = ICalendar()
        cal.add('prodid', '-//Yandex Calendar CLI//')
        cal.add('version', '2.0')
        
        todo = VTodo()
        todo.add('summary', title)
        if description:
            todo.add('description', description)
        if tags:
            todo.add('categories', tags)
        todo.add('priority', priority)
        todo.add('status', 'NEEDS-ACTION')
        todo.add('created', datetime.datetime.now())
        if due:
            todo.add('due', due)
        
        cal.add_component(todo)
        ical_data = cal.to_ical()
        return todo_calendar.save_event(ical_data)
    
    def complete_todo(self, uid: str, todo_calendar: Optional[Calendar] = None) -> bool:
        """Mark a todo as completed."""
        if not todo_calendar:
            todo_calendar = self.get_todo_calendar()
        
        todos = self.get_todos(todo_calendar)
        for todo in todos:
            ical = todo.icalendar_component
            if str(ical.get('uid')) == uid:
                ical['status'] = 'COMPLETED'
                ical['completed'] = datetime.datetime.now()
                todo.save()
                return True
        return False
    
    def delete_todo(self, uid: str, todo_calendar: Optional[Calendar] = None) -> bool:
        """Delete a todo by UID."""
        if not todo_calendar:
            todo_calendar = self.get_todo_calendar()
        
        todos = self.get_todos(todo_calendar)
        for todo in todos:
            ical = todo.icalendar_component
            if str(ical.get('uid')) == uid:
                todo.delete()
                return True
        return False


def parse_date(date_str: str) -> datetime.datetime:
    """Parse date string to datetime."""
    return date_parser.parse(date_str)


def event_to_dict(event: Event) -> Dict[str, Any]:
    """Format event as dict for output."""
    ical = event.icalendar_component
    result = {
        'uid': str(ical.get('uid', '')),
        'title': str(ical.get('summary', '')),
        'description': str(ical.get('description', '')),
        'location': str(ical.get('location', '')),
        'start': str(ical.get('dtstart').dt) if ical.get('dtstart') else None,
        'end': str(ical.get('dtend').dt) if ical.get('dtend') else None,
        'created': str(ical.get('created', '')),
        'last_modified': str(ical.get('last-modified', ''))
    }
    # Add RRULE if present
    rrule = ical.get('rrule')
    if rrule:
        result['rrule'] = str(rrule)
    return result


def todo_to_dict(todo: Any) -> Dict[str, Any]:
    """Format todo as dict for output."""
    ical = todo.icalendar_component
    return {
        'uid': str(ical.get('uid', '')),
        'title': str(ical.get('summary', '')),
        'description': str(ical.get('description', '')),
        'tags': list(ical.get('categories', [])) if ical.get('categories') else [],
        'priority': int(ical.get('priority', 5)),
        'status': str(ical.get('status', 'NEEDS-ACTION')),
        'due': str(ical.get('due').dt) if ical.get('due') else None,
        'created': str(ical.get('created', '')),
        'completed': str(ical.get('completed', '')) if ical.get('completed') else None
    }


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(description='Yandex Calendar CLI')
    parser.add_argument('--token', help='OAuth token', default=os.getenv('YANDEX_CALENDAR_OAUTH_TOKEN'))
    parser.add_argument('--username', help='Yandex username (for Basic auth)', default=os.getenv('YANDEX_CALENDAR_USERNAME'))
    parser.add_argument('--password', help='Yandex password or app password', default=os.getenv('YANDEX_CALENDAR_PASSWORD'))
    parser.add_argument('--user-id', help='Yandex user ID', default=os.getenv('YANDEX_CALENDAR_USER_ID'))
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # List calendars
    subparsers.add_parser('list-calendars', help='List available calendars')
    
    # Events
    events_parser = subparsers.add_parser('events', help='List events')
    events_group = events_parser.add_mutually_exclusive_group()
    events_group.add_argument('--today', action='store_true', help='Events for today')
    events_group.add_argument('--from', dest='from_date', help='Start date (YYYY-MM-DD)')
    events_parser.add_argument('--to', dest='to_date', help='End date (YYYY-MM-DD)')
    events_parser.add_argument('--calendar', help='Calendar name')
    
    # Create event
    create_parser = subparsers.add_parser('create', help='Create event')
    create_parser.add_argument('--title', required=True, help='Event title')
    create_parser.add_argument('--description', help='Event description')
    create_parser.add_argument('--location', help='Event location')
    create_parser.add_argument('--start', help='Start datetime (YYYY-MM-DDTHH:MM:SS)', default=datetime.datetime.now().isoformat())
    create_parser.add_argument('--end', help='End datetime (YYYY-MM-DDTHH:MM:SS)')
    create_parser.add_argument('--reminder', type=int, help='Reminder before event in minutes')
    create_parser.add_argument('--rrule', help='Recurrence rule (RRULE), e.g. "FREQ=WEEKLY;BYDAY=WE"')
    
    # Update event
    update_parser = subparsers.add_parser('update', help='Update event')
    update_parser.add_argument('--uid', required=True, help='Event UID')
    update_parser.add_argument('--title', help='New title')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--location', help='New location')
    update_parser.add_argument('--start', help='New start datetime')
    update_parser.add_argument('--end', help='New end datetime')
    
    # Delete event
    delete_parser = subparsers.add_parser('delete', help='Delete event')
    delete_parser.add_argument('--uid', required=True, help='Event UID')
    
    # Search events
    search_parser = subparsers.add_parser('search', help='Search events')
    search_parser.add_argument('--query', required=True, help='Search query')
    
    # List todos
    subparsers.add_parser('list-todos', help='List todos')
    
    # Create todo
    create_todo_parser = subparsers.add_parser('create-todo', help='Create todo')
    create_todo_parser.add_argument('--title', required=True, help='Todo title')
    create_todo_parser.add_argument('--description', help='Todo description')
    create_todo_parser.add_argument('--tags', help='Todo tags (comma-separated)')
    create_todo_parser.add_argument('--priority', type=int, choices=range(1, 10), default=5, help='Priority (1-9, 1 highest)')
    create_todo_parser.add_argument('--due', help='Due datetime (YYYY-MM-DDTHH:MM:SS)')
    
    # Complete todo
    complete_todo_parser = subparsers.add_parser('complete-todo', help='Mark todo as completed')
    complete_todo_parser.add_argument('--uid', required=True, help='Todo UID')
    
    # Delete todo
    delete_todo_parser = subparsers.add_parser('delete-todo', help='Delete todo')
    delete_todo_parser.add_argument('--uid', required=True, help='Todo UID')
    
    args = parser.parse_args()
    
    # Create client
    client = None
    if args.token:
        client = YandexCalendarClient(token=args.token, user_id=args.user_id)
    elif args.username and args.password:
        client = YandexCalendarClient(username=args.username, password=args.password, user_id=args.user_id)
    else:
        print("Error: Authentication required. Provide either --token or --username/--password.", file=sys.stderr)
        print("Set YANDEX_CALENDAR_OAUTH_TOKEN or YANDEX_CALENDAR_USERNAME/YANDEX_CALENDAR_PASSWORD environment variables.", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.command == 'list-calendars':
            calendars = client.get_calendars()
            result = []
            for cal in calendars:
                result.append({
                    'name': cal.name,
                    'url': str(cal.url)
                })
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.command == 'events':
            # Determine date range
            if args.today:
                start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + datetime.timedelta(days=1)
            else:
                start = parse_date(args.from_date) if args.from_date else datetime.datetime.now()
                end = parse_date(args.to_date) if args.to_date else start + datetime.timedelta(days=7)
            
            calendar = client.get_calendar(args.calendar)
            if not calendar:
                print("Error: No calendar found", file=sys.stderr)
                sys.exit(1)
            
            events = client.get_events(calendar, start, end)
            result = [event_to_dict(event) for event in events]
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.command == 'create':
            # Parse datetime
            start = parse_date(args.start)
            end = parse_date(args.end) if args.end else start + datetime.timedelta(hours=1)
            
            event = client.create_event(
                title=args.title,
                description=args.description or "",
                location=args.location or "",
                start=start,
                end=end,
                reminder_minutes=args.reminder,
                rrule=args.rrule
            )
            if event:
                print(json.dumps({
                    'status': 'created',
                    'uid': event.icalendar_component.get('uid')
                }, indent=2, ensure_ascii=False))
            else:
                print("Error: Failed to create event", file=sys.stderr)
                sys.exit(1)
            
        elif args.command == 'update':
            start = parse_date(args.start) if args.start else None
            end = parse_date(args.end) if args.end else None
            
            event = client.update_event(
                uid=args.uid,
                title=args.title,
                description=args.description,
                location=args.location,
                start=start,
                end=end
            )
            if event:
                print(json.dumps({
                    'status': 'updated',
                    'uid': event.icalendar_component.get('uid')
                }, indent=2, ensure_ascii=False))
            else:
                print("Error: Event not found", file=sys.stderr)
                sys.exit(1)
            
        elif args.command == 'delete':
            success = client.delete_event(args.uid)
            if success:
                print(json.dumps({'status': 'deleted', 'uid': args.uid}, indent=2, ensure_ascii=False))
            else:
                print("Error: Event not found", file=sys.stderr)
                sys.exit(1)
            
        elif args.command == 'search':
            calendar = client.get_calendar()
            if not calendar:
                print("Error: No calendar found", file=sys.stderr)
                sys.exit(1)
            
            events = client.search_events(args.query, calendar)
            result = [event_to_dict(event) for event in events]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.command == 'list-todos':
            todos = client.get_todos()
            result = [todo_to_dict(todo) for todo in todos]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.command == 'create-todo':
            # Parse tags
            tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
            due = parse_date(args.due) if args.due else None
            
            todo = client.create_todo(
                title=args.title,
                description=args.description or "",
                tags=tags,
                priority=args.priority,
                due=due
            )
            if todo:
                print(json.dumps({
                    'status': 'created',
                    'uid': todo.icalendar_component.get('uid')
                }, indent=2, ensure_ascii=False))
            else:
                print("Error: Failed to create todo", file=sys.stderr)
                sys.exit(1)
        
        elif args.command == 'complete-todo':
            success = client.complete_todo(args.uid)
            if success:
                print(json.dumps({'status': 'completed', 'uid': args.uid}, indent=2, ensure_ascii=False))
            else:
                print("Error: Todo not found", file=sys.stderr)
                sys.exit(1)
        
        elif args.command == 'delete-todo':
            success = client.delete_todo(args.uid)
            if success:
                print(json.dumps({'status': 'deleted', 'uid': args.uid}, indent=2, ensure_ascii=False))
            else:
                print("Error: Todo not found", file=sys.stderr)
                sys.exit(1)
        
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':  # pragma: no cover
    main()