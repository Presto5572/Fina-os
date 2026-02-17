import os
import datetime
from flask import Flask, request, jsonify, render_template_string
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv
from core.database import SheilaVault

load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')

if PLAID_ENV == 'sandbox':
    host = plaid.Environment.Sandbox
elif PLAID_ENV == 'development':
    host = plaid.Environment.Development
elif PLAID_ENV == 'production':
    host = plaid.Environment.Production
else:
    host = plaid.Environment.Sandbox

configuration = plaid.Configuration(
    host=host,
    api_key={'clientId': PLAID_CLIENT_ID, 'secret': PLAID_SECRET}
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# --- FRONTEND TEMPLATE ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>S.H.E.I.L.A. Setup</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        body { font-family: monospace; background: #111; color: #0f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { text-align: center; border: 1px solid #0f0; padding: 40px; box-shadow: 0 0 20px #0f0; }
        h1 { margin-bottom: 10px; }
        button { background: #0f0; color: #000; border: none; padding: 15px 30px; font-family: monospace; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #fff; }
        #status { margin-top: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>S.H.E.I.L.A. SETUP SERVER</h1>
        <p>Initialize Secure Financial Link</p>
        <button id="link-button">CONNECT BANK ACCOUNT</button>
        <div id="status">Waiting for input...</div>
    </div>
    <script>
    const statusDiv = document.getElementById('status');
    document.getElementById('link-button').addEventListener('click', async () => {
        statusDiv.innerText = "Generating Link Token...";
        const response = await fetch('/api/create_link_token', { method: 'POST' });
        const data = await response.json();
        if (data.error) { statusDiv.innerText = "Error: " + data.error; return; }
        
        const handler = Plaid.create({
            token: data.link_token,
            onSuccess: async (public_token, metadata) => {
                statusDiv.innerText = "Syncing Data (This may take a moment)...";
                const res = await fetch('/api/exchange_public_token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ public_token: public_token, metadata: metadata })
                });
                const result = await res.json();
                statusDiv.innerText = "SUCCESS! " + result.summary;
            },
            onExit: (err) => { statusDiv.innerText = err ? "Error: " + err.message : "User exited."; }
        });
        handler.open();
    });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/create_link_token', methods=['POST'])
def create_link_token():
    try:
        request_api = LinkTokenCreateRequest(
            products=[Products('transactions'), Products('investments')],
            client_name="Fina OS",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique_user_id')
        )
        response = client.link_token_create(request_api)
        return jsonify(response.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/exchange_public_token', methods=['POST'])
def exchange_public_token():
    try:
        public_token = request.json['public_token']
        
        # 1. Exchange Token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        
        vault = SheilaVault()
        stats = {'accounts': 0, 'holdings': 0, 'transactions': 0}

        # 2. Fetch & Save Accounts
        accounts_request = AccountsGetRequest(access_token=access_token)
        accounts_response = client.accounts_get(accounts_request)
        
        for acc in accounts_response['accounts']:
            vault.add_account(
                account_id=acc['account_id'],
                name=acc['name'],
                type=str(acc['type']),
                subtype=str(acc['subtype']),
                mask=acc['mask'] if acc['mask'] else "0000",
                access_token=access_token
            )
            stats['accounts'] += 1

        # 3. Fetch & Save Investments (Holdings)
        try:
            holdings_request = InvestmentsHoldingsGetRequest(access_token=access_token)
            holdings_response = client.investments_holdings_get(holdings_request)
            
            # Map Securities (ID -> Ticker)
            securities_map = {s.security_id: s for s in holdings_response['securities']}
            
            for h in holdings_response['holdings']:
                security = securities_map.get(h.security_id)
                ticker = security.ticker_symbol if security else "UNKNOWN"
                
                # Only save if we have a valid ticker
                if ticker:
                    vault.add_holding(
                        ticker=ticker,
                        quantity=h.quantity,
                        cost_basis=h.cost_basis if h.cost_basis else 0.0,
                        price=h.institution_price if h.institution_price else 0.0,
                        account_id=h.account_id
                    )
                    stats['holdings'] += 1
        except Exception as e:
            print(f"Warning: Could not fetch holdings: {e}")

        # 4. Fetch & Save Transactions (Sync)
        try:
            # Simple sync for initial fetch
            sync_request = TransactionsSyncRequest(access_token=access_token)
            sync_response = client.transactions_sync(sync_request)
            
            for t in sync_response['added']:
                vault.add_transaction(
                    tx_id=t.transaction_id,
                    date=str(t.date),
                    merchant=t.merchant_name if t.merchant_name else t.name,
                    amount=t.amount,
                    category=t.personal_finance_category.primary if t.personal_finance_category else "Uncategorized",
                    account_id=t.account_id
                )
                stats['transactions'] += 1
        except Exception as e:
             print(f"Warning: Could not fetch transactions: {e}")

        vault.close()
        summary = f"Linked {stats['accounts']} accts, {stats['holdings']} holdings, {stats['transactions']} txns."
        print(f"SUCCESS: {summary}")
        return jsonify({'status': 'success', 'summary': summary})
        
    except Exception as e:
        print(f"SERVER ERROR: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("S.H.E.I.L.A. Setup Server running at http://localhost:5000")
    app.run(port=5000)