[![ErisProtect Banner](https://raw.githubusercontent.com/cymon4380/ErisProtect/master/assets/img/banner.png)](https://discord.gg/EmpnUU5EE7)

<p align="center">
    <a href="https://discord.gg/EmpnUU5EE7"><img src="https://img.shields.io/discord/1136258983565480067?style=flat-square&color=5865f2&logo=discord&logoColor=ffffff&label=discord" alt="Discord server invite" /></a>
    <img src="https://img.shields.io/badge/version-0.2.0-252525?style=flat-square" alt="Version" />
</p>


**ErisProtect** is an open source Discord bot designed to help with protection servers from damage. You can contribute and help us improve it.

## What can ErisProtect do?
**Here are the features that will likely be added to the bot before version 1.0.**

- `0.1` Anti-nuke
- `0.5` User verification (CAPTCHA, Anti-VPN)
- `0.5` Anti-alternative-accounts
- `0.3` Server backups
- `0.4` Quarantine
- `0.2` Improved punishment system

**You can learn more about new versions in our Discord server.**

## How to install the bot?
ErisProtect requires **Python 3.10** and **MongoDB 6.0** to run. Install all libraries from `requirements.txt` and specify `DISCORD_TOKEN` and `MONGO_AUTH_STRING` in environment variables. Then edit the `config.json` file and run the bot using `main.py`.
Your bot must have the **Server Members** and **Message Content** privileged gateway intents.

**Please run the bot from the `src` directory. Otherwise, you will get an error!**

---

**Keep in mind that no one bot can fully protect your server. They can only help you with protection. You shouldn't add unknown bots to your server and grant dangerous permissions to unknown members.**