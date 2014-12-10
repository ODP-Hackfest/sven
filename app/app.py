from flask import Flask, request
import requests
import requests.auth
import urllib

# Config values
AAD_CLIENT_ID = "c3c7e96f-f145-4445-bd72-c655bdf17c31"
AAD_CLIENT_SECRET = "PdstmBJuxCeSnFA4PJIFWgawtpTj6d2YAfWG+0VSaDU="
AAD_REDIRECT_URI = "http://localhost/aad_auth_callback"
AAD_AUTH_ENDPOINT_URI = "https://login.windows.net/common/oauth2/authorize"
AAD_TOKEN_ENDPOINT_URI = "https://login.windows.net/common/oauth2/token"

# Routes
app = Flask(__name__)

@app.route("/")
def root():
    return app.send_static_file('./App/Home/Home.html')

@app.route("/login")
def login():
    link = '<a href="%s" target="_blank">Authenticate with OrgId</a>'
    return link % get_aad_auth_url()

def get_aad_auth_url():
    auth_params={"client_id": AAD_CLIENT_ID,
                 "response_type": "code",
                 "redirect_uri": AAD_REDIRECT_URI}
    auth_url = AAD_AUTH_ENDPOINT_URI + "?" + urllib.urlencode(auth_params)
    return auth_url 

# TODO: AAD oauth2 callback

if __name__ == "__main__":
    app.debug = True
    app.run()

