import os
import re
import datetime

WORKSHOP_DIR = "content/workshops"  # Update based on your repo structure
DATE_FORMATS = ["%b %d, %Y", "%B %d, %Y", "%b %dth, %Y", "%B %dth, %Y"]  # Handles "Dec 7th, 2024" etc.

def parse_date(date_str):
    """Attempts to parse a date from different possible formats."""
    # Remove ordinal suffixes (st, nd, rd, th)
    for fmt in DATE_FORMATS:
        try:
            clean_date_str = re.sub(r"(st|nd|rd|th)", "", date_str)
            return datetime.datetime.strptime(clean_date_str, fmt).date()
        except ValueError:
            continue
    return None

def update_workshop_status():
    today = datetime.date.today()
    
    for filename in os.listdir(WORKSHOP_DIR):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(WORKSHOP_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.readlines()

        new_content = []
        date_found = False
        status_updated = False

        for line in content:
            if line.startswith("workshopdate:"):
                full_date_str = line.split(": ", 1)[1].strip()
                # Split on comma to get the initial part before any extra text.
                parts = full_date_str.split(",")[0]
                # If no 4-digit year is found in the full string, append the current year.
                if not re.search(r'\d{4}', full_date_str):
                    date_str = parts.strip() + f", {today.year}"
                else:
                    date_str = full_date_str.strip()
                workshop_date = parse_date(date_str)
                date_found = True
            elif line.startswith("temporalstatus:") and date_found:
                if workshop_date and workshop_date < today and "future" in line:
                    new_content.append("temporalstatus: past\n")
                    status_updated = True
                    continue
            new_content.append(line)

        if status_updated:
            with open(filepath, "w", encoding="utf-8") as file:
                file.writelines(new_content)
            print(f"Updated {filename}")

if __name__ == "__main__":
    update_workshop_status()
