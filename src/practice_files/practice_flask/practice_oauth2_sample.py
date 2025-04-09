from flask_oauthlib.provider import OAuth2Provider
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
oauth = OAuth2Provider(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/ahram/test.db"
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    client_id = db.Column(db.String, unique=True)


class Client(db.Model):
    # human readable name, not required
    name = db.Column(db.String(40))

    # human readable description, not required
    description = db.Column(db.String(400))

    # creator of the client, not required
    user_id = db.Column(db.ForeignKey("user.id"))
    # required if you need to support client credential
    user = db.relationship("User")

    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(
        db.String(55), unique=True, index=True, nullable=False
    )

    # public or confidential
    is_confidential = db.Column(db.Boolean)

    _redirect_uris = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    @property
    def client_type(self):
        if self.is_confidential:
            return "confidential"
        return "public"

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")
    )
    user = db.relationship("User")

    client_id = db.Column(
        db.String(40),
        db.ForeignKey("client.client_id"),
        nullable=False,
    )
    client = db.relationship("Client")

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40),
        db.ForeignKey("client.client_id"),
        nullable=False,
    )
    client = db.relationship("Client")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


@oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()


from datetime import datetime, timedelta


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()


def get_current_user(client_id):
    return User.query.filter_by(User.client_id == client_id).first()


@oauth.grantsetter
def save_grant(client_id, code, request_, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code["code"],
        redirect_uri=request_.redirect_uri,
        _scopes=" ".join(request_.scopes),
        user=get_current_user(client_id),
        expires=expires,
    )
    db.session.add(grant)
    db.session.commit()
    return grant


@oauth.tokengetter
def load_token(access_token_=None, refresh_token_=None):
    if access_token_:
        return Token.query.filter_by(access_token=access_token_).first()
    elif refresh_token_:
        return Token.query.filter_by(refresh_token=refresh_token_).first()


from datetime import datetime, timedelta


@oauth.tokensetter
def save_token(token, request_, *args, **kwargs):
    toks = Token.query.filter_by(
        client_id=request_.client.client_id, user_id=request_.user.id
    )
    # make sure that every client has only one token connected to a user
    for t in toks:
        db.session.delete(t)

    expires_in = token.get("expires_in")
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        token_type=token["token_type"],
        _scopes=token["scope"],
        expires=expires,
        client_id=request_.client.client_id,
        user_id=request_.user.id,
    )
    db.session.add(tok)
    db.session.commit()
    return tok


@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user = User.query.filter_by(username=username).first()
    # if user.check_password(password):
    return user
    # return None


@oauth.invalid_response
def require_oauth_invalid(req):
    return jsonify(message=req.error_message), 401


@app.route("/oauth/authorize", methods=["GET", "POST"])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == "GET":
        client_id = kwargs.get("client_id")
        client = Client.query.filter_by(client_id=client_id).first()
        kwargs["client"] = client
        return render_template("confirm.html", **kwargs)

    confirm = request.form.get("confirm", "no")
    return confirm == "yes"


@app.route("/oauth/token")
@oauth.token_handler
def access_token():
    return {"version": "0.1.0"}


@app.route("/oauth/revoke", methods=["POST"])
@oauth.revoke_handler
def revoke_token():
    pass


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/api/email")
@oauth.require_oauth("email")
def email_api():
    oauth_ = request.oauth
    return jsonify(email="me@oauth.net", username=oauth_.user.username)


@app.route("/api/client")
@oauth.require_oauth()
def client_api():
    oauth_ = request.oauth
    return jsonify(client=oauth_.client.name)


@app.route("/")
def index():
    return "<h1>Hello world!!</h1>"


if __name__ == "__main__":
    db.create_all()
    app.run(port=5000, debug=True)
