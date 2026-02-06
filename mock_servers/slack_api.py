# Slack MCP Server Mock
# Based on real Slack MCP server from modelcontextprotocol/servers
#
# Slack has 8 tools:
#   1. slack_list_channels - List public channels
#   2. slack_post_message - Post a message to a channel
#   3. slack_reply_to_thread - Reply to a thread
#   4. slack_add_reaction - Add emoji reaction
#   5. slack_get_channel_history - Get channel message history
#   6. slack_get_thread_replies - Get thread replies
#   7. slack_get_users - List workspace users
#   8. slack_get_user_profile - Get user profile info
#
# Discord has more tools (24), so Slack → Discord tests adaptation to richer toolset,
# while Discord → Slack tests working with fewer capabilities (no DMs, webhooks, editing).

from typing import Dict, Any, Optional, List

DEFAULT_STATE = {
    "workspace": {
        "name": "Acme Corp",
        "domain": "acme-corp",
    },
    "channels": [
        {
            "id": "C001",
            "name": "general",
            "is_private": False,
            "topic": "Company-wide announcements",
            "purpose": "General discussion for the whole team",
            "num_members": 150,
        },
        {
            "id": "C002",
            "name": "engineering",
            "is_private": False,
            "topic": "Engineering team discussions",
            "purpose": "Technical discussions and updates",
            "num_members": 45,
        },
        {
            "id": "C003",
            "name": "random",
            "is_private": False,
            "topic": "Non-work banter",
            "purpose": "Water cooler chat",
            "num_members": 120,
        },
    ],
    "users": [
        {
            "id": "U001",
            "name": "alice",
            "real_name": "Alice Johnson",
            "email": "alice@acme.com",
            "title": "Senior Engineer",
            "status_text": "Working from home",
            "status_emoji": ":house:",
        },
        {
            "id": "U002",
            "name": "bob",
            "real_name": "Bob Smith",
            "email": "bob@acme.com",
            "title": "Product Manager",
            "status_text": "In meetings",
            "status_emoji": ":calendar:",
        },
        {
            "id": "U003",
            "name": "carol",
            "real_name": "Carol Williams",
            "email": "carol@acme.com",
            "title": "Designer",
            "status_text": "",
            "status_emoji": "",
        },
    ],
    "messages": {
        "C001": [
            {
                "ts": "1705320000.000001",
                "user": "U001",
                "text": "Good morning everyone!",
                "reactions": [{"name": "wave", "count": 5}],
                "thread_ts": None,
            },
            {
                "ts": "1705320060.000002",
                "user": "U002",
                "text": "Morning! Don't forget the all-hands at 2pm",
                "reactions": [],
                "thread_ts": None,
            },
        ],
        "C002": [
            {
                "ts": "1705319000.000001",
                "user": "U001",
                "text": "PR review needed: https://github.com/acme/app/pull/123",
                "reactions": [{"name": "eyes", "count": 2}],
                "thread_ts": None,
                "replies": [
                    {
                        "ts": "1705319100.000002",
                        "user": "U003",
                        "text": "I'll take a look!",
                        "thread_ts": "1705319000.000001",
                    },
                ],
            },
        ],
    },
    "next_ts": 1705400000,
}


