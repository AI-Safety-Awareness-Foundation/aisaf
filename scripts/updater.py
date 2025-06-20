import os
import re
import datetime
from typing import Dict, List, Tuple, Optional

WORKSHOP_DIR = "content/workshops"  # Update based on your repo structure
DATE_FORMATS = [
    "%b %d, %Y", "%B %d, %Y", "%b %dth, %Y", "%B %dth, %Y",
    "%b %dst, %Y", "%B %dst, %Y", "%b %dnd, %Y", "%B %dnd, %Y",
    "%b %drd, %Y", "%B %drd, %Y"
]  # Handles various ordinal suffixes

def parse_date(date_str):
    """Attempts to parse a date from different possible formats."""
    print(f"  Attempting to parse date: '{date_str}'")
    
    # Extract just the date part before any time information
    date_part = date_str.split(' ')[0:3]  # Take first 3 parts (Month Day, Year)
    if len(date_part) >= 2:
        date_part_str = ' '.join(date_part)
        # Remove trailing comma if present
        date_part_str = date_part_str.rstrip(',')
        print(f"  Extracted date part: '{date_part_str}'")
        
        # Try to parse with ordinal suffixes first
        for fmt in DATE_FORMATS:
            try:
                parsed = datetime.datetime.strptime(date_part_str, fmt).date()
                print(f"  Successfully parsed as: {parsed}")
                return parsed
            except ValueError:
                continue
        
        # Try without ordinal suffixes
        clean_date_str = re.sub(r"(st|nd|rd|th)", "", date_part_str)
        print(f"  Trying without ordinals: '{clean_date_str}'")
        for fmt in DATE_FORMATS:
            try:
                clean_fmt = fmt.replace("th", "").replace("st", "").replace("nd", "").replace("rd", "")
                parsed = datetime.datetime.strptime(clean_date_str, clean_fmt).date()
                print(f"  Successfully parsed as: {parsed}")
                return parsed
            except ValueError:
                continue
    
    print(f"  Failed to parse date: '{date_str}'")
    return None

def parse_workshop_file(filepath: str) -> Dict:
    """Parse a workshop markdown file and extract frontmatter data."""
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.readlines()
    
    workshop_data = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'content': content,
        'workshopdate': None,
        'temporalstatus': None,
        'listindex': None,
        'parsed_date': None
    }
    
    for i, line in enumerate(content):
        if line.startswith("workshopdate:"):
            full_date_str = line.split(": ", 1)[1].strip()
            workshop_data['workshopdate'] = full_date_str
            workshop_data['workshopdate_line'] = i
            
            # Parse the date
            parts = full_date_str.split(",")[0]
            if not re.search(r'\d{4}', full_date_str):
                date_str = parts.strip() + f", {datetime.date.today().year}"
            else:
                date_str = full_date_str.strip()
            workshop_data['parsed_date'] = parse_date(date_str)
            
        elif line.startswith("temporalstatus:"):
            workshop_data['temporalstatus'] = line.split(": ", 1)[1].strip()
            workshop_data['temporalstatus_line'] = i
            
        elif line.startswith("listindex:"):
            try:
                workshop_data['listindex'] = int(line.split(": ", 1)[1].strip())
                workshop_data['listindex_line'] = i
            except ValueError:
                workshop_data['listindex'] = None
    
    return workshop_data

def get_max_past_listindex(workshops: List[Dict]) -> int:
    """Get the maximum listindex value among workshops with temporalstatus: past."""
    max_index = 0
    for workshop in workshops:
        if workshop['temporalstatus'] == 'past' and workshop['listindex'] is not None:
            max_index = max(max_index, workshop['listindex'])
    return max_index

def update_workshop_file(workshop: Dict, new_temporalstatus: str = None, new_listindex: int = None):
    """Update a workshop file with new temporalstatus and/or listindex."""
    content = workshop['content'].copy()
    
    if new_temporalstatus and 'temporalstatus_line' in workshop:
        content[workshop['temporalstatus_line']] = f"temporalstatus: {new_temporalstatus}\n"
    
    if new_listindex is not None and 'listindex_line' in workshop:
        content[workshop['listindex_line']] = f"listindex: {new_listindex}\n"
    
    with open(workshop['filepath'], "w", encoding="utf-8") as file:
        file.writelines(content)

def update_workshop_status():
    """Main function to update workshop statuses and reorder listindexes."""
    today = datetime.date.today()
    print(f"Today's date: {today}")
    
    # Parse all workshop files
    workshops = []
    print(f"Scanning workshop directory: {WORKSHOP_DIR}")
    for filename in os.listdir(WORKSHOP_DIR):
        if not filename.endswith(".md"):
            continue
        
        print(f"\nProcessing file: {filename}")
        filepath = os.path.join(WORKSHOP_DIR, filename)
        workshop_data = parse_workshop_file(filepath)
        workshops.append(workshop_data)
        
        print(f"  Status: {workshop_data['temporalstatus']}")
        print(f"  Date: {workshop_data['workshopdate']}")
        print(f"  Parsed date: {workshop_data['parsed_date']}")
        print(f"  Listindex: {workshop_data['listindex']}")
    
    # Find workshops that need status update (future -> past)
    workshops_to_update = []
    print(f"\nChecking for workshops that need updates...")
    for workshop in workshops:
        if (workshop['parsed_date'] and 
            workshop['parsed_date'] < today and 
            workshop['temporalstatus'] == 'future'):
            print(f"  {workshop['filename']} needs update: {workshop['parsed_date']} < {today}")
            workshops_to_update.append(workshop)
    
    if not workshops_to_update:
        print("No workshops need status updates.")
        return
    
    # Sort workshops to update by date (earliest first)
    workshops_to_update.sort(key=lambda w: w['parsed_date'])
    print(f"\nWorkshops to update (sorted by date):")
    for workshop in workshops_to_update:
        print(f"  {workshop['filename']}: {workshop['parsed_date']}")
    
    # Get the current maximum listindex for past workshops
    max_past_listindex = get_max_past_listindex(workshops)
    print(f"\nCurrent max listindex for past workshops: {max_past_listindex}")
    
    # Update each workshop
    next_listindex = max_past_listindex + 1
    print(f"\nUpdating workshops:")
    for workshop in workshops_to_update:
        print(f"  Updating {workshop['filename']}: future -> past, listindex -> {next_listindex}")
        update_workshop_file(workshop, new_temporalstatus='past', new_listindex=next_listindex)
        next_listindex += 1

if __name__ == "__main__":
    update_workshop_status()
