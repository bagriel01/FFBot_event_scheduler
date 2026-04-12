the FFBot (FruityFur Bot) is an event scheduling assistant for Fur Meets and Furry Events. It helps group admins create event posts, pin them in the group, request approval by DM, and then publish approved events into a central channel.

Current flow:
- Group admin sends `/FFPost` in a group.
- The bot collects event name, description, date/time, location, and pictures.
- The event post includes the group address when available (for example, `t.me/something`).
- The bot sends an approval request by DM to the configured `ADMIN_USER_IDS`.
- After approval, the event is published to `APPROVED_EVENT_CHANNEL_ID`.

Config:
- `BOT_TOKEN` - Telegram bot token.
- `APPROVED_EVENT_CHANNEL_ID` - channel where approved events will be posted.
- `ADMIN_USER_IDS` - comma-separated Telegram user IDs that receive approval requests by DM.

At this moment, on version 1.0, the bot is simplified with no persistence in its core. Persistence will be added later and new features will follow!

