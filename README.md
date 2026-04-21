the FFBot (FruityFur Bot) is an event scheduling assistant for Fur Meets and Furry Events. It helps group admins create event posts, pin them in the group, request approval by DM, and then publish approved events into a central channel.

Features:
`/FFPost`
- Group admin replies to an existing message with `/FFPost` to pin it and send for approval.
- The bot forwards the message to configured admins for approval.
- After approval, the message is forwarded to the channel.
  
`/FFThisMonth`
- Allows group admins to forward the posts for events scheduled at this month

Config:
- `BOT_TOKEN` - Telegram bot token.
- `APPROVED_EVENT_CHANNEL_ID` - channel where approved events will be posted.
- `ADMIN_USER_IDS` - comma-separated Telegram user IDs that receive approval requests by DM.

Setup:
1. Create a .env file with the required variables.
2. Install dependencies: pip install python-telegram-bot python-dotenv
3. Run with python run.py

Current version is 1.1L(Banana)

