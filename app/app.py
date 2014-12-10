from flask import Flask, request
import requests
import requests.auth
import urllib
import jwt

# Config values
AAD_CLIENT_ID = "c3c7e96f-f145-4445-bd72-c655bdf17c31"
AAD_CLIENT_SECRET = "PdstmBJuxCeSnFA4PJIFWgawtpTj6d2YAfWG+0VSaDU="
# SPO files: Microsoft.SharePoint
# AAD graph: https://graph.windows.net
# EXO ?
AAD_RESOURCE = "Microsoft.SharePoint"
AAD_REDIRECT_URI = "http://localhost/aad_auth_callback"
AAD_AUTH_ENDPOINT_URI = "https://login.windows.net/common/oauth2/authorize"
AAD_TOKEN_ENDPOINT_URI = "https://login.windows.net/common/oauth2/token"
AAD_GRAPH_ENDPOINT_URI = "https://graph.windows.net"

# Routes
app = Flask(__name__)

@app.route("/")
def root():
    return app.send_static_file('./App/Home/Home.html')

#####
# AAD login
@app.route("/aad_login")
def login():
    link = '<a href="%s" target="_blank">Authenticate with OrgId</a>'
    return link % get_aad_auth_url() # TODO: render_page


@app.route("/aad_auth_callback")
def aad_auth_callbak():
    error = request.args.get('error', '')
    if error:
        return "Error from AAD authorization endpoint: " + error
    # TODO: validate state    
    code = request.args.get('code')
    body = {"grant_type": "authorization_code",
            "code": code,
            "client_id": AAD_CLIENT_ID,
            "client_secret": AAD_CLIENT_SECRET,
            "resource": AAD_RESOURCE,
            "redirect_uri": AAD_REDIRECT_URI}
    headers = {"User-Agent": "ODP-HackFest-Docker-Python",
               "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(AAD_TOKEN_ENDPOINT_URI,
                             headers=headers,
                             data=body)
    json = response.json()
    access_token = json["access_token"]
    refresh_token = json["refresh_token"]
    id_token = json["id_token"]
    id_token_decoded = jwt.decode(id_token, verify=False)
    unique_name = id_token_decoded["unique_name"]
    return "me: " + unique_name + ", access token: " + access_token + ", refresh token: " + refresh_token + ", id token: " + id_token


def get_aad_auth_url():
    auth_params={"client_id": AAD_CLIENT_ID,
                 "response_type": "code",
                 "resource": AAD_RESOURCE,
                 "redirect_uri": AAD_REDIRECT_URI} # TODO: state
    auth_url = AAD_AUTH_ENDPOINT_URI + "?" + urllib.urlencode(auth_params)
    return auth_url 


def get_aad_user_info(access_token):
    pass # TODO: It requires access_token with scope for AAD graph resources
    url = AAD_GRAPH_ENDPOINT_URI + "/me?api-version=2013-11-08"
    headers = {"Authorization": "Bearer " + access_token,
               "Content-Type": "application/json"}
    response = requests.get(url,
                            headers=headers)
    return response.json()

# AAD login
#####

if __name__ == "__main__":
    app.debug = True
    app.run(port=80)

