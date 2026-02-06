# Discord MCP Server Mock
# Based on real Discord MCP server from SaseQ/discord-mcp
#
# Discord has 24 tools total, but we select:
# - All overlapping tools with Slack (core messaging)
# - Minimal extra tools to test adaptation
#
# OVERLAP WITH SLACK (8 tools):
#   1. list_channels - List channels (slack_list_channels)
#   2. send_message - Send message (slack_post_message)
#   3. read_messages - Get history (slack_get_channel_history)
#   4. add_reaction - Add reaction (slack_add_reaction)
#   5. get_user_id_by_name - Find user (slack_get_users / slack_get_user_profile)
#
# DISCORD-ONLY EXTRAS (5 tools - forces adaptation):
#   6. edit_message - Edit existing message (Slack can't do this!)
#   7. delete_message - Delete a message (Slack can't do this!)
#   8. send_private_message - Send DM (Slack can't do this!)
#   9. create_text_channel - Create channel (Slack can't do this!)
#   10. get_server_info - Server details
#
# Total: 10 tools (vs Slack's 8) - tests adaptation in both directions

from typing import Dict, Any, Optional, List

DEFAULT_STATE = {
    "server": {
        "id": "123456789",
        "name": "Acme Gaming",
        "member_count": 250,
        "owner_id": "U001",
    },
    "channels": [
        {
            "id": "CH001",
            "name": "general",
            "type": "text",
            "topic": "General discussion",
            "category_id": "CAT001",
        },
        {
            "id": "CH002",
            "name": "dev-talk",
            "type": "text",
            "topic": "Development discussions",
            "category_id": "CAT002",
        },
        {
            "id": "CH003",
            "name": "random",
            "type": "text",
            "topic": "Off-topic chat",
            "category_id": "CAT001",
        },
    ],
    "categories": [
        {"id": "CAT001", "name": "General"},
        {"id": "CAT002", "name": "Development"},
    ],
    "users": [
        {
            "id": "U001",
            "username": "alice_dev",
            "display_name": "Alice",
            "discriminator": "1234",
        },
        {
            "id": "U002",
            "username": "bob_gamer",
            "display_name": "Bob",
            "discriminator": "5678",
        },
        {
            "id": "U003",
            "username": "carol_mod",
            "display_name": "Carol",
            "discriminator": "9012",
        },
    ],
    "messages": {
        "CH001": [
            {
                "id": "M001",
                "author_id": "U001",
                "content": "Hey everyone! Welcome to the server!",
                "timestamp": "2024-01-15T10:00:00Z",
                "reactions": [{"emoji": "👋", "count": 5}],
            },
            {
                "id": "M002",
                "author_id": "U002",
                "content": "Thanks for the invite!",
                "timestamp": "2024-01-15T10:05:00Z",
                "reactions": [],
            },
        ],
        "CH002": [
            {
                "id": "M003",
                "author_id": "U001",
                "content": "Working on the new feature branch today",
                "timestamp": "2024-01-15T09:00:00Z",
                "reactions": [{"emoji": "💻", "count": 2}],
            },
        ],
    },
    "direct_messages": {},
    "next_message_id": 100,
    "next_channel_id": 100,
}


