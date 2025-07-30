from .imports_and_instrument_token import *


def upstox_login(creds):
    client_id = creds["auth"]["client_id"]
    client_pass = creds["auth"]["client_pass"]
    client_pin = creds["auth"]["client_pin"]
    api_key = creds["auth"]["api_key"]
    api_secret = creds["auth"]["api_secret"]
    redirect_uri = creds["auth"]["redirect_uri"]
    ucc = creds["auth"].get("ucc", "")  # Add UCC from creds

    # Initialize api headers to avoid KeyError
    creds.setdefault("api", {}).setdefault("headers", {})

    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}"

    print(f"Visit this url: {login_url}. Then, paste the code from the redirected browser.")

    try:
        auth_code = input("Paste the code from the redirected browser here: ").strip()
        if not auth_code:
            raise ValueError("Authorization code cannot be empty")
    except Exception as e:
        logging.error(f"Error reading auth code input: {e}")
        creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
        creds["api"]["last_function"] = "login_failed"
        return creds
    
    url = "https://api.upstox.com/v2/login/authorization/token"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'code': auth_code,
        'client_id': api_key,
        'client_secret': api_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token = response.json().get('access_token')
        if not token:
            raise ValueError("Access token not found in response")
        
        creds["auth"]["access_token"] = token
        creds["api"]["headers"] = {
            'Accept': 'application/json',
            'Api-Version': '2.0',
            'Authorization': f'Bearer {token}'
        }
        print(f"Logged in: {client_id}")
        
    except requests.HTTPError as e:
        logging.error(f"Token request failed: Status {e.response.status_code}, {e.response.text}")
        print(f"Unable to log in: {client_id}. Error: {e.response.status_code}, {e.response.text}")
        creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
        creds["api"]["last_function"] = "login_failed"
        return creds
    except Exception as e:
        logging.error(f"Unexpected error in login: {e}")
        print(f"Unable to log in: {client_id}. Error: {e}")
        creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
        creds["api"]["last_function"] = "login_failed"
        return creds

    creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"] = "login"
    return creds
    
def upstox_auth(creds):
    try:
        headers = creds.get("api", {}).get("headers", None)
        if not headers:
            logging.error("Missing 'headers' in creds['api'] — call upstox_login() first")
            print(f"Authentication failed: {creds['auth']['client_id']}. Headers missing.")
            return upstox_login(creds)
        
        if not creds["auth"].get("ucc"):
            logging.error("Missing 'ucc' in creds['auth']")
            raise ValueError("UCC is required for profile endpoint")
        
        url = f"https://api.upstox.com/v2/user/profile?ucc={creds['auth']['ucc']}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        json_data = response.json()
        if json_data.get("status") != "success":
            logging.error(f"Auth API returned error: {json_data}")
            raise ValueError("Auth API returned error status")
        
        print(f"Authentication Successful: {creds['auth']['client_id']}")
        
    except requests.HTTPError as e:
        logging.critical(f"Auth API failed: Status {e.response.status_code}, {e.response.text}")
        logging.critical(f"Curlify Request: {curlify.to_curl(e.response.request)}")
        if e.response.status_code == 401:
            print(f"Token expired for: {creds['auth']['client_id']}. Retrying login.")
            return upstox_login(creds)
        else:
            print(f"Authentication Failed: {creds['auth']['client_id']}. Error: {e}")
            return creds
    except ValueError as e:
        logging.critical(f"Auth API failed: {e}")
        print(f"Authentication Failed: {creds['auth']['client_id']}. Error: {e}")
        return creds
    except Exception as e:
        logging.critical(f"Unexpected error in auth: {e}")
        print(f"Authentication Failed: {creds['auth']['client_id']}. Error: {e}")
        return creds

    creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"] = "auth"
    return creds

