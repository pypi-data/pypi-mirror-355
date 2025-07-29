"""
Cal.com MCP Server

A FastMCP server for interacting with the Cal.com API. This enables LLMs to manage event types,
create bookings, and access Cal.com scheduling data programmatically.

Author: Arley Peter
License: MIT
Disclaimer: This project is not affiliated with or endorsed by Cal.com in any way.
"""

import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load environment variables from .env file
load_dotenv()

# Initialize the FastMCP server
mcp = FastMCP(
    name="Cal.com MCP Server for clients to book meetings."
)

# Get Cal.com API key from environment variable
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
print(f"Cal.com API Key: {CALCOM_API_KEY}")
CALCOM_API_BASE_URL = "https://api.cal.com/v2"

@mcp.tool()
def get_current_datetime(timezone: str = "UTC") -> dict:
    """Get the current date and time in the specified timezone.
    
    Args:
        timezone: IANA timezone name (e.g., 'America/New_York', 'Europe/London', 'UTC'). Defaults to UTC.
    
    Returns:
        A dictionary containing current datetime information in various formats.
    """
    try:
        # Get timezone object
        tz = pytz.timezone(timezone)
        
        # Get current datetime in the specified timezone
        now = datetime.now(tz)
        
        return {
            "current_datetime_iso": now.isoformat(),
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "timezone": timezone,
            "day_of_week": now.strftime("%A"),
            "formatted_datetime": now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        }
    except Exception as e:
        return {"error": f"Invalid timezone or error getting current time: {e}"}

@mcp.tool()
def calculate_future_date(days_ahead: int, timezone: str = "UTC", time_of_day: str = "09:00", consider_weekends: bool = True) -> dict:
    """Calculate a future date and time, useful for relative dates like 'tomorrow', 'next week', etc.
    
    Args:
        days_ahead: Number of days from today (1 for tomorrow, 7 for next week, etc.)
        timezone: IANA timezone name (e.g., 'America/New_York', 'Europe/London', 'UTC'). Defaults to UTC.
        time_of_day: Time in HH:MM format (24-hour). Defaults to '09:00'.
        consider_weekends: If True, automatically skip weekends and find the next available weekday. Defaults to True.
    
    Returns:
        A dictionary containing the calculated future datetime in ISO format.
    """
    try:
        # Get timezone object
        tz = pytz.timezone(timezone)
        
        # Get current date in the specified timezone
        today = datetime.now(tz).date()
        
        # Calculate initial future date
        future_date = today + timedelta(days=days_ahead)
        
        # If consider_weekends is True, skip weekends
        if consider_weekends:
            # Check if the calculated date falls on a weekend
            day_of_week = future_date.weekday()  # 0=Monday, 6=Sunday
            
            if day_of_week == 5:  # Saturday
                future_date += timedelta(days=2)  # Move to Monday
            elif day_of_week == 6:  # Sunday
                future_date += timedelta(days=1)  # Move to Monday
        
        # Parse time
        hour, minute = map(int, time_of_day.split(':'))
        
        # Create datetime object
        future_datetime = datetime.combine(future_date, datetime.min.time().replace(hour=hour, minute=minute))
        future_datetime = tz.localize(future_datetime)
        
        # Convert to UTC for API calls
        future_datetime_utc = future_datetime.astimezone(pytz.UTC)
        
        result = {
            "datetime_iso_utc": future_datetime_utc.isoformat().replace('+00:00', 'Z'),
            "datetime_iso_local": future_datetime.isoformat(),
            "date": future_date.strftime("%Y-%m-%d"),
            "time_local": time_of_day,
            "timezone": timezone,
            "day_of_week": future_date.strftime("%A"),
            "formatted": future_datetime.strftime("%A, %B %d, %Y at %I:%M %p %Z"),
            "weekends_considered": consider_weekends
        }
        
        # Add note if date was adjusted due to weekend
        if consider_weekends:
            original_date = today + timedelta(days=days_ahead)
            if original_date != future_date:
                result["note"] = f"Date adjusted from {original_date.strftime('%A, %B %d')} to avoid weekend"
                result["original_date_was_weekend"] = True
            else:
                result["original_date_was_weekend"] = False
        
        return result
    except Exception as e:
        return {"error": f"Error calculating future date: {e}"}

@mcp.tool()
def get_api_status() -> str:
    """Check if the Cal.com API key is configured in the environment.

    Returns:
        A string indicating whether the Cal.com API key is configured or not.
    """
    if CALCOM_API_KEY:
        return "Cal.com API key is configured."
    else:
        return "Cal.com API key is NOT configured. Please set the CALCOM_API_KEY environment variable."

