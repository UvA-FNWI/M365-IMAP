# Using Microsoft 365 IMAP/SMTP with OAuth2

This repository provides instructions and small helper scripts to obtain and refresh OAuth2 tokens for Microsoft 365.  
You can then use these with:
- **[offlineimap3](https://github.com/OfflineIMAP/offlineimap3)** to read/sync your mailbox via IMAP
- **[msmtp](https://wiki.debian.org/msmtp)** (or similar) to send mail via SMTP
- **[mutt](http://www.mutt.org/)** to do both
- a small Python demo script (`demo.py`) that shows both.

The basic idea:
1. Use `get_token.py` once to log in via a browser and obtain an initial **refresh token**.
2. Use `refresh_token.py` whenever you need a new **access token**.
3. Configure your IMAP/SMTP tools to authenticate with XOAUTH2 using that access token.

Your Microsoft 365 tenant must be configured to allow IMAP/SMTP with modern authentication, and your admin must grant permissions for the chosen client ID.

---
## Choosing a client ID
There are two options.

### 1. Use Thunderbird’s public client ID (no secret)
Thunderbird uses a public Azure AD application with:
```text
Client ID:     9e5f94bc-e8a4-4e73-b8be-63364c29d753
```
Note that the updated version doesn't rely on a "client secret" any longer.
Your organisation’s admin must once approve this app for your tenant, granting at least:
- `IMAP.AccessAsUser.All`
- `SMTP.Send`
- `offline_access`

Note that there isn't a hard connection to, for instance, Thunderbird's Azure Client ID, meaning that you could use the same ID for other tools as well (offlineimap3, msmtp, scripts).

### 2. Use your own Azure AD app registration
If you manage Azure AD yourself, you can create a dedicated app registration and grant it the same permissions.

In that case, set in `config.py`:
```python
ClientId = "<your client id>"
ClientSecret = "<your client secret>"
```
The rest of the instructions stay the same. Again, notice that not all applications need both (like Thunderbird).

---
## Obtaining auth tokens
### Step 1: initial login (`get_token.py`)
Modify `config.py` so `ClientId` (and optionally `ClientSecret`) match the client you want to use.

Then run:
```bash
pip install -r requirements.txt
python3 get_token.py
```
What happens:
1. A browser window/tab opens to the Microsoft 365 login page.
2. You sign in with your M365 account.
3. After login you are redirected to `https://localhost:7598/`.
4. `get_token.py` captures the authorization code and exchanges it for tokens (see the terminal as well).

Note that you could see some irrelevant warnings related to certificates in the terminal.

The script writes two files in the repository directory:
- `imap_smtp_refresh_token` – **refresh token**, long‑lived
- `imap_smtp_access_token` – **access token**, short‑lived

If the automatic browser/open redirect does not work (e.g. over SSH), the script asks you to paste the final URL manually.

You normally only need to run `get_token.py` once per account/client combination.

### Step 2: refreshing tokens (`refresh_token.py`)
When you need a fresh access token (for SMTP or your own scripts), run:
```bash
python3 refresh_token.py
```
This script:
- reads the refresh token from `imap_smtp_refresh_token`
- requests a new access token
- updates `imap_smtp_refresh_token` with the new refresh token
- prints the new access token to stdout

IMAP/SMTP clients can call this script as a `passwordeval`/`passwordcmd` to always send a valid access token.

---
## Using offlineimap3
Install offlineimap3 (e.g. via pip or your distro):
```bash
pip install offlineimap3
```
Create or edit `~/.offlineimaprc` with a minimal configuration like:
```ini
[general]
accounts = M365

[Account M365]
localrepository  = Local
remoterepository = Remote

[Repository Local]
type         = Maildir
localfolders = ~/Maildir

[Repository Remote]
type = IMAP
remotehost = outlook.office365.com
remoteuser = <your M365 email>
ssl = yes

# OAuth2 settings
auth_mechanisms    = XOAUTH2
oauth2_request_url = https://login.microsoftonline.com/common/oauth2/v2.0/token

# Thunderbird client ID (no secret)
oauth2_client_id     = 9e5f94bc-e8a4-4e73-b8be-63364c29d753
oauth2_client_secret =

# Contents of the file written by get_token.py
oauth2_refresh_token = <contents of imap_smtp_refresh_token>

# Optional: skip non‑mail folders
# folderfilter = lambda folder: not folder.startswith('Calendar') and not folder.startswith('Contacts')
```
Then run:
```bash
offlineimap3
```
to synchronise your mailbox into `~/Maildir`.

If you use your own Azure app instead of Thunderbird’s, just replace `oauth2_client_id` and `oauth2_client_secret` accordingly.

---
## Using msmtp
Install msmtp and create `~/.msmtprc`:
```ini
account m365
host smtp.office365.com
port 587
tls on
tls_starttls on

from <your M365 email>
user <your M365 email>
auth xoauth2

# Always get a fresh access token
passwordeval "python3 /path/to/refresh_token.py"
```
Send a test message with:
```bash
echo "Test" | msmtp -a m365 someone@example.com
```

Any other SMTP client that can run an external command to obtain the password can use the same pattern: call `refresh_token.py` and treat the printed access token as the XOAUTH2 password.

---
## Using mutt
Install mutt and config `~/.muttrc`:
```bash
set imap_user = <your M365 email>
set folder = imaps://${imap_user}@outlook.office365.com:993/
set imap_authenticators = "xoauth2"
set imap_oauth_refresh_command = "python3 /path/to/refresh_token.py"
set smtp_url = smtp://${imap_user}@smtp.office365.com:587
set smtp_authenticators = "xoauth2"
set smtp_oauth_refresh_command = ${imap_oauth_refresh_command}
```

---
## Python demo client (`demo.py`)
`demo.py` is a small example script that reuses the same tokens (scripts) to access your mailbox from the local terminal.

Usage:
```bash
python3 demo.py
```
The script will:
1. Ask you to choose `inbox` or `message`.
2. For `inbox`: fetch and print the 15 most recent emails from your INBOX using IMAP + XOAUTH2.
3. For `message`: prompt for recipients, subject and body, then send the mail via SMTP + XOAUTH2.

Internally it uses the same refresh‑token mechanism as `refresh_token.py` and connects directly to:
- `outlook.office365.com` (IMAP)
- `smtp.office365.com` (SMTP)

This is meant as a simple, readable example of how to apply the access and refresh tokens from AD.

---
## Security notes
- The refresh token in `imap_smtp_refresh_token` grants full access to your mailbox for the configured app. Protect this file using the right permissions, encryption, keyring, etc.
- Treat access tokens like passwords; they are short‑lived but still sensitive.
- If a token is compromised, revoke access by removing the app’s consent in Azure AD and re‑running `get_token.py`.

---
## Files in this repository
- `config.py`          – client ID/secret and scope configuration
- `get_token.py`       – run once to obtain initial refresh/access tokens
- `refresh_token.py`   – refreshes the access token and updates the refresh token
- `demo.py`            – simple IMAP/SMTP demo (inbox listing + send mail)
- `imap_smtp_refresh_token` / `imap_smtp_access_token` – token storage files
- `requirements.txt`   – Python dependencies (MSAL)

