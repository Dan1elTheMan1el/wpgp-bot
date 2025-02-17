### Version 1.2.3

# Features

After installing, the bot will automatically monitor the heartbeat channel and determine which discord members are actively rerolling or not. Then, it will assign roles and update an `ids.txt` file on github, which is referenced by all AHK Farmers in the server! This allows for seamless joining/leaving sessions with no interaction apart from starting / stopping the ahk script.

The bot also organizes all user data into one discord channel, summarizing packs found, hours grinded, instances running, etc.

# Usage Instructions

## AHK Setup

- Friend ID: `https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/ids.txt`

- Discord ID: *User's discord ID*

- Discord Webhook URL: *Webhook created in Pack Alert channel*

- Discord Heartbeat: ✅
    - Name: *User's discord ID*
    - Webhook URL: *Webhook created in Heartbeat channel*

## Commands

- **/profile set `friend_code`**
    - Connect PTCGP friend code to discord ID

- **/profile get `discord_id`**
    - Display information about user:
        - Friend code
        - Status/ last active time
        - Total time farmed
        - Total packs farmed
        - Last recorded number of running instances

- **/profile manage `discord_id` `param` `value`** *(Admin only)*
    - Edit a user's friend code, activity status, or time active
    - Value must be `true` or `false` for activity status

- **/usernames**
    - Generates a file with 200 numbered usernames to use in your ahk folder for better alt identification

- **/offline**
    - Manual switch to turn your activity off, since bot can only update ~30min after last heartbeat

- **/gp_status `status`**
    - Used in pack thread - changes thread tag to dead or alive

# Installation Instructions

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git
- Discord server with:
    - Separate channels for both webhooks (Heartbeat, Packs)
    - Forum channel (For threads)
        - Three tags in said channel (alive, dead, and unknown)
    - Active and Inactive user roles
    - Status channel for bot to store stats

## Step 1: Clone the Repository
```bash
git clone https://github.com/Dan1elTheMan1el/wpgp-bot.git
```

## Step 2: Create a GitHub Repository / Token
1. Go to [GitHub](https://github.com) and log in to your account.
2. Click on the "+" icon in the top right corner and select "New repository".
3. Name your repository and click "Create repository".
4. In the root directory of this repository, create a file named `ids.txt` (Leave empty).
5. Create a GitHub fine-grained personal access token with `repo` scope by following [these instructions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token).
6. Under the "TOKEN" section, click "Copy" to copy your bot token. You will need these details for the `.env` file.

## Step 3: Create a Discord Application
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click on "New Application".
3. Name your application and click "Create".
4. Navigate to the "Bot" tab on the left sidebar.
5. Click "Add Bot" and confirm by clicking "Yes, do it!".
6. Under the "TOKEN" section, click "Copy" to copy your bot token. You will need this for the `.env` file.

## Step 4: Create the `.env` File
1. In the root directory of the cloned repository, create a file named `.env`.
2. Open the `.env` file and add the following lines (REPLACE FIELDS):
    ```
    DISCORD_TOKEN=discord_bot_token
    GUILD=discord_server_id
    HEARTBEAT=heartbeat_channel_id
    PACKALERT=webhook_channel_id
    STATUS=status_channel_id

    PACKFORUM=pack_forum_channel_id
    PACKTAG=unknown_pack_tag_id
    PACKLIVETAG=live_pack_tag_id
    PACKDEADTAG=dead_pack_tag_id

    GITHUB_TOKEN=github_token
    GITHUB_USER=your_username
    GITHUB_REPO=your_repo
    GITHUB_FILEPATH=ids.txt
    ```

## Step 5: Install Dependencies
- py-cord (v2.0+, see documentation for install)
- python-dotenv
- requests

## Step 6: Run the Bot
```bash
python wpgp-bot.py
```

Your bot should now be running and connected to your Discord server!