def upstox_margin(creds):
    try:
        headers = creds.get("api", {}).get("headers", None)
        if not headers:
            logging.error("Missing 'headers' in creds['api'] — call upstox_login() first")
            print(f"Margin retrieval failed: {creds['auth']['client_id']}. Headers missing.")
            return upstox_login(creds)
        
        url = "https://api.upstox.com/v2/user/get-funds-and-margin"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        json_data = response.json()
        if json_data.get("status") != "success":
            logging.error(f"Margin API returned error: {json_data}")
            raise ValueError("Margin API returned error status")
        
        creds["api"]["margin"] = json_data["data"]
        print(f"Margin retrieved for: {creds['auth']['client_id']}")
        
    except requests.HTTPError as e:
        logging.critical(f"Margin API failed: Status {e.response.status_code}, {e.response.text}")
        logging.critical(f"Curlify Request: {curlify.to_curl(e.response.request)}")
        if e.response.status_code == 401:
            print(f"Token expired for: {creds['auth']['client_id']}. Retrying login.")
            return upstox_login(creds)
        else:
            # Fallback to profile check
            try:
                profile_url = f"https://api.upstox.com/v2/user/profile?ucc={creds['auth']['ucc']}"
                profile_response = requests.get(profile_url, headers=headers)
                profile_response.raise_for_status()
                print(f"Margin API down but profile accessible for: {creds['auth']['client_id']}")
                return creds
            except requests.HTTPError:
                print(f"Margin and profile APIs failed: {creds['auth']['client_id']}. Error: {e}")
                return upstox_login(creds)
    except ValueError as e:
        logging.critical(f"Margin API failed: {e}")
        print(f"Margin retrieval failed: {creds['auth']['client_id']}. Error: {e}")
        return creds
    except Exception as e:
        logging.critical(f"Unexpected error in margin: {e}")
        print(f"Margin retrieval failed: {creds['auth']['client_id']}. Error: {e}")
        return creds

    creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"] = "margin"
    return creds

def upstox_positions(creds):
    try:
        headers = creds.get("api", {}).get("headers", None)
        if not headers:
            logging.error("Missing 'headers' in creds['api'] — call upstox_login() first")
            print(f"Positions retrieval failed: {creds['auth']['client_id']}. Headers missing.")
            return upstox_login(creds)
        
        url = "https://api.upstox.com/v2/portfolio/short-term-positions"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        json_data = response.json()
        if json_data.get("status") != "success":
            logging.error(f"Positions API returned error: {json_data}")
            raise ValueError("Positions API returned error status")
        
        creds["api"]["positions"] = json_data["data"]
        print(f"Positions retrieved for: {creds['auth']['client_id']}")
        
    except requests.HTTPError as e:
        logging.critical(f"Positions API failed: Status {e.response.status_code}, {e.response.text}")
        logging.critical(f"Curlify Request: {curlify.to_curl(e.response.request)}")
        if e.response.status_code == 401:
            print(f"Token expired for: {creds['auth']['client_id']}. Retrying login.")
            return upstox_login(creds)
        else:
            # Fallback to profile check
            try:
                profile_url = f"https://api.upstox.com/v2/user/profile?ucc={creds['auth']['ucc']}"
                profile_response = requests.get(profile_url, headers=headers)
                profile_response.raise_for_status()
                print(f"Positions API down but profile accessible for: {creds['auth']['client_id']}")
                return creds
            except requests.HTTPError:
                print(f"Positions and profile APIs failed: {creds['auth']['client_id']}. Error: {e}")
                return upstox_login(creds)
    except ValueError as e:
        logging.critical(f"Positions API failed: {e}")
        print(f"Positions retrieval failed: {creds['auth']['client_id']}. Error: {e}")
        return creds
    except Exception as e:
        logging.critical(f"Unexpected error in positions: {e}")
        print(f"Positions retrieval failed: {creds['auth']['client_id']}. Error: {e}")
        return creds

    creds["api"]["last_updated"] = str(datetime.datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"] = "positions"  # Fixed typo: "postions" -> "positions"
    return creds