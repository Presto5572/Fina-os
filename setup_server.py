# This file is fully built as a TEST for the database layer of S.H.E.I.L.A. 

# setup_server.py
from flask import Flask, render_template_string, request, jsonify
from core.plaid_client import SheilaConnector
from core.database import SheilaVault

app = Flask(__name__)
sheila = SheilaConnector()
vault = SheilaVault()

# This is the tiny HTML/JS page that opens the Plaid Login window
# We embed it here so you don't need a separate .html file
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>S.H.E.I.L.A. Setup</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
        button { padding: 15px 30px; font-size: 18px; background: #000; color: #fff; border: none; cursor: pointer; border-radius: 5px; }
    </style>
</head>
<body>
    <button id="link-button">Connect Bank to S.H.E.I.L.A.</button>
    <script>
    document.getElementById('link-button').onclick = async function() {
        // 1. Ask Python for a Link Token
        const response = await fetch('/api/create_link_token', { method: 'POST' });
        const data = await response.json();
        const linkToken = data.link_token;

        // 2. Open the Plaid Login Window
        const handler = Plaid.create({
            token: linkToken,
            onSuccess: async function(public_token, metadata) {
                // 3. Send the public_token back to Python to exchange for permanent access
                await fetch('/api/exchange_public_token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ public_token: public_token, metadata: metadata })
                });
                alert('Success! Account linked. You can close this window.');
            },
        });
        handler.open();
    };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/create_link_token', methods=['POST'])
def create_link_token():
    token = sheila.create_link_token()
    return jsonify({'link_token': token})

@app.route('/api/exchange_public_token', methods=['POST'])
def exchange_public_token():
    data = request.get_json()
    public_token = data['public_token']
    metadata = data['metadata']
    
    # 1. Exchange for permanent access token
    access_token = sheila.exchange_public_token(public_token)
    
    # 2. Save to Encrypted Database
    account_id = metadata['account_id']
    institution_name = metadata['institution']['name']
    
    # Note: Plaid Link returns one "main" account ID, but the access_token 
    # usually gives access to all accounts at that bank.
    vault.add_account(
        account_id=account_id,
        name=institution_name,
        type="depository", # Defaulting for sandbox
        subtype="checking",
        access_token=access_token
    )
    
    print(f"SUCCESSFULLY LINKED: {institution_name}")
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    print("S.H.E.I.L.A. Setup Server running at http://localhost:5000")
    app.run(port=5000)