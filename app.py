from flask import Flask, render_template, request, redirect
import hashlib
import random
import string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# -------------------------------
# Database configuration
# -------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voters.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

candidates = ["Luka Pavikjevikj", "Ian Park", "Abstain"]

# -------------------------------
# Helper: hash generator
# -------------------------------
def generate_hashable_id(firstname, lastname, email, huid, seed=None):
    """
    Returns a short alphanumeric hash string based on user data + random seed.
    """
    if seed is None:
        seed = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    base_string = f"{firstname}{lastname}{email}{huid}{seed}"
    hash_obj = hashlib.sha256(base_string.encode())
    return hash_obj.hexdigest()[:16]  # shorten to 16 chars for readability

class Tally(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, candidate_name):
        self.candidate_name = candidate_name
        self.votes = 0

# -------------------------------
# Database model
# -------------------------------
class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    huid = db.Column(db.String(50), unique=True, nullable=False)
    hashable_id = db.Column(db.String(64), unique=True, nullable=False)
    has_voted = db.Column(db.Boolean, default=False, nullable=False)
    
    def __init__(self, firstname, lastname, email, huid):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.huid = huid
        self.has_voted = False
        self.hashable_id = generate_hashable_id(firstname, lastname, email, huid)

    def __repr__(self):
        return f"<Voter {self.firstname} {self.lastname}>"

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html", title="Home")

@app.route("/voters")
def voters():
    voters = Voter.query.all()
    return render_template("voters.html", title="Voters", voters=voters)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        huid = request.form.get("huid")

        voter = Voter(firstname, lastname, email, huid)
        db.session.add(voter)
        db.session.commit()

        voters = Voter.query.all()
        return render_template("register.html", title="Registered", voter=voter, voters=voters)
    
    voters = Voter.query.all()
    return render_template("register.html", title="Register", voters=voters)

@app.route("/voter_login", methods=["GET", "POST"])
def voter_login():
    if request.method == "POST":
        hashable_id = request.form.get("hashable_id")
        

        return redirect(f"/vote/{hashable_id}")
        
    return render_template("vote.html", title="Vote", mode="login")

@app.route("/vote/<hashable_id>", methods=["POST", "GET"])
def vote(hashable_id):
    voter = Voter.query.filter_by(hashable_id=hashable_id).first()
    if not voter or voter.has_voted:
        return render_template("vote.html", title="Vote", error="Invalid voter or already voted.")

    if request.method == "POST":
        candidate = request.form.get("candidate")
        tally = Tally.query.filter_by(candidate_name=candidate).first()
        if not tally:
            tally = Tally(candidate)
            db.session.add(tally)

        tally.votes += 1
        voter.has_voted = True
        db.session.commit()

        return render_template("vote.html", title="Vote", success="Vote recorded successfully!")
    
    return render_template("vote.html", title="Vote", voter=voter, candidates=candidates)


@app.route("/results")
def results():
    return redirect("/")
    tally_data = Tally.query.all()
    results = {tally.candidate_name: tally.votes for tally in tally_data}
    winner = max(results, key=results.get) if results else None
    return render_template("results.html", title="Results", results=results, winner=winner)

# -------------------------------
# Run the app
# -------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(debug=True)
