# Using OfflineIMAP with M365

This instruction describes how [OfflineIMAP](https://www.offlineimap.org/) can be used with an IMAP-enabled Exchange Online (M365) environment using OAuth2. Note that the tenant must be configured to support IMAP over 'modern authentication' and that it requires app consent to be granted for a mail app for which you have the client ID and secret. 

A variation of the below should work with any OAuth-enabled mail client or script. 

## Step 1: get a client ID/secret
In order to connect to Azure AD for authentication, you need a client ID and secret (an "app registration" in AAD). Confusingly, the client secret doesn't actually need to be a secret (a client app like a mail client can't keep secrets, after all). You can your own app registration, or use an existing one such as Thunderbird's, which is [publicly available](https://hg.mozilla.org/comm-central/file/tip/mailnews/base/src/OAuth2Providers.jsm) (see the `login.microsoft.com` section). Whatever client ID you use, it will need to have been granted the `IMAP.AccessAsUser.All` permission in your M365 tenant.  

## Step 2: get a token
Since OfflineIMAP doesn't support an interactive flow for getting a token, you need to do this step yourself. You can use `get_token.py` for this purpose, which uses Microsoft's [MSAL](https://docs.microsoft.com/en-us/azure/active-directory/develop/msal-overview) wrapper library to perform the OAuth2 flow:

```sh
git clone https://github.com/UvA-FNWI/M365-IMAP
cd M365-IMAP
pip install msal
# add the client ID and secret from step 1 to config.py 
python3 get_token.py
```

Follow the instructions to obtain a `refresh_token` file containing an AAD refresh token. Note that the token allows access to your full mailbox (in combination with the client 'secret') and hence should be stored securely. 

## Step 3: configure OfflineIMAP
Edit your `.offlineimaprc` file so that your remote repository section looks like this:

```ini
[Repository Remote]
type = IMAP
sslcacertfile = <path to CA certificates>
remotehost = outlook.office365.com 
remoteuser = <your M365 email address>
auth_mechanisms = XOAUTH2
oauth2_request_url = https://login.microsoftonline.com/common/oauth2/v2.0/token
oauth2_client_id = <the client ID from step 1>
oauth2_client_secret = <the client secret from step 1>
oauth2_refresh_token = <the contents of the refresh_token file from step 2>
```
