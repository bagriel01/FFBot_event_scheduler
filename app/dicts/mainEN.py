START = """
Welcome and thank you for using FFBot! To get started, add me to your group and grant me administrator permissions. I promise I won't do anything malicious, uwu.
"""

PING = """
Bot is online.
Date: {}
Current bot version: 3.1.1 (Apricot-Pie)
"""

HELP = """
📨 */FFPost*
    Use this command to schedule an event post.
    There are two ways to use it:

    • Reply to the event message in the group with /FFPost — the bot will contact you via DM to finish the process;
    • Forward the event message directly to the bot's DM.

    In the DM, the bot will ask for the event date and time in the format MM/DD/YYYY \\- HH:MM and send the post for approval.

📅 */FFThisMonth*
    Displays this month's published events.

🗑️ */FFRemove*
    Reply to the original event message with this command to remove it from the channel and the schedule.

⛔️ */cancel*
    Cancels the current operation.

🏓 */FFPing*
    Checks whether the bot is online and displays the current version.

🔐 */FFPrivacy*
    Displays the bot's privacy policy.

⚠️ *Notes:*
    • /FFPost only works in groups — or by forwarding an event directly to the bot's DM.
    • /FFThisMonth can be used by group administrators or by any user in the bot's DM.
    • Only group administrators may use group management commands.
"""

PRIVACY = """
Privacy Policy

This bot collects the minimum amount of information required to operate correctly, such as user IDs and submitted messages. The collected information is used solely for operational purposes and is never shared with third parties.

By using this bot, you agree to this privacy policy.

https://telegram.org/privacy/br#6-mensagens-de-bot

The bot administrator is not responsible for any events advertised through this bot. If any issues occur during an event, please contact the developer at @thenightweaver.
"""

HANDLER_ADD_TO_GROUP = """
Thank you for adding me to your group! If you need help using the bot, run /FFHelp or contact the developer at @thenightweaver.
"""