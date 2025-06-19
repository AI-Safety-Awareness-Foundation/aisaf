#!/usr/bin/env python3
"""
Meetup Event Creator - A script to create Meetup.com events from Markdown files.

This script:
1. Parses a Markdown file containing event information with YAML frontmatter
2. Authenticates with the Meetup.com GraphQL API using OAuth2
3. Creates a new event using the information from the Markdown file
4. Optionally publishes the event or leaves it as a draft

Usage:
    python meetup_event_creator.py path/to/event_file.md --group_urlname YOUR_GROUP_URLNAME [--publish]
"""

import argparse
import datetime
import os
import sys
from typing import Dict, Any, Optional

import frontmatter
import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


class MeetupEventCreator:
    """A class to create Meetup.com events from Markdown files."""

    def __init__(self, access_token: str, group_urlname: str):
        """
        Initialize the MeetupEventCreator.

        Args:
            access_token: OAuth2 access token for Meetup.com API
            group_urlname: The urlname of the Meetup.com group to create events for
        """
        self.access_token = access_token
        self.group_urlname = group_urlname
        self.client = self._create_gql_client()

    def _create_gql_client(self) -> Client:
        """
        Create a GraphQL client for making requests to the Meetup.com API.

        Returns:
            A configured GraphQL client
        """
        transport = RequestsHTTPTransport(
            url="https://api.meetup.com/gql",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            use_json=True,
        )
        return Client(transport=transport, fetch_schema_from_transport=True)

    def parse_event_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Markdown file with YAML frontmatter containing event information.

        Args:
            file_path: Path to the Markdown file to parse

        Returns:
            Dictionary containing the parsed event information
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Event file not found: {file_path}")

        # Parse the markdown file with frontmatter
        post = frontmatter.load(file_path)
        
        required_fields = ["title", "workshopdate", "workshoplocation"]
        for field in required_fields:
            if field not in post.metadata:
                raise ValueError(f"Required field '{field}' missing from event file")

        # Extract event information
        event_data = {
            "title": post.metadata.get("title"),
            "description": post.content.strip() if post.content else "",
            "location": post.metadata.get("workshoplocation"),
            "date_time": post.metadata.get("workshopdate"),
        }

        # Convert date string to ISO format
        try:
            # Parse date and time from string like "Mar 13th, 6 p.m. - 8 p.m. Eastern"
            datetime_parts = event_data["date_time"].split("-")
            start_datetime_str = datetime_parts[0].strip()
            
            # Check if there's a year in the date, if not use current year
            if not any(str(year) in start_datetime_str for year in range(datetime.datetime.now().year, datetime.datetime.now().year + 5)):
                start_datetime_str = f"{start_datetime_str} {datetime.datetime.now().year}"
            
            # Parse the date and time
            start_datetime = datetime.datetime.strptime(start_datetime_str, "%b %dth, %I %p.m. %Y")
            
            # If we have an end time, calculate duration in milliseconds
            if len(datetime_parts) > 1:
                end_time_str = datetime_parts[1].strip().split(" Eastern")[0].strip()
                end_time = datetime.datetime.strptime(end_time_str, "%I %p.m.")
                
                # Replace the hour and minute in start_datetime with end_time
                end_datetime = start_datetime.replace(hour=end_time.hour, minute=end_time.minute)
                
                # Calculate duration in milliseconds
                duration = int((end_datetime - start_datetime).total_seconds() * 1000)
            else:
                # Default to 2 hours duration
                duration = 2 * 60 * 60 * 1000
                
            # Format start time in ISO format
            event_data["start_datetime"] = start_datetime.isoformat()
            event_data["duration"] = duration
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Error parsing date and time: {e}")
            
        return event_data

    def create_event(self, event_data: Dict[str, Any], publish: bool = False) -> Dict[str, Any]:
        """
        Create a new event on Meetup.com using the GraphQL API.

        Args:
            event_data: Dictionary containing event information
            publish: Whether to publish the event immediately (True) or save as draft (False)

        Returns:
            Dictionary containing the API response
        """
        # Define the GraphQL mutation for creating an event
        create_event_mutation = gql(
            """
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
        )

        # Prepare the variables for the mutation
        variables = {
            "input": {
                "groupUrlname": self.group_urlname,
                "title": event_data["title"],
                "description": event_data["description"],
                "startDateTime": event_data["start_datetime"],
                "duration": event_data["duration"],
                "publishStatus": "PUBLISHED" if publish else "DRAFT",
                # Add venue information if available
                # If it's a physical location with venue ID:
                # "venueId": "venue_id_here"
                # or for a custom address:
                "address": event_data["location"]
                # For online events:
                # "eventType": "ONLINE"
            }
        }

        # Execute the mutation
        try:
            response = self.client.execute(create_event_mutation, variable_values=variables)
            return response
        except Exception as e:
            print(f"Error creating event: {e}")
            raise

    def verify_token(self) -> bool:
        """
        Verify that the access token is valid by making a test query.

        Returns:
            True if the token is valid, False otherwise
        """
        try:
            test_query = gql(
                """
                query {
                    self {
                        id
                        name
                    }
                }
                """
            )
            result = self.client.execute(test_query)
            return "self" in result and "id" in result["self"]
        except Exception as e:
            print(f"Token verification failed: {e}")
            return False


def get_access_token() -> str:
    """
    Get the access token for the Meetup.com API.
    
    This checks for a token in the environment variable MEETUP_ACCESS_TOKEN
    or prompts the user to enter one.

    Returns:
        The access token string
    """
    token = os.environ.get("MEETUP_ACCESS_TOKEN")
    if not token:
        token = input("Enter your Meetup.com OAuth2 access token: ")
    return token


def main():
    """Main function to parse arguments and create a Meetup.com event."""
    parser = argparse.ArgumentParser(description="Create a Meetup.com event from a Markdown file")
    parser.add_argument("file_path", help="Path to the Markdown file with event information")
    parser.add_argument("--group_urlname", required=True, help="The urlname of your Meetup.com group")
    parser.add_argument("--publish", action="store_true", help="Publish the event immediately (default: save as draft)")

    args = parser.parse_args()

    try:
        # Get the access token
        access_token = get_access_token()

        # Create the event creator
        creator = MeetupEventCreator(access_token, args.group_urlname)

        # Verify the token
        if not creator.verify_token():
            print("Error: Invalid or expired access token")
            sys.exit(1)

        # Parse the event file
        event_data = creator.parse_event_file(args.file_path)
        print(f"Parsed event information: {event_data}")

        # Create the event
        response = creator.create_event(event_data, args.publish)

        # Print the result
        if "createEvent" in response and response["createEvent"]["event"]:
            event = response["createEvent"]["event"]
            status = "Published" if args.publish else "Drafted"
            print(f"{status} event successfully!")
            print(f"Event ID: {event['id']}")
            print(f"Event Title: {event['title']}")
            print(f"Event URL: {event['eventUrl']}")
        elif "createEvent" in response and response["createEvent"]["errors"]:
            print("Error creating event:")
            for error in response["createEvent"]["errors"]:
                print(f"  {error['message']} (code: {error['code']}, field: {error['field']})")
        else:
            print(f"Unexpected response: {response}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
