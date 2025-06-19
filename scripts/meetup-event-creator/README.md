# Meetup Event Creator

A Python script to create Meetup.com events from Markdown files with YAML frontmatter.

## Features

- Parse Markdown files with YAML frontmatter containing event information
- Create events on Meetup.com using their GraphQL API
- Support for both in-person and online events
- Option to publish immediately or save as a draft

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/meetup-event-creator.git
   cd meetup-event-creator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Authentication

The script requires a Meetup.com OAuth2 access token to authenticate with the API. You can either:

1. Set the `MEETUP_ACCESS_TOKEN` environment variable:
   ```
   export MEETUP_ACCESS_TOKEN="your-oauth2-token"
   ```

2. Or enter the token when prompted by the script.

To obtain an OAuth2 token, follow Meetup's [OAuth2 Server Flow documentation](https://www.meetup.com/api/authentication/#oauth2-server-flow).

## Markdown File Format

Your Markdown files should include YAML frontmatter with the following fields:

```markdown
---
title: AI Safety Meet-Up | NYC
workshopdate: Mar 13th, 6 p.m. - 8 p.m. Eastern
workshoplocation: Bibliotheque, 54 Mercer St, New York, NY 10013, USA
temporalstatus: past
detailstobedetermined: false
listindex: 3
---

Event description goes here. This text will be used as the event description on Meetup.com.

You can include Markdown formatting, links, and lists - they will be converted appropriately.
```

Required frontmatter fields:
- `title`: The title of the event
- `workshopdate`: The date and time of the event
- `workshoplocation`: The location of the event

## Usage

Run the script with the following command:

```
python meetup_event_creator.py path/to/event_file.md --group_urlname YOUR_GROUP_URLNAME [--publish]
```

Arguments:
- `path/to/event_file.md`: Path to the Markdown file containing event information
- `--group_urlname`: The urlname of your Meetup.com group (required)
- `--publish`: Optional flag to publish the event immediately (default: save as draft)

Example:
```
python meetup_event_creator.py events/ai-safety-nyc.md --group_urlname ai-safety-nyc
```

## Notes

- The script will parse the date and time from the `workshopdate` field and calculate the duration based on the start and end times.
- For online events, you may need to modify the script to set the appropriate event type.
- If you need to specify a venue ID for an existing venue, you'll need to modify the script accordingly.
