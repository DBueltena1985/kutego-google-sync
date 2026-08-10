import requests
from icalendar import Calendar


def fetch_kutego_events(ics_url):
    """Fetch and parse the kutego (kurs.software) ICS feed into a uid -> event dict."""
    resp = requests.get(ics_url, timeout=30)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)

    events = {}
    for component in cal.walk("VEVENT"):
        uid = str(component.get("uid"))
        summary = str(component.get("summary", ""))
        location = str(component.get("location", "") or "")
        description = str(component.get("description", "") or "")
        start = component.get("dtstart").dt
        end = component.get("dtend").dt

        attendee_field = component.get("attendee")
        attendees = []
        if attendee_field:
            if not isinstance(attendee_field, list):
                attendee_field = [attendee_field]
            for attendee in attendee_field:
                cn = attendee.params.get("CN", "")
                if cn:
                    attendees.append(str(cn))

        events[uid] = {
            "uid": uid,
            "summary": summary,
            "location": location,
            "description": description,
            "start": start,
            "end": end,
            "attendees": attendees,
        }

    return events
