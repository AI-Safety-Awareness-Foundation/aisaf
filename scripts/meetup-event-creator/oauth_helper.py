#!/usr/bin/env python3
"""
OAuth2 Helper for Meetup.com API

This script helps obtain an OAuth2 token from Meetup.com using the authorization code flow.
You'll need to register your application at https://www.meetup.com/api/oauth/create/
to get a client ID and client secret.

Usage:
    python oauth_helper.py

The script will guide you through the OAuth2 authorization process and print the access token.
"""

import json
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs

import requests


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth2 callback."""
    
    def do_GET(self):
        """Handle GET request with authorization code."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Extract the authorization code from the query string
        if '?' in self.path:
            query = self.path.split('?', 1)[1]
            params = parse_qs(query)
            
            if 'code' in params:
                self.server.auth_code = params['code'][0]
                response = """
                <html>
                <body>
                <h1>Authorization Successful</h1>
                <p>You can now close this window and return to the application.</p>
                </body>
                </html>
                """
            elif 'error' in params:
                self.server.auth_error = params['error'][0]
                response = """
                <html>
                <body>
                <h1>Authorization Failed</h1>
                <p>Error: {}</p>
                <p>Please close this window and try again.</p>
                </body>
                </html>
                """.format(params['error'][0])
            else:
                response = """
                <html>
                <body>
                <h1>Invalid Response</h1>
                <p>No authorization code or error was received.</p>
                </body>
                </html>
                """
        else:
            response = """
            <html>
            <body>
            <h1>Invalid Response</h1>
            <p>No query parameters were received.</p>
            </body>
            </html>
            """
        
        self.wfile.write(response.encode())


def get_meetup_oauth_token(client_id, client_secret, redirect_uri="https://aisafetyawarenessproject.org"):
    """
    Get an OAuth2 token from Meetup.com using the authorization code flow.
    
    Args:
        client_id: The OAuth2 client ID for your Meetup.com application
        client_secret: The OAuth2 client secret for your Meetup.com application
        redirect_uri: The redirect URI for your application (default: http://localhost:8080)
        
    Returns:
        dict: The OAuth2 token response containing the access token, refresh token, etc.
    """
    # Step 1: Authorize the application
    auth_params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'basic group_edit event_management'
    }
    auth_url = "https://secure.meetup.com/oauth2/authorize?" + urlencode(auth_params)
    
    print("Opening browser for authorization...")
    print(f"Authorization URL: {auth_url}")
    webbrowser.open(auth_url)
    
    # Step 2: Start a local server to receive the callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None
    server.auth_error = None
    
    print("Waiting for authorization...")
    while server.auth_code is None and server.auth_error is None:
        server.handle_request()
    
    if server.auth_error:
        raise Exception(f"Authorization failed: {server.auth_error}")
    
    auth_code = server.auth_code
    print("Authorization code received!")
    
    # Step 3: Exchange the authorization code for an access token
    token_params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': auth_code
    }
    token_url = "https://secure.meetup.com/oauth2/access"
    
    print("Exchanging authorization code for access token...")
    response = requests.post(token_url, data=token_params)
    
    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.text}")
    
    token_data = response.json()
    return token_data


def main():
    """Main function to get an OAuth2 token from Meetup.com."""
    print("Meetup.com OAuth2 Helper")
    print("========================")
    print("This script will help you obtain an OAuth2 token from Meetup.com.")
    print("You'll need to register your application at https://www.meetup.com/api/oauth/create/")
    print()
    
    client_id = input("Enter your OAuth2 client ID: ")
    client_secret = input("Enter your OAuth2 client secret: ")
    
    try:
        token_data = get_meetup_oauth_token(client_id, client_secret)
        
        print("\nOAuth2 token received successfully!")
        print(f"Access Token: {token_data['access_token']}")
        print(f"Refresh Token: {token_data.get('refresh_token', 'None')}")
        print(f"Expires In: {token_data.get('expires_in', 'Unknown')} seconds")
        
        # Save the token for future use
        save_token = input("Would you like to save the token data to a file? (y/n): ")
        if save_token.lower() == 'y':
            filename = input("Enter the filename (default: meetup_token.json): ") or "meetup_token.json"
            with open(filename, 'w') as f:
                json.dump(token_data, f, indent=2)
            print(f"Token data saved to {filename}")
        
        # Set environment variable
        print("\nTo use this token with the meetup_event_creator.py script, you can:")
        print(f"1. Set the MEETUP_ACCESS_TOKEN environment variable:")
        print(f"   export MEETUP_ACCESS_TOKEN=\"{token_data['access_token']}\"")
        print(f"2. Or enter the token when prompted by the script.")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
