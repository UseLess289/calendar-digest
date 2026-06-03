import os
import requests
from icalendar import Calendar
import recurring_ical_events
from datetime import date, datetime, time as dt_time
import pytz
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TIMEZONE         = pytz.timezone("Europe/Paris")

CALENDARS = {
    "Domicile":   os.getenv("ICS_DOMICILE"),
    "Travail":    os.getenv("ICS_TRAVAIL"),
    "Université": os.getenv("ICS_UNIVERSITE"),
 #   "Gmail": os.getenv("ICS_GMAIL"),
}

CAL_EMOJI = {
    "Domicile":   "🏠",
    "Travail":    "💼",
    "Université": "🎓",
    "Gmail":  "🎰",
}

FR_DAYS   = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin",
             "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def fetch_today_events(name, url):
    if not url:
        return []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        cal = Calendar.from_ical(r.text)

        today    = date.today()
        start_dt = TIMEZONE.localize(datetime.combine(today, dt_time.min))
        end_dt   = TIMEZONE.localize(datetime.combine(today, dt_time.max))

        raw_events = recurring_ical_events.of(cal).between(start_dt, end_dt)

        result = []
        for ev in raw_events:
            dtstart = ev.get("DTSTART").dt
            dtend_raw = ev.get("DTEND")
            dtend = dtend_raw.dt if dtend_raw else None

            all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)

            if all_day:
                sort_key = TIMEZONE.localize(datetime.combine(dtstart, dt_time.min))
                time_str = "Toute la journée"
            else:
                if dtstart.tzinfo:
                    dtstart = dtstart.astimezone(TIMEZONE)
                sort_key = dtstart
                time_str = dtstart.strftime("%H:%M")
                if dtend:
                    if hasattr(dtend, "tzinfo") and dtend.tzinfo:
                        dtend = dtend.astimezone(TIMEZONE)
                    time_str += f" → {dtend.strftime('%H:%M')}"

            location = ev.get("LOCATION")
            result.append({
                "calendar": name,
                "summary":  str(ev.get("SUMMARY", "Sans titre")),
                "time":     time_str,
                "sort_key": sort_key,
                "location": str(location) if location else "",
                "all_day":  all_day,
            })

        return result

    except Exception as e:
        print(f"[{name}] Erreur lors de la récupération : {e}")
        return []


def build_message(events):
    today    = date.today()
    date_str = f"{FR_DAYS[today.weekday()]} {today.day} {FR_MONTHS[today.month - 1]} {today.year}"

    lines = [f"📅 <b>{date_str}</b>\n"]

    if not events:
        lines.append("Aucun événement prévu. Journée libre 🎉")
        return "\n".join(lines)

    # Événements toute la journée en premier, puis tri par heure
    events.sort(key=lambda e: (not e["all_day"], e["sort_key"]))

    for ev in events:
        emoji = CAL_EMOJI.get(ev["calendar"], "📆")

        if ev["all_day"]:
            time_part = f"<i>{ev['time']}</i>"
        else:
            time_part = f"<b>{ev['time']}</b>"

        line = f"{emoji} {time_part}  {ev['summary']}"
        if ev["location"]:
            line += f"\n       📍 <i>{ev['location']}</i>"

        lines.append(line)

    n = len(events)
    lines.append(f"\n<i>{n} événement{'s' if n > 1 else ''} aujourd'hui</i>")

    return "\n".join(lines)


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


if __name__ == "__main__":
    all_events = []
    for name, url in CALENDARS.items():
        all_events.extend(fetch_today_events(name, url))

    message = build_message(all_events)
    send_telegram(message)
    print(f"Résumé envoyé ({len(all_events)} événement(s)).")
