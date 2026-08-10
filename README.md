# kutego → Google Calendar Sync

Schreibt kutego-Kurstermine (inkl. Buchungsstatus und Teilnehmerliste) automatisch als
echte Termine in einen Google-Kalender – per Google Calendar API, nicht per ICS-Abo.
Dadurch: Sync-Latenz von ~5 Minuten statt der 8-24h, die Google/Apple beim Abonnieren
externer ICS-URLs brauchen.

Jeder synchronisierte Termin bekommt:
- `✅ ` vor dem Titel, wenn mindestens eine Buchung (ATTENDEE) vorliegt
- `🔲 ` vor dem Titel, wenn noch niemand gebucht hat
- die Namen der Teilnehmer in der Beschreibung

## 1. Google Cloud einrichten (einmalig)

1. [console.cloud.google.com](https://console.cloud.google.com) öffnen, neues Projekt anlegen
   (z. B. "kutego-sync").
2. Im Menü **APIs & Dienste → Bibliothek** nach "Google Calendar API" suchen und **aktivieren**.
3. **APIs & Dienste → Anmeldedaten → Anmeldedaten erstellen → Dienstkonto**.
   - Name frei wählbar (z. B. `kutego-sync-bot`).
   - Rollen können übersprungen werden (nicht nötig für Calendar API).
4. Im erstellten Dienstkonto → Tab **Keys/Schlüssel → Schlüssel hinzufügen → JSON**.
   Die heruntergeladene Datei umbenennen in `service-account.json` und in diesen
   Projektordner legen (liegt in `.gitignore`, wird nicht committet).
5. Die E-Mail-Adresse des Dienstkontos kopieren (sieht aus wie
   `kutego-sync-bot@kutego-sync.iam.gserviceaccount.com`).
6. Im **Google-Kalender deiner Schwester** (calendar.google.com) → Einstellungen des
   Zielkalenders → **Für bestimmte Personen freigeben** → diese Dienstkonto-E-Mail
   eintragen, Berechtigung **"Änderungen an Terminen vornehmen"**.
7. Die Calendar-ID des Zielkalenders notieren (Kalendereinstellungen → "Kalender
   integrieren" → "Kalender-ID"; beim Hauptkalender ist das schlicht ihre Gmail-Adresse).

## 2. Projekt einrichten

```powershell
cd kutego-google-sync
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` ausfüllen (nur für den lokalen Test nötig):
- `KUTEGO_ICS_URL` – die kutego-ICS-URL
- `GOOGLE_CALENDAR_ID` – aus Schritt 1.7
- `GOOGLE_SERVICE_ACCOUNT_FILE` – Pfad zu `service-account.json`

## 3. Lokal testen

```powershell
python sync.py
```

Gibt `{'created': X, 'updated': X, 'deleted': X, 'unchanged': X}` aus. Danach im
Google-Kalender prüfen, ob die Termine mit ✅/🔲 auftauchen.

## 4. Deployment: GitHub Actions (kostenlos, kein eigener Server nötig)

PythonAnywhere scheidet auf dem Free-Tier aus: ausgehende Verbindungen sind dort auf
eine Domain-Whitelist beschränkt, `api.kurs.software` steht nicht drauf (Proxy-Fehler
403). GitHub Actions hat diese Einschränkung nicht und läuft bei einem **öffentlichen**
Repo mit unbegrenzten kostenlosen Minuten (bei einem privaten Repo würde das 5-Minuten-
Intervall das kostenlose Monatskontingent sprengen, weil jeder Lauf mindestens 1 Minute
kostet).

1. Neues **öffentliches** GitHub-Repo anlegen (z. B. `kutego-google-sync`). Der Code
   selbst enthält keine Geheimnisse – die liegen ausschließlich in verschlüsselten
   GitHub Secrets, nie im Repo.
2. Projektordner hochladen/pushen (ohne `.env` und `service-account.json` – die bleiben
   dank `.gitignore` sowieso außen vor).
3. Im Repo unter **Settings → Secrets and variables → Actions → New repository secret**
   folgende Secrets anlegen:
   - `KUTEGO_ICS_URL` – die kutego-ICS-URL
   - `GOOGLE_CALENDAR_ID` – `puehlm@gmail.com`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` – kompletter Inhalt von `service-account.json`
     (die ganze JSON-Datei als Text reinkopieren)
4. Fertig. Der Workflow unter `.github/workflows/sync.yml` läuft automatisch alle 5
   Minuten (`cron: '*/5 * * * *'`) und schreibt Änderungen in den Google-Kalender.
5. Zum manuellen Testen: Tab **Actions** im Repo → Workflow "kutego-sync" auswählen →
   **"Run workflow"** → nach ein paar Sekunden auf den Lauf klicken und die Logs prüfen.

**Hinweis:** GitHub deaktiviert geplante Workflows automatisch, wenn 60 Tage lang keine
Aktivität im Repo stattfindet. Ein gelegentlicher Commit (oder manuelles "Run workflow")
reicht, um das zu vermeiden.
