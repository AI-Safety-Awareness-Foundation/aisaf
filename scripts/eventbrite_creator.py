import re
import datetime
import frontmatter
from dateutil import parser
import pytz
import requests

def parse_workshop_date(date_str):
    """
    Parse a date string like 'Mar 15th, 4 p.m. - 5:30 p.m. EDT' and return:
      - start_dt_utc: start datetime in UTC,
      - end_dt_utc: end datetime in UTC,
      - tz_str: timezone string (e.g., 'EDT')
    """
    # Remove ordinal suffixes (st, nd, rd, th)
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    # Split the string into the date part and the time range plus timezone
    try:
        month_day, time_range_tz = date_str.split(',', 1)
    except ValueError:
        raise ValueError("Date string format unexpected. Expected a comma-separated date and time range.")

    month_day = month_day.strip()  # e.g., "Mar 15"
    
    # Assume the timezone is the last word in the string and the rest is the time range.
    time_range_tz = time_range_tz.strip()  # e.g., "4 p.m. - 5:30 p.m. EDT"
    parts = time_range_tz.rsplit(' ', 1)
    if len(parts) != 2:
        raise ValueError("Time range and timezone not properly formatted.")
    time_range, tz_str = parts
    # Split the time range into start and end times.
    try:
        start_time_str, end_time_str = [s.strip() for s in time_range.split('-', 1)]
    except ValueError:
        raise ValueError("Time range does not contain a valid '-' separator.")
    
    # Use current year (or hardcode a specific year if needed).
    year = datetime.datetime.now().year
    # Build complete datetime strings.
    start_datetime_str = f"{month_day} {year} {start_time_str} {tz_str}"
    end_datetime_str = f"{month_day} {year} {end_time_str} {tz_str}"
    
    # Parse using dateutil.
    start_dt = parser.parse(start_datetime_str)
    end_dt = parser.parse(end_datetime_str)
    
    # Convert to UTC.
    start_dt_utc = start_dt.astimezone(pytz.utc)
    end_dt_utc = end_dt.astimezone(pytz.utc)
    
    return start_dt_utc, end_dt_utc, tz_str

def create_event_on_eventbrite(event_payload, organization_id, oauth_token):
    """
    Post an event payload to the Eventbrite API to create a new event.
    """
    url = f"https://www.eventbriteapi.com/v3/organizations/{organization_id}/events/"
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=event_payload, headers=headers)
    return response

def main():
    # Path to your markdown file
    markdown_file = "event.md"
    post = frontmatter.load(markdown_file)

    # Extract required fields from the YAML front matter.
    title = post.get("title")
    workshopdate = post.get("workshopdate")
    workshoplocation = post.get("workshoplocation")
    
    if not title or not workshopdate:
        raise ValueError("Markdown file must contain 'title' and 'workshopdate' in the front matter.")
    
    # Use the markdown body as the base description.
    description_body = post.content.strip()
    
    # Optionally, incorporate the workshop location into the description.
    if workshoplocation:
        description_html = f"<p>{description_body}</p><p><strong>Location:</strong> {workshoplocation}</p>"
    else:
        description_html = f"<p>{description_body}</p>"
    
    # Parse the workshop date to get start and end times in UTC and timezone string.
    start_dt_utc, end_dt_utc, tz_str = parse_workshop_date(workshopdate)
    
    # Build the payload for Eventbrite.
    event_payload = {
        "event": {
            "name": {
                "html": title
            },
            "description": {
                "html": description_html
            },
            "start": {
                "timezone": tz_str,
                "utc": start_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "end": {
                "timezone": tz_str,
                "utc": end_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "currency": "USD",
            # Mark the event as not online since a physical location is provided.
            "online_event": False
        }
    }
    
    # Set your Eventbrite organization ID and OAuth token.
    organization_id = "your_organization_id"   # Replace with your organization ID
    oauth_token = "your_personal_oauth_token"    # Replace with your OAuth token
    
    # Create the event on Eventbrite.
    response = create_event_on_eventbrite(event_payload, organization_id, oauth_token)
    
    if response.status_code in (200, 201):
        print("Event created successfully!")
        print("Response:", response.json())
    else:
        print("Failed to create event. Status code:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    main()
