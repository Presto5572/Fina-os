import os
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from dotenv import load_dotenv
from datetime import date, timedelta

# Load keys from .env
load_dotenv()

class SheilaConnector:
    """
    The 'Nerves' of the operation. 
    Handles all direct communication with the Plaid Financial API.
    """

    def __init__(self):
        # 1. Configure the Client
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox, # Change to Development for real data once ready to leave "Sandbox"
            api_key={
                'clientId': os.getenv('PLAID_CLIENT_ID'),
                'secret': os.getenv('PLAID_SECRET'),
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    # These are the setup methods

    def create_link_token(self):
        """
        Generates a temporary token needed to open the Plaid 'Link' UI 
        so you can log in to your bank securely.
        """
        request = LinkTokenCreateRequest(
            products=[Products('transactions'), Products('investments')],
            client_name="Fina.os - S.H.E.I.L.A.",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id='sheila_admin_01'
            )
        )
        response = self.client.link_token_create(request)
        return response['link_token']

    def exchange_public_token(self, public_token):
        """
        Exchanges the temporary 'public_token' (received after you log in)
        for a permanent 'access_token' (which we save in the database).
        """
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = self.client.item_public_token_exchange(request)
        return response['access_token']

    # --- DATA FETCHING METHODS (The Daily Routine) ---

    def get_transactions(self, access_token, days_back=30):
        """
        Fetches transaction history for the Sentinel Spoke.
        """
        start_date = date.today() - timedelta(days=days_back)
        end_date = date.today()
        
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(
                include_personal_finance_category=True # Getting that AI categorization
            )
        )
        response = self.client.transactions_get(request)
        return response['transactions']

    def get_holdings(self, access_token):
        """
        Fetches investment holdings for the Tax-Loss Scout.
        """
        request = InvestmentsHoldingsGetRequest(
            access_token=access_token
        )
        response = self.client.investments_holdings_get(request)
        return response['holdings'], response['securities']

# Quick Test (Only works if you have valid keys in .env)
if __name__ == "__main__":
    try:
        sheila = SheilaConnector()
        print("S.H.E.I.L.A. Connection established with Plaid Servers.")
        token = sheila.create_link_token()
        print(f"Link Token generated: {token[:10]}...")
    except Exception as e:
        print(f"Connection Failed: {e}")