@mcp.tool()
def list_event_types() -> list[dict] | dict:
    """Fetch a simplified list of active (non-hidden) event types from Cal.com.
    This is preferred for LLMs to easily present options or make booking decisions.

    Returns:
        A list of dictionaries, each with 'id', 'title', 'slug', 'length_minutes',
        'owner_profile_slug' (user or team slug), and 'location_summary'.
        Returns an error dictionary if the API call fails or no event types are found.
    """
    if not CALCOM_API_KEY:
        return {"error": "Cal.com API key not configured. Please set the CALCOM_API_KEY environment variable."}
    
    headers = {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    raw_response_data = {}
    try:
        response = requests.get(f"{CALCOM_API_BASE_URL}/event-types", headers=headers)
        response.raise_for_status()
        raw_response_data = response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "status_code": response.status_code, "response_text": response.text}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request exception occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred during API call or data processing: {e}"}

    options = []
    event_type_groups = raw_response_data.get("data", {}).get("eventTypeGroups", [])

    if not event_type_groups and raw_response_data.get("data", {}).get("eventTypes"):
        event_types_direct = raw_response_data.get("data", {}).get("eventTypes", [])
        for et in event_types_direct:
            if not et.get("hidden"):
                owner_slug_info = f"user_id_{et.get('userId')}"
                if et.get("teamId"):
                    owner_slug_info = f"team_id_{et.get('teamId')}"

                location_types = [
                    loc.get("type", "unknown")
                    .replace("integrations:google:meet", "Google Meet")
                    .replace("integrations:zoom:zoom_video", "Zoom") # Common Zoom integration key
                    .replace("integrations:microsoft:teams", "Microsoft Teams") # Common Teams key
                    .replace("inPerson", "In-person")
                    for loc in et.get("locations", [])
                ]
                location_summary = ", ".join(location_types) or "Provider configured"
                # Check for Cal Video (often 'dailyCo', 'calvideo', or similar)
                if any("daily" in loc_type.lower() or "calvideo" in loc_type.lower() for loc_type in location_types):
                    location_summary = "Cal Video"

                options.append({
                    "id": et.get("id"),
                    "title": et.get("title"),
                    "slug": et.get("slug"),
                    "length_minutes": et.get("length"),
                    "owner_info": owner_slug_info,
                    "location_summary": location_summary,
                    "requires_confirmation": et.get("requiresConfirmation", False),
                    "description_preview": (et.get("description") or "")[:100] + "..." if et.get("description") else "No description."
                })

    else:
        for group in event_type_groups:
            owner_profile_slug = group.get("profile", {}).get("slug", f"group_owner_id_{group.get('id')}") # Fallback if slug missing
            for et in group.get("eventTypes", []):
                if not et.get("hidden"):  # Only include non-hidden event types
                    location_types = [
                        loc.get("type", "unknown")
                        .replace("integrations:google:meet", "Google Meet")
                        .replace("integrations:zoom:zoom_video", "Zoom")
                        .replace("integrations:microsoft:teams", "Microsoft Teams")
                        .replace("inPerson", "In-person")
                        for loc in et.get("locations", [])
                    ]
                    location_summary = ", ".join(location_types) or "Provider configured"
                    if any("daily" in loc_type.lower() or "calvideo" in loc_type.lower() for loc_type in location_types):
                        location_summary = "Cal Video"

                    options.append({
                        "id": et.get("id"),
                        "title": et.get("title"),
                        "slug": et.get("slug"),
                        "length_minutes": et.get("length"),
                        "owner_profile_slug": owner_profile_slug,
                        "location_summary": location_summary,
                        "requires_confirmation": et.get("requiresConfirmation", False),
                        # Add a snippet of the description if available
                        "description_preview": (et.get("description") or "")[:100] + "..." if et.get("description") else "No description."
                    })

    if not options:
        # Check if there was an issue with the raw response structure itself if it wasn't an HTTP/Request error
        if not raw_response_data or "data" not in raw_response_data:
             return {"error": "Failed to parse event types from Cal.com API response.", "raw_response_preview": str(raw_response_data)[:200]}
        return {"message": "No active (non-hidden) event types found for the configured API key."}
    
    return options

@mcp.tool()
def get_bookings(event_type_id: int = None, user_id: int = None, status: str = None, date_from: str = None, date_to: str = None, limit: int = 20) -> dict:
    """Fetch a simplified list of bookings from Cal.com, showing only essential scheduling information.

    Args:
        event_type_id: Optional. Filter bookings by a specific event type ID.
        user_id: Optional. Filter bookings by a specific user ID (typically the user associated with the API key or a managed user).
        status: Optional. Filter bookings by status (e.g., 'ACCEPTED', 'PENDING', 'CANCELLED', 'REJECTED').
        date_from: Optional. Filter bookings from this date (ISO 8601 format, e.g., '2023-10-26T10:00:00.000Z').
        date_to: Optional. Filter bookings up to this date (ISO 8601 format, e.g., '2023-10-27T10:00:00.000Z').
        limit: Optional. Maximum number of bookings to return (default is 20).

    Returns:
        A dictionary containing a simplified list of bookings with only essential information:
        - id: booking ID
        - title: meeting title
        - status: booking status
        - start: start time in ISO format
        - end: end time in ISO format
        - date: date in YYYY-MM-DD format
        Returns an error dictionary if the API call fails.
    """
    if not CALCOM_API_KEY:
        return {"error": "Cal.com API key not configured. Please set the CALCOM_API_KEY environment variable."}
    
    headers = {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": "2024-08-13"
    }
    
    params = {}
    if event_type_id is not None:
        params['eventTypeId'] = event_type_id
    if user_id is not None:
        params['userId'] = user_id
    if status is not None:
        params['status'] = status
    if date_from is not None:
        params['afterStart'] = date_from
    if date_to is not None:
        params['beforeEnd'] = date_to
    if limit is not None:
        params['take'] = limit
    
    try:
        response = requests.get(f"{CALCOM_API_BASE_URL}/bookings", headers=headers, params=params)
        response.raise_for_status()
        full_response = response.json()
        
        # Extract only essential booking information
        bookings = []
        for booking in full_response.get("data", []):
            start_time = booking.get("start", "")
            end_time = booking.get("end", "")
            # Extract date from start time (YYYY-MM-DD format)
            date = start_time.split("T")[0] if start_time else ""
            
            simplified_booking = {
                "id": booking.get("id"),
                "title": booking.get("title", ""),
                "status": booking.get("status", ""),
                "start": start_time,
                "end": end_time,
                "date": date,
                "duration_minutes": booking.get("duration", 0)
            }
            bookings.append(simplified_booking)
        
        return {
            "bookings": bookings,
            "total_count": full_response.get("pagination", {}).get("totalItems", len(bookings))
        }
        
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "status_code": response.status_code, "response_text": response.text}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request exception occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