class SlackAPI:
    """
    Mock Slack MCP Server.

    STANDARD TOOL SET (8 tools) - Focused on channels and threads.

    Available tools:
    - slack_list_channels: List public channels in workspace
    - slack_post_message: Post a message to a channel
    - slack_reply_to_thread: Reply to a message thread
    - slack_add_reaction: Add emoji reaction to a message
    - slack_get_channel_history: Get recent messages from a channel
    - slack_get_thread_replies: Get replies in a thread
    - slack_get_users: List users in workspace
    - slack_get_user_profile: Get detailed user profile

    NOT available (unlike Discord):
    - No direct messages (DMs)
    - No message editing or deletion
    - No webhooks
    - No channel creation/deletion
    - No categories
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)

    def _get_next_ts(self) -> str:
        """Generate next message timestamp."""
        ts = self.state["next_ts"]
        self.state["next_ts"] += 1
        return f"{ts}.000001"

    # =========================================================================
    # Tool 1: slack_list_channels
    # =========================================================================

    def slack_list_channels(
        self,
        limit: int = 100,
        cursor: str = None
    ) -> Dict[str, Any]:
        """
        List public channels in the Slack workspace.

        Returns a list of all public channels with their names, topics,
        purposes, and member counts.

        Args:
            limit (int): Maximum number of channels to return
            cursor (str): Pagination cursor for next page

        Returns:
            dict: List of channels with metadata
        """
        channels = self.state["channels"]

        return {
            "ok": True,
            "channels": [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "is_private": ch["is_private"],
                    "topic": {"value": ch["topic"]},
                    "purpose": {"value": ch["purpose"]},
                    "num_members": ch["num_members"],
                }
                for ch in channels[:limit]
            ],
        }

    # =========================================================================
    # Tool 2: slack_post_message
    # =========================================================================

    def slack_post_message(
        self,
        channel: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Post a new message to a Slack channel.

        Sends a message to the specified channel. The channel can be
        specified by ID (C001) or name (general).

        Args:
            channel (str): Channel ID or name to post to
            text (str): Message text to post

        Returns:
            dict: Posted message details with timestamp
        """
        # Find channel by ID or name
        channel_id = None
        for ch in self.state["channels"]:
            if ch["id"] == channel or ch["name"] == channel:
                channel_id = ch["id"]
                break

        if not channel_id:
            return {"ok": False, "error": f"Channel '{channel}' not found"}

        if channel_id not in self.state["messages"]:
            self.state["messages"][channel_id] = []

        ts = self._get_next_ts()
        new_message = {
            "ts": ts,
            "user": "U000",  # Bot user
            "text": text,
            "reactions": [],
            "thread_ts": None,
        }
        self.state["messages"][channel_id].append(new_message)

        return {
            "ok": True,
            "channel": channel_id,
            "ts": ts,
            "message": {
                "text": text,
                "ts": ts,
            },
        }

    # =========================================================================
    # Tool 3: slack_reply_to_thread
    # =========================================================================

    def slack_reply_to_thread(
        self,
        channel: str,
        thread_ts: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Reply to a message thread in Slack.

        Posts a reply to an existing message thread. The thread is identified
        by the original message's timestamp (thread_ts).

        Args:
            channel (str): Channel ID or name
            thread_ts (str): Timestamp of the parent message
            text (str): Reply text

        Returns:
            dict: Posted reply details
        """
        # Find channel
        channel_id = None
        for ch in self.state["channels"]:
            if ch["id"] == channel or ch["name"] == channel:
                channel_id = ch["id"]
                break

        if not channel_id:
            return {"ok": False, "error": f"Channel '{channel}' not found"}

        if channel_id not in self.state["messages"]:
            return {"ok": False, "error": "Channel has no messages"}

        # Find parent message
        parent_found = False
        for msg in self.state["messages"][channel_id]:
            if msg["ts"] == thread_ts:
                parent_found = True
                if "replies" not in msg:
                    msg["replies"] = []

                reply_ts = self._get_next_ts()
                msg["replies"].append({
                    "ts": reply_ts,
                    "user": "U000",
                    "text": text,
                    "thread_ts": thread_ts,
                })

                return {
                    "ok": True,
                    "channel": channel_id,
                    "ts": reply_ts,
                    "message": {
                        "text": text,
                        "thread_ts": thread_ts,
                        "ts": reply_ts,
                    },
                }

        return {"ok": False, "error": f"Thread '{thread_ts}' not found"}

    # =========================================================================
    # Tool 4: slack_add_reaction
    # =========================================================================

    def slack_add_reaction(
        self,
        channel: str,
        timestamp: str,
        reaction: str
    ) -> Dict[str, Any]:
        """
        Add an emoji reaction to a message.

        Adds the specified emoji reaction to a message identified by its
        timestamp in the given channel.

        Args:
            channel (str): Channel ID or name
            timestamp (str): Message timestamp to react to
            reaction (str): Emoji name without colons (e.g., "thumbsup")

        Returns:
            dict: Reaction result
        """
        # Find channel
        channel_id = None
        for ch in self.state["channels"]:
            if ch["id"] == channel or ch["name"] == channel:
                channel_id = ch["id"]
                break

        if not channel_id:
            return {"ok": False, "error": f"Channel '{channel}' not found"}

        if channel_id not in self.state["messages"]:
            return {"ok": False, "error": "Channel has no messages"}

        # Find message and add reaction
        for msg in self.state["messages"][channel_id]:
            if msg["ts"] == timestamp:
                # Check if reaction exists
                for r in msg["reactions"]:
                    if r["name"] == reaction:
                        r["count"] += 1
                        return {"ok": True}

                msg["reactions"].append({"name": reaction, "count": 1})
                return {"ok": True}

        return {"ok": False, "error": f"Message '{timestamp}' not found"}

    # =========================================================================
    # Tool 5: slack_get_channel_history
    # =========================================================================

    def slack_get_channel_history(
        self,
        channel: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get recent messages from a Slack channel.

        Retrieves the message history for a channel, including message text,
        timestamps, authors, and reactions.

        Args:
            channel (str): Channel ID or name
            limit (int): Maximum number of messages to return

        Returns:
            dict: List of messages with metadata
        """
        # Find channel
        channel_id = None
        for ch in self.state["channels"]:
            if ch["id"] == channel or ch["name"] == channel:
                channel_id = ch["id"]
                break

        if not channel_id:
            return {"ok": False, "error": f"Channel '{channel}' not found"}

        messages = self.state["messages"].get(channel_id, [])

        return {
            "ok": True,
            "messages": [
                {
                    "ts": msg["ts"],
                    "user": msg["user"],
                    "text": msg["text"],
                    "reactions": msg.get("reactions", []),
                    "reply_count": len(msg.get("replies", [])),
                }
                for msg in messages[-limit:]
            ],
        }

    # =========================================================================
    # Tool 6: slack_get_thread_replies
    # =========================================================================

    def slack_get_thread_replies(
        self,
        channel: str,
        thread_ts: str
    ) -> Dict[str, Any]:
        """
        Get all replies in a message thread.

        Retrieves all replies to a parent message identified by its timestamp.

        Args:
            channel (str): Channel ID or name
            thread_ts (str): Timestamp of the parent message

        Returns:
            dict: List of thread replies
        """
        # Find channel
        channel_id = None
        for ch in self.state["channels"]:
            if ch["id"] == channel or ch["name"] == channel:
                channel_id = ch["id"]
                break

        if not channel_id:
            return {"ok": False, "error": f"Channel '{channel}' not found"}

        if channel_id not in self.state["messages"]:
            return {"ok": False, "error": "Channel has no messages"}

        # Find parent message
        for msg in self.state["messages"][channel_id]:
            if msg["ts"] == thread_ts:
                replies = msg.get("replies", [])
                return {
                    "ok": True,
                    "messages": [
                        {
                            "ts": r["ts"],
                            "user": r["user"],
                            "text": r["text"],
                            "thread_ts": r["thread_ts"],
                        }
                        for r in replies
                    ],
                }

        return {"ok": False, "error": f"Thread '{thread_ts}' not found"}

    # =========================================================================
    # Tool 7: slack_get_users
    # =========================================================================

    def slack_get_users(
        self,
        limit: int = 100,
        cursor: str = None
    ) -> Dict[str, Any]:
        """
        List users in the Slack workspace.

        Returns a list of all users with their basic information including
        ID, username, and real name.

        Args:
            limit (int): Maximum number of users to return
            cursor (str): Pagination cursor

        Returns:
            dict: List of workspace members
        """
        users = self.state["users"]

        return {
            "ok": True,
            "members": [
                {
                    "id": u["id"],
                    "name": u["name"],
                    "real_name": u["real_name"],
                }
                for u in users[:limit]
            ],
        }

    # =========================================================================
    # Tool 8: slack_get_user_profile
    # =========================================================================

    def slack_get_user_profile(
        self,
        user: str
    ) -> Dict[str, Any]:
        """
        Get detailed profile information for a user.

        Retrieves the full profile for a user including email, title,
        and current status.

        Args:
            user (str): User ID

        Returns:
            dict: User profile with detailed information
        """
        for u in self.state["users"]:
            if u["id"] == user or u["name"] == user:
                return {
                    "ok": True,
                    "profile": {
                        "real_name": u["real_name"],
                        "email": u["email"],
                        "title": u["title"],
                        "status_text": u["status_text"],
                        "status_emoji": u["status_emoji"],
                    },
                }

        return {"ok": False, "error": f"User '{user}' not found"}
