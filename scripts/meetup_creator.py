import re
import os
import json
import requests
import yaml
import argparse
from datetime import datetime
import webbrowser

def parse_md_file(file_path):
    """Parse a markdown file to extract event details."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        front_matter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        
        front_matter_text = front_matter_match.group(1)
        front_matter = yaml.safe_load(front_matter_text)
        
        main_content = content[front_matter_match.end():]
        
        event = {
            "title": front_matter.get("title", ""),
            "description": main_content.strip(),
            "start_date": None,
            
            "_parsed_is_online": "http" in front_matter.get("workshoplocation", "").lower(),
            "_parsed_location_hint": front_matter.get("workshoplocation", ""),
            "_parsed_temporal_status": front_matter.get("temporalstatus", ""),
            "_parsed_details_tbd": front_matter.get("detailstobedetermined", False),
            "_parsed_list_index": front_matter.get("listindex", "")
        }
        
        # Parse workshop date
        workshop_date = front_matter.get("workshopdate", "")
        if workshop_date:
            try:
                date_parts = workshop_date.split(',')
                date_str = date_parts[0].strip()  # e.g., "Feb 1st"
                time_str = date_parts[1].strip() if len(date_parts) > 1 else ""  # e.g., "2 p.m. Central"
                
                date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)  # Remove ordinal suffixes
                
                if not re.search(r'\d{4}', date_str):
                    date_str += f" {datetime.now().year}"
                
                # Try to parse the combined date and time
                if time_str:
                    time_str = time_str.replace("a.m.", "AM").replace("p.m.", "PM")
                    time_str = re.sub(r'(\d+)\s*(AM|PM)', r'\1:00 \2', time_str)
                    
                    timezone_match = re.search(r'(Eastern|Central|Mountain|Pacific|GMT[-+]\d+)', time_str)
                    timezone = timezone_match.group(0) if timezone_match else ""
                    
                    clean_time = re.sub(r'(Eastern|Central|Mountain|Pacific|GMT[-+]\d+)', '', time_str).strip()
                    
                    dt_str = f"{date_str} {clean_time}"
                    try:
                        dt = datetime.strptime(dt_str, "%b %d %Y %I:%M %p")
                    except ValueError:
                        try:
                            dt = datetime.strptime(dt_str, "%B %d %Y %I:%M %p")
                        except ValueError:
                            # Simplified fallback for time parsing issues
                            dt = datetime.strptime(date_str, "%b %d %Y")
                
                event["start_date"] = dt.strftime("%Y-%m-%dT%H:%M")
            except Exception as e:
                print(f"Warning: Error parsing date '{workshop_date}': {e}")
                print("You'll need to set the date manually when creating the event.")
        
        return event
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}

def get_access_token(client_id, client_secret):
    
    auth_url = (
        f"https://secure.meetup.com/oauth2/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri=https://aisafetyawarenessfoundation.org"
    )
    
    webbrowser.open(auth_url)
    
    auth_code = input("\nURL: ")
    
    code_match = re.search(r'code=([^&]+)', auth_code)
    if not code_match:
        print("Error: Could not find authorization code in the URL.")
        return None
    
    code = code_match.group(1)
    
    #access token
    token_url = "https://secure.meetup.com/oauth2/access"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": "https://aisafetyawarenessfoundation.org",
        "code": code
    }
    
    try:
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"Error getting access token: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during token exchange: {str(e)}")
        return None


def get_user_groups(token):
    """Get a list of groups the user organizes or co-organizes"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = """
    query {
        self {
            groups {
                edges {
                    node {
                        id
                        urlname
                        name
                        memberships {
                            role
                        }
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            "https://api.meetup.com/gql",
            headers=headers,
            json={"query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            edges = data.get("data", {}).get("self", {}).get("groups", {}).get("edges", [])
            
            organizer_groups = []
            for edge in edges:
                node = edge.get("node", {})
                memberships = node.get("memberships", {})
                role = memberships.get("role", "")
                
                if role in ["ORGANIZER", "CO_ORGANIZER", "ASSISTANT_ORGANIZER"]:
                    organizer_groups.append({
                        "id": node.get("id"),
                        "urlname": node.get("urlname"),
                        "name": node.get("name"),
                        "role": role
                    })
            
            return organizer_groups
        else:
            print(f"Error getting groups: {response.text}")
            return []
    except Exception as e:
        print(f"Exception getting groups: {str(e)}")
        return []

def create_meetup_event(token, group_urlname, event_data):
    """Create a new event on Meetup.com using the GraphQL API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Build the mutation variables with ONLY title, description, and start time
    variables = {
        "input": {
            "groupUrlname": group_urlname,
            "title": event_data["title"],
            "description": event_data["description"],
        }
    }
    
    # Add start date if available
    if event_data.get("start_date"):
        variables["input"]["startDateTime"] = event_data["start_date"]
    
    # GraphQL mutation
    mutation = """
    mutation($input: CreateEventInput!) {
      createEvent(input: $input) {
        event {
          id
          title
          eventUrl
        }
        errors {
          message
          code
          field
        }
      }
    }
    """
    
    # Make the API request
    try:
        response = requests.post(
            "https://api.meetup.com/gql",
            headers=headers,
            json={
                "query": mutation,
                "variables": variables
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API request failed with status {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {"error": f"Exception making API request: {str(e)}"}

def main():
    print("=== Create a Meetup.com event from a markdown file ===\n")
    
    # Get file path input from user
    file_path = input("Enter the path to your markdown file: ")
    
    # Parse the markdown file
    print(f"\nParsing markdown file: {file_path}")
    event_data = parse_md_file(file_path)
    
    if "error" in event_data:
        print(f"Error: {event_data['error']}")
        return
    
    # Display parsed event data
    print(f"Title: {event_data['title']}")
    print(f"Start Date: {event_data.get('start_date', 'Not specified')}")
    print(f"Description: {(event_data['description'])}")
    
    # Get authentication information
    access_token = input("\nEnter your Meetup API access token (or press Enter to use client credentials): ")
    
    if not access_token:
        client_id = input("Enter your Meetup OAuth client ID: ")
        client_secret = input("Enter your Meetup OAuth client secret: ")
        
        if client_id and client_secret:
            access_token = get_access_token(client_id, client_secret)
    
    if not access_token:
        print("\nError: You must provide either an access token or client ID and secret.")
        return
    
    # Get groups the user can create events for
    print("\nFetching your Meetup groups...")
    groups = get_user_groups(access_token)
    
    if not groups:
        print("No groups found where you have organizer privileges.")
        return
    
    print("\n=== Your Meetup Groups ===")
    for i, group in enumerate(groups, 1):
        print(f"{i}. {group['name']} ({group['urlname']}) - {group['role']}")
    
    # Let the user select a group
    while True:
        try:
            selection = int(input("\nSelect a group to create the event for (enter number): "))
            if 1 <= selection <= len(groups):
                selected_group = groups[selection - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(groups)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Create the event
    print("\nCreating event...")
    result = create_meetup_event(access_token, selected_group['urlname'], event_data)
    
    # Process the result
    if "error" in result:
        print(f"Error creating event: {result['error']}")
        if "details" in result:
            print(f"Details: {result['details']}")
    else:
        event_data = result.get("data", {}).get("createEvent", {})
        
        if "errors" in event_data and event_data["errors"]:
            print("API returned errors:")
            for error in event_data["errors"]:
                print(f"- {error.get('message')} (Code: {error.get('code')}, Field: {error.get('field')})")
        else:
            event = event_data.get("event", {})
            if event:
                print(" Event created successfully!")
                print(f"Title: {event.get('title')}")
                print(f"ID: {event.get('id')}")
                print(f"URL: {event.get('eventUrl')}")
            else:
                print("Unexpected response from API. Check your Meetup account to verify if the event was created.")

if __name__ == "__main__":
    main()

    