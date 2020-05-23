from google_auth_oauthlib.flow import InstalledAppFlow
    
flow = InstalledAppFlow.from_client_secrets_file('clientsecret.json', scopes="https://www.googleapis.com/auth/youtube.force-ssl")
creds=flow.run_console()