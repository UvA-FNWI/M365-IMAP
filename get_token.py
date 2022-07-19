from msal import ConfidentialClientApplication, SerializableTokenCache
import config
import http.server
import os
import sys
import threading
import urllib.parse
import webbrowser


redirect_uri = "http://localhost:8745/"

# We use the cache to extract the refresh token
cache = SerializableTokenCache()
app = ConfidentialClientApplication(config.ClientId, client_credential=config.ClientSecret, token_cache=cache, authority=config.Authority)

url = app.get_authorization_request_url(config.Scopes, redirect_uri=redirect_uri)

# webbrowser.open may fail silently
print("Navigate to the following url in a web browser, if doesn't open automatically:")
print(url)
try:
    webbrowser.open(url)
except Exception:
    pass


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        parsed_query = urllib.parse.parse_qs(parsed_url.query)
        global code
        code = next(iter(parsed_query['code']), '')

        response_body = b'Success. Look back at your terminal.\r\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', len(response_body))
        self.end_headers()
        self.wfile.write(response_body)

        global httpd
        t = threading.Thread(target=lambda: httpd.shutdown())
        t.start()


code = ''

server_address = ('', 8745)
httpd = http.server.HTTPServer(server_address, Handler)

# If we are running over ssh then the browser on the local machine
# would never be able access localhost:8745
if not os.getenv('SSH_CONNECTION'):
    httpd.serve_forever()

if code == '':
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