class DiscordAPI:
    """
    Mock Discord MCP Server.

    EXTENDED TOOL SET (10 tools) - More than Slack's 8 tools.

    OVERLAPPING TOOLS (work similar to Slack):
    - list_channels: List server channels
    - send_message: Send message to channel
    - read_messages: Get channel message history
    - add_reaction: Add emoji reaction
    - get_user_id_by_name: Find user by username

    DISCORD-ONLY TOOLS (Slack can't do these):
    - edit_message: Modify existing message
    - delete_message: Remove a message
    - send_private_message: Send direct message
    - create_text_channel: Create new channel
    - get_server_info: Get server details

    This tests model adaptation:
    - Slack → Discord: Model gains editing, DMs, channel creation
    - Discord → Slack: Model loses these capabilities, must adapt
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)

    def _get_next_message_id(self) -> str:
        """Generate next message ID."""
        mid = self.state["next_message_id"]
        self.state["next_message_id"] += 1
        return f"M{mid:06d}"

    def _get_next_channel_id(self) -> str:
        """Generate next channel ID."""
        cid = self.state["next_channel_id"]
        self.state["next_channel_id"] += 1
        return f"CH{cid:03d}"

    # =========================================================================
    # OVERLAPPING TOOLS (similar to Slack)
    # =========================================================================

    # Tool 1: list_channels (overlaps with slack_list_channels)
    def list_channels(self) -> Dict[str, Any]:
        """
        List all text channels in the Discord server.

        Returns all available channels with their names, topics, and IDs.

        Returns:
            dict: List of server channels
        """
        return {
            "success": True,
            "channels": [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "type": ch["type"],
                    "topic": ch.get("topic", ""),
                    "category_id": ch.get("category_id"),
                }
                for ch in self.state["channels"]
            ],
        }

    # Tool 2: send_message (overlaps with slack_post_message)
    def send_message(
        self,
        channel_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send a message to a Discord channel.

        Posts a new message to the specified channel.

        Args:
            channel_id (str): Channel ID to send message to
            content (str): Message content

        Returns:
            dict: Sent message details
        """
        # Find channel
        channel = None
        for ch in self.state["channels"]:
            if ch["id"] == channel_id or ch["name"] == channel_id:
                channel = ch
                break

        if not channel:
            return {"success": False, "error": f"Channel '{channel_id}' not found"}

        channel_id = channel["id"]
        if channel_id not in self.state["messages"]:
            self.state["messages"][channel_id] = []

        message_id = self._get_next_message_id()
        new_message = {
            "id": message_id,
            "author_id": "BOT",
            "content": content,
            "timestamp": "2024-01-20T12:00:00Z",
            "reactions": [],
        }
        self.state["messages"][channel_id].append(new_message)

        return {
            "success": True,
            "message": {
                "id": message_id,
                "channel_id": channel_id,
                "content": content,
            },
        }

    # Tool 3: read_messages (overlaps with slack_get_channel_history)
    def read_messages(
        self,
        channel_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Read recent messages from a Discord channel.

        Retrieves message history including content, authors, and reactions.

        Args:
            channel_id (str): Channel ID to read from
            limit (int): Maximum messages to return

        Returns:
            dict: List of recent messages
        """
        # Find channel
        channel = None
        for ch in self.state["channels"]:
            if ch["id"] == channel_id or ch["name"] == channel_id:
                channel = ch
                break

        if not channel:
            return {"success": False, "error": f"Channel '{channel_id}' not found"}

        channel_id = channel["id"]
        messages = self.state["messages"].get(channel_id, [])

        return {
            "success": True,
            "messages": [
                {
                    "id": msg["id"],
                    "author_id": msg["author_id"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"],
                    "reactions": msg.get("reactions", []),
                }
                for msg in messages[-limit:]
            ],
        }

    # Tool 4: add_reaction (overlaps with slack_add_reaction)
    def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> Dict[str, Any]:
        """
        Add an emoji reaction to a Discord message.

        Args:
            channel_id (str): Channel containing the message
            message_id (str): Message ID to react to
            emoji (str): Emoji to add (e.g., "👍" or ":thumbsup:")

        Returns:
            dict: Reaction result
        """
        # Find channel
        channel = None
        for ch in self.state["channels"]:
            if ch["id"] == channel_id or ch["name"] == channel_id:
                channel = ch
                break

        if not channel:
            return {"success": False, "error": f"Channel '{channel_id}' not found"}

        channel_id = channel["id"]
        if channel_id not in self.state["messages"]:
            return {"success": False, "error": "Channel has no messages"}

        # Find message
        for msg in self.state["messages"][channel_id]:
            if msg["id"] == message_id:
                # Check if reaction exists
                for r in msg["reactions"]:
                    if r["emoji"] == emoji:
                        r["count"] += 1
                        return {"success": True}

                msg["reactions"].append({"emoji": emoji, "count": 1})
                return {"success": True}

        return {"success": False, "error": f"Message '{message_id}' not found"}

    # Tool 5: get_user_id_by_name (overlaps with slack_get_users/slack_get_user_profile)
    def get_user_id_by_name(
        self,
        username: str
    ) -> Dict[str, Any]:
        """
        Find a Discord user by their username.

        Searches for a user and returns their ID for mentions or DMs.

        Args:
            username (str): Username to search for

        Returns:
            dict: User ID and basic info
        """
        username_lower = username.lower()
        for user in self.state["users"]:
            if (user["username"].lower() == username_lower or
                user["display_name"].lower() == username_lower):
                return {
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "display_name": user["display_name"],
                    },
                }

        return {"success": False, "error": f"User '{username}' not found"}

    # =========================================================================
    # DISCORD-ONLY TOOLS (Slack can't do these)
    # =========================================================================

    # Tool 6: edit_message (Discord-only)
    def edit_message(
        self,
        channel_id: str,
        message_id: str,
        new_content: str
    ) -> Dict[str, Any]:
        """
        Edit an existing Discord message.

        Modifies the content of a previously sent message.
        NOTE: This capability is NOT available in Slack!

        Args:
            channel_id (str): Channel containing the message
            message_id (str): Message ID to edit
            new_content (str): New message content

        Returns:
            dict: Updated message details
        """
        # Find channel
        channel = None
        for ch in self.state["channels"]:
            if ch["id"] == channel_id or ch["name"] == channel_id:
                channel = ch
                break

        if not channel:
            return {"success": False, "error": f"Channel '{channel_id}' not found"}

        channel_id = channel["id"]
        if channel_id not in self.state["messages"]:
            return {"success": False, "error": "Channel has no messages"}

        # Find and edit message
        for msg in self.state["messages"][channel_id]:
            if msg["id"] == message_id:
                msg["content"] = new_content
                msg["edited_timestamp"] = "2024-01-20T12:30:00Z"
                return {
                    "success": True,
                    "message": {
                        "id": message_id,
                        "content": new_content,
                        "edited": True,
                    },
                }

        return {"success": False, "error": f"Message '{message_id}' not found"}

    # Tool 7: delete_message (Discord-only)
    def delete_message(
        self,
        channel_id: str,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Delete a Discord message.

        Permanently removes a message from the channel.
        NOTE: This capability is NOT available in Slack!

        Args:
            channel_id (str): Channel containing the message
            message_id (str): Message ID to delete

        Returns:
            dict: Deletion result
        """
        # Find channel
        channel = None
        for ch in self.state["channels"]:
            if ch["id"] == channel_id or ch["name"] == channel_id:
                channel = ch
                break

        if not channel:
            return {"success": False, "error": f"Channel '{channel_id}' not found"}

        channel_id = channel["id"]
        if channel_id not in self.state["messages"]:
            return {"success": False, "error": "Channel has no messages"}

        # Find and delete message
        messages = self.state["messages"][channel_id]
        for i, msg in enumerate(messages):
            if msg["id"] == message_id:
                del messages[i]
                return {"success": True, "deleted": True}

        return {"success": False, "error": f"Message '{message_id}' not found"}

    # Tool 8: send_private_message (Discord-only)
    def send_private_message(
        self,
        user_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send a direct message to a Discord user.

        Sends a private message that only the recipient can see.
        NOTE: This capability is NOT available in Slack MCP!

        Args:
            user_id (str): User ID to message
            content (str): Message content

        Returns:
            dict: Sent DM details
        """
        # Verify user exists
        user = None
        for u in self.state["users"]:
            if u["id"] == user_id or u["username"] == user_id:
                user = u
                break

        if not user:
            return {"success": False, "error": f"User '{user_id}' not found"}

        user_id = user["id"]
        if user_id not in self.state["direct_messages"]:
            self.state["direct_messages"][user_id] = []

        message_id = self._get_next_message_id()
        new_dm = {
            "id": message_id,
            "content": content,
            "timestamp": "2024-01-20T12:00:00Z",
        }
        self.state["direct_messages"][user_id].append(new_dm)

        return {
            "success": True,
            "message": {
                "id": message_id,
                "recipient_id": user_id,
                "content": content,
            },
        }

    # Tool 9: create_text_channel (Discord-only)
    def create_text_channel(
        self,
        name: str,
        topic: str = "",
        category_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a new text channel in the Discord server.

        Creates a new channel that all members can see and use.
        NOTE: This capability is NOT available in Slack MCP!

        Args:
            name (str): Channel name (will be lowercased, spaces to dashes)
            topic (str): Channel topic/description
            category_id (str): Optional category to place channel in

        Returns:
            dict: Created channel details
        """
        # Normalize channel name
        normalized_name = name.lower().replace(" ", "-")

        # Check if channel already exists
        for ch in self.state["channels"]:
            if ch["name"] == normalized_name:
                return {"success": False, "error": f"Channel '{normalized_name}' already exists"}

        channel_id = self._get_next_channel_id()
        new_channel = {
            "id": channel_id,
            "name": normalized_name,
            "type": "text",
            "topic": topic,
            "category_id": category_id,
        }
        self.state["channels"].append(new_channel)
        self.state["messages"][channel_id] = []

        return {
            "success": True,
            "channel": {
                "id": channel_id,
                "name": normalized_name,
                "topic": topic,
            },
        }

    # Tool 10: get_server_info (Discord-only)
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the Discord server.

        Returns server name, member count, and other details.

        Returns:
            dict: Server information
        """
        server = self.state["server"]
        return {
            "success": True,
            "server": {
                "id": server["id"],
                "name": server["name"],
                "member_count": server["member_count"],
                "owner_id": server["owner_id"],
                "channel_count": len(self.state["channels"]),
            },
        }
