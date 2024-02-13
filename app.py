from flask import Flask, redirect, url_for, session
import msal
import uuid

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'un_secret_tres_secret'  # Devrait être un secret aléatoire
app.config['SESSION_TYPE'] = 'filesystem'

# Configurez ces valeurs avec celles de votre application Azure B2C
app.config['B2C_TENANT'] = "ab39bc97-fa3e-44e9-a2c6-e0f1aa8183f7"
app.config['B2C_CLIENT_ID'] = "3c0393e1-d9ea-4d48-84b7-a1f4c3f5c98c"
app.config['B2C_CLIENT_SECRET'] = "x9E8Q~3c7z12nfit7JCs4w5VI7D7uZmVB_Db_a17"
app.config['B2C_REDIRECT_URI'] = "https://application-test-bluink.azurewebsites.net"  # Changez pour votre URL de production
app.config['B2C_AUTHORITY'] = "https://DevopsCoffee.b2clogin.com/DevopsCoffee.onmicrosoft.com/B2C_1_signupsignin1"

# Créez une instance MSAL
msal_app = msal.ConfidentialClientApplication(
    app.config['B2C_CLIENT_ID'],
    authority=app.config['B2C_AUTHORITY'],
    client_credential=app.config['B2C_CLIENT_SECRET'],
)

@app.route('/')
def index():
    return 'Bienvenue dans l\'application Flask Azure B2C! <a href="/login">Se connecter</a>'

@app.route('/login')
def login():
    # Génère l'URL de connexion et redirige vers la page de connexion d'Azure B2C
    session['state'] = str(uuid.uuid4())
    fixed_code_challenge = 'YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl'
    auth_url = msal_app.get_authorization_request_url(
        scopes=[],
        state=session['state'],
        redirect_uri=url_for('authorized', _external=True, _scheme='https'))
    # Ensuite, ajoutez manuellement le code_challenge à l'URL
    auth_url += '&code_challenge={}'.format(fixed_code_challenge)
    return redirect(auth_url)

@app.route('/getAToken')
def authorized():
    # La requête de retour de l'authentification Azure B2C
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("index"))  # Aucune correspondance d'état; possible attaque CSRF
    if 'error' in request.args:  # Si l'utilisateur a refusé la permission
        return redirect(url_for("index"))

    # Récupérer le token avec le code de la requête
    cache = msal.SerializableTokenCache()
    result = msal_app.acquire_token_by_authorization_code(
        request.args['code'],
        scopes=["openid", "profile"],  # Les scopes pour lesquels le token est requis
        redirect_uri=url_for('authorized', _external=True, _scheme='https'),
        cache=cache
    )

    if "id_token" in result:
        # Succès, vous pouvez utiliser result['id_token'] pour obtenir les informations de l'utilisateur
        session['user'] = result.get('id_token_claims')
        return redirect(url_for("index"))
    else:
        return f"Erreur d'authentification: {result.get('error_description')}"

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Utilisez ssl_context pour le https en local
