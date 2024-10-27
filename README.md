# Discord Boost Bot

A powerful Discord bot designed to manage server boosts using Discord tokens. This bot allows for easy token management and server boosting with commands for adding, removing, and listing tokens.

## Features

- **Automatic Boosting**: Use tokens to boost specified servers with minimal effort.
- **Token Management**: Easily add, remove, and list boost tokens with bot commands.
- **Nickname & Profile Picture Customization**: Customize user nicknames and profile pictures within servers.
- **Authorization & Guild Joining**: Automate the joining and authorization process for boosted accounts.

## Setup

1. **Clone the repository**:
   ```bash
   cd your-repo
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Your Bot**:
   - Update `BOT_TOKEN`, `CLIENT_SECRET`, and `CLIENT_ID` in `main.py` with your Discord bot details.
   - Set any specific guild IDs, nickname preferences, or profile pictures you want.

4. **Run the Bot**:
   ```bash
   python main.py
   ```

## Commands

| Command            | Description                                          |
|--------------------|------------------------------------------------------|
| `/operate`         | Begin boost operations with tokens for a specified server. |
| `/add_token`       | Add a boost token.                                   |
| `/remove_token`    | Remove a boost token.                                |
| `/list_tokens`     | List all available boost tokens.                     |

## Donation

If you'd like to support this project, donations are greatly appreciated! Every bit helps with further development and maintenance.

**Litecoin Address**: `ltc1qcuc2ufpvylaas7s6prdhsp97gc8dvp9rg5a28j`

Thank you for your support!
