# Cal.com MCP Server for Customers

A FastMCP server that allows AI assistants and LLMs to interact with your Cal.com calendar. This enables AI to help your customers book meetings, check availability, and manage your scheduling directly through natural conversation.

## Quick Start

The easiest way to use this MCP server is with `uvx`:

```bash
uvx run calcom-mcp-for-customers@latest stdio
```

## What This Does

This MCP server gives AI assistants the ability to:

- **Check your availability** by listing your event types
- **Book meetings** on your calendar with customer details
- **View existing bookings** and their status
- **Access your Cal.com schedules, teams, and users**
- **Manage webhooks** for your Cal.com account

## Setup Requirements

Before using this MCP server, you need:

1. **A Cal.com account** with API access
2. **Your Cal.com API key** (get it from your Cal.com settings → Developer section)
3. **Set your API key** as an environment variable:

   ```bash
   export CALCOM_API_KEY="your_actual_api_key_here"
   ```

## Usage with AI Assistants

Once running, the MCP server provides these tools to AI assistants:

### Booking Management

- `create_booking()` - Book new meetings with customer details
- `get_bookings()` - View existing bookings with filters
- `list_event_types()` - Show available meeting types

### Account Information

- `list_schedules()` - View your availability schedules
- `list_teams()` - Access team information
- `list_users()` - View account users
- `list_webhooks()` - Manage webhook configurations

### Status Check

- `get_api_status()` - Verify API key configuration

## Transport Options

The server supports different connection methods:

- `stdio` - Standard input/output (most common)
- `sse` - Server-Sent Events (port 9557)
- `streamable-http` - HTTP streaming (port 9558)

## Example AI Conversation

With this MCP server running, you can have conversations like:

> **You:** "What meeting types do I have available?"
>
> **AI:** _Uses `list_event_types()` to show your Cal.com event types_
>
> **You:** "Book a 30-minute consultation with John Doe (john@example.com) for tomorrow at 2 PM"
>
> **AI:** _Uses `create_booking()` to schedule the meeting and confirms the booking_

## Security Note

**Keep your Cal.com API key secure!** Never share it publicly or commit it to version control. Always use environment variables to store your API key.

## Installation for Development

If you want to modify or contribute to this MCP server:

```bash
git clone https://github.com/Niopub/calcom-mcp-for-customers.git
cd calcom-mcp-for-customers
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