@mcp.tool()
def create_booking(
    start_time: str,
    attendee_name: str,
    attendee_email: str,
    attendee_timezone: str,
    event_type_id: int = None,
    event_type_slug: str = None,
    username: str = None,
    team_slug: str = None,
    organization_slug: str = None,
    attendee_phone_number: str = None,
    attendee_language: str = None,
    guests: list[str] = None,
    location_input: str = None,
    metadata: dict = None,
    length_in_minutes: int = None,
    booking_fields_responses: dict = None
) -> dict:
    """Create a new booking in Cal.com for a specific event type and attendee.

    Args:
        start_time: Required. The start time of the booking in ISO 8601 format in UTC (e.g., '2024-08-13T09:00:00Z').
        attendee_name: Required. The name of the primary attendee.
        attendee_email: Required. The email of the primary attendee.
        attendee_timezone: Required. The IANA time zone of the primary attendee (e.g., 'America/New_York').
        event_type_id: Optional. The ID of the event type to book. Either this or (eventTypeSlug + username/teamSlug) is required.
        event_type_slug: Optional. The slug of the event type. Used with username or team_slug if event_type_id is not provided.
        username: Optional. The username of the event owner. Used with event_type_slug.
        team_slug: Optional. The slug of the team owning the event type. Used with event_type_slug.
        organization_slug: Optional. The organization slug, used with event_type_slug and username/team_slug if applicable.
        attendee_phone_number: Optional. Phone number for the attendee (e.g., for SMS reminders).
        attendee_language: Optional. Preferred language for the attendee (e.g., 'en', 'it').
        guests: Optional. A list of additional guest email addresses.
        location_input: Optional. Specifies the meeting location. Can be a simple string for Cal Video, or a URL for custom locations.
        metadata: Optional. A dictionary of custom key-value pairs (max 50 keys, 40 char key, 500 char value).
        length_in_minutes: Optional. If the event type allows variable lengths, specify the desired duration.
        booking_fields_responses: Optional. A dictionary for responses to custom booking fields (slug: value).

    Returns:
        A dictionary containing the API response (booking details) or an error message.
    """
    if not CALCOM_API_KEY:
        return {"error": "Cal.com API key not configured. Please set the CALCOM_API_KEY environment variable."}
    if not event_type_id and not (event_type_slug and (username or team_slug)):
        return {"error": "Either 'event_type_id' or ('event_type_slug' and 'username'/'team_slug') must be provided."}
    headers = {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": "2024-08-13"
    }
    payload = {
        "start": start_time,
        "attendee": {
            "name": attendee_name,
            "email": attendee_email,
            "timeZone": attendee_timezone
        }
    }
    if event_type_id:
        payload['eventTypeId'] = event_type_id
    else:
        payload['eventTypeSlug'] = event_type_slug
        if username:
            payload['username'] = username
        elif team_slug:
            payload['teamSlug'] = team_slug
        if organization_slug:
            payload['organizationSlug'] = organization_slug
    if attendee_phone_number:
        payload['attendee']['phoneNumber'] = attendee_phone_number
    if attendee_language:
        payload['attendee']['language'] = attendee_language
    if guests:
        payload['guests'] = guests
    if location_input:
        payload['location'] = location_input
    if metadata:
        payload['metadata'] = metadata
    if length_in_minutes:
        payload['lengthInMinutes'] = length_in_minutes
    if booking_fields_responses:
        payload['bookingFieldsResponses'] = booking_fields_responses
    try:
        response = requests.post(f"{CALCOM_API_BASE_URL}/bookings", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        error_details = {"error": f"HTTP error occurred: {http_err}", "status_code": response.status_code}
        try:
            error_details["response_text"] = response.json()
        except ValueError:
            error_details["response_text"] = response.text
        return error_details
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request exception occurred: {req_err}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}