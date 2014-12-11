from flask import Flask, render_template, url_for, request, redirect, session, flash, send_from_directory

from flickr_api.auth import AuthHandler
from flickr_api import FlickrError
import flickr_api

import requests
import requests.auth
import urllib
import jwt

# Config values
AAD_CLIENT_ID = "c3c7e96f-f145-4445-bd72-c655bdf17c31"
AAD_CLIENT_SECRET = "PdstmBJuxCeSnFA4PJIFWgawtpTj6d2YAfWG+0VSaDU="
#AAD_REDIRECT_URI = "http://localhost/aad_auth_callback"
AAD_REDIRECT_URI = "http://104.236.173.186/aad_auth_callback"

# SPO MyFiles              : Varies with tenant, need to call discovery API
# AAD graph                : https://graph.windows.net/
# EXO Contact Calendar Mail: https://outlook.office365.com/
AAD_RESOURCE = "https://api.office.com/discovery/"

AAD_AUTH_ENDPOINT_URI = "https://login.windows.net/common/oauth2/authorize"
AAD_TOKEN_ENDPOINT_URI = "https://login.windows.net/common/oauth2/token"
O365_DISCOVERY_ENDPOINT_URI = "https://api.office.com/discovery/me/services"
AAD_GRAPH_ENDPOINT_URI = "https://graph.windows.net"

# Flickr config
FLICKR_KEY = '298c1f664f996ecbc003d0480cd25554'
FLICKR_SECRET = 'fa377e5c4a158410'

secrets = {'api_key': FLICKR_KEY, 'api_secret': FLICKR_SECRET }

# Routes
app = Flask(__name__)

@app.route("/")
def index():
    if request.method == 'OPTIONS':
        print 'OPTIONS'
        return ''
    else:
        return render_template('home.html', username='Olaf')
        #return app.send_static_file('./App/Home/Home.html')


@app.route('/<path:filename>')
def send_file(filename):
    return send_from_directory(app.static_folder, filename)


#####
# AAD login
# http://msdn.microsoft.com/en-us/office/office365/api/discovery-service-rest-operations
# http://msdn.microsoft.com/en-us/library/azure/dn645542.aspx
@app.route("/aad_login")
def login():
    link = "https://api.office.com/discovery/v1.0/me/FirstSignIn?redirect_uri=%s&scope=MyFiles.Read"
    return redirect(link % AAD_REDIRECT_URI, code=302)


@app.route("/aad_auth_callback")
def aad_auth_callbak():
    error = request.args.get('error', '')
    if error:
        return "Error from AAD authorization endpoint: " + error

    # From FirstSignIn
    user_email = request.args.get('user_email')
    if (user_email):
        return redirect(get_aad_auth_url(user_email), code=302)

    # From AAD authorization endpoint
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
    session["o365_access_token"] = access_token
    session["o365_refresh_token"] = refresh_token

    id_token_decoded = jwt.decode(id_token, verify=False) 
    unique_name = id_token_decoded["unique_name"]

    o365_myFiles_serviceInfo = get_o365_service_info(access_token, "MyFiles")
    o365_myFiles_service_endpoint = o365_myFiles_serviceInfo["ServiceEndpointUri"] # e.g) https://yongjkim-my.sharepoint.com/personal/yongjkim_yongjkim_onmicrosoft_com/_api
    o365_myFiles_service_resource_id = o365_myFiles_serviceInfo["ServiceResourceId"] # e.g) https://yongjkim-my.sharepoint.com/
    session["o365_myFiles_service_endpoint"] = o365_myFiles_service_endpoint
    session["o365_myFiles_service_resource_id"] = o365_myFiles_service_resource_id

    flash("O365 logged in successfully", "success")
    return '<a href="javascript:window.close()">O365 logged in successfully, close this window</a>'


def get_aad_auth_url(login_hint):
    auth_params={"client_id": AAD_CLIENT_ID,
                 "response_type": "code",
                 "resource": AAD_RESOURCE,
                 "login_hint": login_hint,
                 "redirect_uri": AAD_REDIRECT_URI} # TODO: state
    auth_url = AAD_AUTH_ENDPOINT_URI + "?" + urllib.urlencode(auth_params)
    return auth_url


