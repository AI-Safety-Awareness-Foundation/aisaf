# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the website for the AI Safety Awareness Project (AISAF), built with Hugo static site generator. The site showcases AI safety workshops, provides educational content, and manages event information.

## Development Commands

### Hugo Site
- `hugo server` - Run development server (serves at http://localhost:1313)
- `hugo` - Build the static site for production
- `hugo new content/workshops/workshop-name.md` - Create new workshop content

### Python Scripts
- `cd scripts && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` - Set up Python environment for scripts
- `python scripts/meetup-event-creator/meetup-event-creator.py path/to/event.md --group_urlname GROUP_NAME` - Create Meetup events from markdown files
- `python scripts/updater.py` - Update site content (specific functionality depends on script)

## Site Architecture

### Content Structure
- **Hugo Configuration**: `hugo.toml` defines site settings and baseURL
- **Content**: `/content/` contains all site content including workshops, static pages
- **Layouts**: `/layouts/` contains HTML templates for different page types
- **Static Assets**: `/static/` contains CSS, images, and other static files
- **Generated Site**: `/public/` contains the built Hugo site (generated, not tracked)

### Workshop Management
- Workshop content lives in `/content/workshops/` as Markdown files with YAML frontmatter
- Each workshop has metadata including: title, date, location, temporal status (future/past), and event links
- The homepage dynamically displays upcoming workshops based on the `temporalstatus` and `listindex` parameters
- Workshop-specific location pages are in `/content/workshopday-specific-locations/`

### Event Creation Workflow
1. Create workshop markdown file in `/content/workshops/`
2. Use Python scripts in `/scripts/` to create events on external platforms (Meetup, Eventbrite)
3. Update the markdown file with event links
4. Rebuild Hugo site to reflect changes

### Key Files
- `layouts/index.html` - Homepage template with workshop listings and mailing list signup
- `content/workshops.md` - Main workshops page
- `scripts/meetup-event-creator/` - Python tool for creating Meetup events from markdown files
- `hugo.toml` - Hugo configuration file

## Development Notes

- The site uses Hugo's built-in server for development
- Workshop content is managed through YAML frontmatter in Markdown files
- Python scripts require virtual environment setup and dependencies from requirements.txt files
- The site includes SendGrid integration for mailing list signups
- Event creation scripts use OAuth2 for external platform integration