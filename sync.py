import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ics_source import fetch_kutego_events
from google_calendar import build_event_body, event_changed, get_service, list_synced_events

PROJECT_DIR = Path(__file__).resolve().parent
ACTIVE_HOURS_TZ = "Europe/Berlin"
ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 22


def run_sync():
    now = datetime.now(ZoneInfo(ACTIVE_HOURS_TZ))
    if not (ACTIVE_HOUR_START <= now.hour < ACTIVE_HOUR_END):
        return {"skipped": True, "reason": f"outside {ACTIVE_HOUR_START}-{ACTIVE_HOUR_END} {ACTIVE_HOURS_TZ}"}

    ics_url = os.environ["KUTEGO_ICS_URL"].strip()
    calendar_id = os.environ["GOOGLE_CALENDAR_ID"].strip()
    credentials_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")
    if not os.path.isabs(credentials_path):
        credentials_path = str(PROJECT_DIR / credentials_path)
    timezone = os.environ.get("EVENT_TIMEZONE", "Europe/Berlin")

    current_events = fetch_kutego_events(ics_url)

    service = get_service(credentials_path)
    existing_events = list_synced_events(service, calendar_id)

    created = updated = deleted = unchanged = 0

    for uid, event in current_events.items():
        desired_body = build_event_body(event, timezone)

        if uid in existing_events:
            if event_changed(existing_events[uid], desired_body):
                service.events().update(
                    calendarId=calendar_id,
                    eventId=existing_events[uid]["id"],
                    body=desired_body,
                ).execute()
                updated += 1
            else:
                unchanged += 1
        else:
            service.events().insert(calendarId=calendar_id, body=desired_body).execute()
            created += 1

    removed_uids = set(existing_events) - set(current_events)
    for uid in removed_uids:
        service.events().delete(
            calendarId=calendar_id, eventId=existing_events[uid]["id"]
        ).execute()
        deleted += 1

    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "unchanged": unchanged,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print(run_sync())
