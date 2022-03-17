from msal import ConfidentialClientApplication, SerializableTokenCache
import config
import sys

redirect_uri = "http://localhost"

# We use the cache to extract the refresh token
cache = SerializableTokenCache()
app = ConfidentialClientApplication(config.ClientId, client_credential=config.ClientSecret, token_cache=cache)

url = app.get_authorization_request_url(config.Scopes, redirect_uri=redirect_uri)

print('Navigate to the following url in a web browser:')
print(url)

print()

print('After login, you will be redirected to a blank (or error) page with a url containing an access code. Paste the url below.')
resp = input('Response url: ')

i = resp.find('code') + 5
code = resp[i : resp.find('&', i)] if i > 4 else resp

token = app.acquire_token_by_authorization_code(code, config.Scopes, redirect_uri=redirect_uri)

print()

if 'error' in token:
    print(token)
    sys.exit("Failed to get access token")

with open(config.RefreshTokenFileName, 'w') as f:
    print(f'Refresh token acquired, writing to file {config.RefreshTokenFileName}')
    f.write(token['refresh_token'])

with open(config.AccessTokenFileName, 'w') as f:
    print(f'Access token acquired, writing to file {config.AccessTokenFileName}')
    f.write(token['access_token'])
