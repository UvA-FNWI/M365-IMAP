from msal import ConfidentialClientApplication, SerializableTokenCache
import config
import sys

print_access_token = True

# We use the cache to extract the refresh token
cache = SerializableTokenCache()
app = ConfidentialClientApplication(config.ClientId, client_credential=config.ClientSecret, token_cache=cache)


old_refresh_token = open(config.RefreshTokenFileName,'r').read()

token = app.acquire_token_by_refresh_token(old_refresh_token,config.Scopes)

if 'error' in token:
    print(token)
    sys.exit("Failed to get access token")

# you're supposed to save the old refresh token each time
with open(config.RefreshTokenFileName, 'w') as f:
    #f.write(cache.find('RefreshToken')[0]['secret'])
    f.write(token['refresh_token'])

with open(config.AccessTokenFileName, 'w') as f:
    f.write(token['access_token'])
    if print_access_token:
        print(token['access_token'])