def get_o365_service_info(access_token, capability):
    url = O365_DISCOVERY_ENDPOINT_URI
    auth_headers = {"Authorization": "Bearer " + access_token,
                    "Accept": "application/json;odata=verbose"}
    response = requests.get(url,
                            headers=auth_headers)
    response_json = response.json()
    results = response_json["d"]["results"]
    for serviceInfo in results:
        if serviceInfo["Capability"] == capability:
            return serviceInfo


def is_o365_logged_in():
    serviceEndpointUri = session.get("o365_myFiles_service_endpoint")
    serviceResourceId = session.get("o365_myFiles_service_resource_id")
    refresh_token = session.get("o365_refresh_token")
    if (serviceEndpointUri is None) or (serviceResourceId is None) or (refresh_token is None):
        return False
    else:
        return True


class Photo:
    def __init__(self, photo_url):
        self.photo_url = photo_url

    def getPhotoFile(self):
        return self.photo_url

def get_o365_myFiles(term):
    if is_o365_logged_in() == False:
        return None

    serviceEndpointUri = session.get("o365_myFiles_service_endpoint")
    serviceResourceId = session.get("o365_myFiles_service_resource_id")
    refresh_token = session.get("o365_refresh_token")
    access_token = get_o365_access_token_myFiles(serviceResourceId, refresh_token)
    url = serviceEndpointUri + "/Files('Shared%20with%20Everyone')/Children"
    auth_headers = {"Authorization": "Bearer " + access_token,
                    "Accept": "application/json"}
    response = requests.get(url,
                            headers=auth_headers)
    response_json = response.json()
    photos = []
    for document in response_json["value"]:
        url = document["Url"]
        if url.endswith(".jpg") or url.endswith(".png"):
            if term in url:
                photos.append(Photo(url))
    return photos


def get_o365_access_token_myFiles(serviceResourceId, refresh_token):
    body = {"resource": serviceResourceId,
            "client_id": AAD_CLIENT_ID,
            "client_secret": AAD_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token}
    response = requests.get(AAD_TOKEN_ENDPOINT_URI,
                           data=body)
    response_json = response.json()
    return response_json["access_token"]


def get_aad_user_info(access_token):
    pass # TODO: It requires access_token with scope for AAD graph resource id
    url = AAD_GRAPH_ENDPOINT_URI + "/me?api-version=2013-11-08"
    headers = {"Authorization": "Bearer " + access_token,
               "Content-Type": "application/json"}
    response = requests.get(url,
                            headers=headers)
    return response.json()

# AAD login
#####


#-----------------------------------------------------------------------------
# flickr login
#-----------------------------------------------------------------------------

@app.route('/flickr_login')
def flickr_login():
    """Login to flickr with read only access.After successful login redirects to
    callback url else redirected to index page
    """
    try:
        auth = AuthHandler(key=FLICKR_KEY, secret=FLICKR_SECRET,
                            callback=url_for('flickr_callback', _external=True))
        return redirect(auth.get_authorization_url('read'))

    except FlickrError, f:
        # Flash failed login & redirect to index page
        flash(u'Failed to authenticate user with flickr', 'error')
        return redirect(url_for('index'))

@app.route('/flickr_login/callback')
def flickr_callback():
    """Callback handler from flickr.
    Set the oauth token, oauth_verifier to session variable for later use.
    Redirect to /photos
    """
    session['oauth_token'] = request.args.get('oauth_token')
    session['oauth_verifier'] = request.args.get('oauth_verifier')

    flash("logged in successfully", "success")
    return redirect(url_for('index'))


#-----------------------------------------------------------------------------
# flickr search rendering
#-----------------------------------------------------------------------------
@app.route('/search/<term>')
def search(term):
    flickr_api.set_keys(**secrets)
    photos = flickr_api.Photo.search(
                #tags=term,
                text=term,
                sort='interestingness-desc',
                per_page=20
    )
    print photos
    #raise

    # OneDrive photos
    odb_photos = None
    if is_o365_logged_in():
        odb_photos = get_o365_myFiles(term)

    return render_template('photos.html', photos=photos, odb_photos=odb_photos, maximum=20, term=term)


#-----------------------------------------------------------------------------
# main
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    import os

    app.debug = True
    app.secret_key = os.urandom(24)

    # Set root view that handles OPTIONS call
    index.provide_automatic_options = False
    index.methods = ['GET', 'OPTIONS']
    app.add_url_rule('/', index)

    app.run(host='0.0.0.0', port=80)
