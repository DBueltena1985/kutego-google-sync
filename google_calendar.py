from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SOURCE_TAG = "kutego"


def get_service(credentials_path):
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_synced_events(service, calendar_id):
    """Return {kutego_uid: google_event} for every event this sync previously created."""
    existing = {}
    page_token = None
    while True:
        resp = service.events().list(
            calendarId=calendar_id,
            privateExtendedProperty=f"source={SOURCE_TAG}",
            singleEvents=True,
            maxResults=2500,
            pageToken=page_token,
        ).execute()
        for item in resp.get("items", []):
            uid = item.get("extendedProperties", {}).get("private", {}).get("kutego_uid")
            if uid:
                existing[uid] = item
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return existing


def build_event_body(event, timezone):
    booked = bool(event["attendees"])
    prefix = "✅ " if booked else "🔲 "

    description = event["description"]
    if booked:
        description += "\n\nTeilnehmer:\n" + "\n".join(f"- {name}" for name in event["attendees"])
    else:
        description += "\n\n(Noch keine Buchung)"

    return {
        "summary": prefix + event["summary"],
        "location": event["location"],
        "description": description,
        "start": {"dateTime": event["start"].isoformat(), "timeZone": timezone},
        "end": {"dateTime": event["end"].isoformat(), "timeZone": timezone},
        "extendedProperties": {
            "private": {"source": SOURCE_TAG, "kutego_uid": event["uid"]}
        },
    }


def event_changed(existing, desired):
    return (
        existing.get("summary") != desired["summary"]
        or existing.get("location") != desired["location"]
        or existing.get("description") != desired["description"]
        or existing.get("start", {}).get("dateTime") != desired["start"]["dateTime"]
        or existing.get("end", {}).get("dateTime") != desired["end"]["dateTime"]
    )
