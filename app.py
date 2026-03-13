from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import date, datetime
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "wolf-energy-secret")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────────
# MODÈLES (miroirs des tables PostgreSQL)
# ─────────────────────────────────────────────

class Client(db.Model):
    __tablename__ = "clients"
    id_client     = db.Column(db.Integer, primary_key=True)
    type_client   = db.Column(db.String(20), nullable=False)
    nom           = db.Column(db.String(100), nullable=False)
    prenom        = db.Column(db.String(100))
    raison_sociale= db.Column(db.String(150))
    siret         = db.Column(db.String(14))
    adresse       = db.Column(db.String(300), nullable=False)
    telephone     = db.Column(db.String(20))
    email         = db.Column(db.String(150), nullable=False)
    date_creation = db.Column(db.Date, default=date.today)
    notes         = db.Column(db.Text)
    actif         = db.Column(db.Boolean, default=True)

class Bien(db.Model):
    __tablename__ = "biens"
    id_bien            = db.Column(db.Integer, primary_key=True)
    id_client          = db.Column(db.Integer, db.ForeignKey("clients.id_client"), nullable=False)
    reference_bien     = db.Column(db.String(50), nullable=False)
    type_bien          = db.Column(db.String(30), nullable=False)
    adresse            = db.Column(db.String(300), nullable=False)
    surface_m2         = db.Column(db.Numeric(10,2))
    annee_construction = db.Column(db.Integer)
    nb_niveaux         = db.Column(db.SmallInteger)
    type_chauffage     = db.Column(db.String(50))
    type_ventilation   = db.Column(db.String(50))
    type_isolation     = db.Column(db.String(100))
    dpe_classe         = db.Column(db.String(1))
    dpe_date           = db.Column(db.Date)
    notes              = db.Column(db.Text)
    date_ajout         = db.Column(db.Date, default=date.today)
    actif              = db.Column(db.Boolean, default=True)
    client             = db.relationship("Client", backref="biens")

class Audit(db.Model):
    __tablename__ = "audits"
    id_audit                = db.Column(db.Integer, primary_key=True)
    id_bien                 = db.Column(db.Integer, db.ForeignKey("biens.id_bien"), nullable=False)
    id_client               = db.Column(db.Integer, db.ForeignKey("clients.id_client"), nullable=False)
    reference_audit         = db.Column(db.String(50), nullable=False)
    statut                  = db.Column(db.String(30), default="En cours")
    type_audit              = db.Column(db.String(50), nullable=False)
    date_visite             = db.Column(db.Date)
    date_livraison          = db.Column(db.Date)
    auditeur                = db.Column(db.String(150))
    consommation_avant_kwh  = db.Column(db.Numeric(12,2))
    consommation_apres_kwh  = db.Column(db.Numeric(12,2))
    gain_energetique_pct    = db.Column(db.Numeric(5,2))
    classe_avant            = db.Column(db.String(1))
    classe_apres            = db.Column(db.String(1))
    recommandations         = db.Column(db.Text)
    observations            = db.Column(db.Text)
    montant_ht              = db.Column(db.Numeric(12,2))
    taux_tva                = db.Column(db.Numeric(4,2), default=20.00)
    notes_internes          = db.Column(db.Text)
    date_creation           = db.Column(db.DateTime, default=datetime.now)
    client                  = db.relationship("Client", backref="audits")
    bien                    = db.relationship("Bien", backref="audits")

class Document(db.Model):
    __tablename__ = "documents"
    id_document    = db.Column(db.Integer, primary_key=True)
    id_audit       = db.Column(db.Integer, db.ForeignKey("audits.id_audit"))
    id_client      = db.Column(db.Integer, db.ForeignKey("clients.id_client"))
    id_bien        = db.Column(db.Integer, db.ForeignKey("biens.id_bien"))
    type_document  = db.Column(db.String(50), nullable=False)
    nom_fichier    = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.Text, nullable=False)
    format_fichier = db.Column(db.String(10))
    description    = db.Column(db.Text)
    date_ajout     = db.Column(db.DateTime, default=datetime.now)
    ajoute_par     = db.Column(db.String(100))
    version        = db.Column(db.String(20), default="1.0")
    confidentiel   = db.Column(db.Boolean, default=False)

class Devis(db.Model):
    __tablename__ = "devis"
    id_devis         = db.Column(db.Integer, primary_key=True)
    id_audit         = db.Column(db.Integer, db.ForeignKey("audits.id_audit"))
    id_client        = db.Column(db.Integer, db.ForeignKey("clients.id_client"), nullable=False)
    reference_devis  = db.Column(db.String(50), nullable=False)
    statut           = db.Column(db.String(20), default="Brouillon")
    date_devis       = db.Column(db.Date, default=date.today)
    description      = db.Column(db.Text)
    montant_ht       = db.Column(db.Numeric(12,2), nullable=False)
    taux_tva         = db.Column(db.Numeric(4,2), default=20.00)
    notes            = db.Column(db.Text)
    date_acceptation = db.Column(db.Date)
    date_creation    = db.Column(db.DateTime, default=datetime.now)
    client           = db.relationship("Client", backref="devis")

class Facture(db.Model):
    __tablename__ = "factures"
    id_facture        = db.Column(db.Integer, primary_key=True)
    id_devis          = db.Column(db.Integer, db.ForeignKey("devis.id_devis"))
    id_audit          = db.Column(db.Integer, db.ForeignKey("audits.id_audit"))
    id_client         = db.Column(db.Integer, db.ForeignKey("clients.id_client"), nullable=False)
    reference_facture = db.Column(db.String(50), nullable=False)
    type_facture      = db.Column(db.String(20), default="Facture")
    date_facture      = db.Column(db.Date, default=date.today)
    description       = db.Column(db.Text)
    montant_ht        = db.Column(db.Numeric(12,2), nullable=False)
    taux_tva          = db.Column(db.Numeric(4,2), default=20.00)
    montant_paye      = db.Column(db.Numeric(12,2), default=0)
    date_paiement     = db.Column(db.Date)
    mode_paiement     = db.Column(db.String(20))
    notes             = db.Column(db.Text)
    mentions_legales  = db.Column(db.Text, default="TVA non applicable – article 293 B du CGI")
    date_creation     = db.Column(db.DateTime, default=datetime.now)
    client            = db.relationship("Client", backref="factures")

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/init-admin")
def init_admin():
    if User.query.first():
        return "Administrateur déjà créé."
    with app.app_context():
        db.create_all()
        user = User(
            username="admin",
            password=generate_password_hash("wolf2026")
        )
        db.session.add(user)
        db.session.commit()
    return "Administrateur créé ! Login: admin / Mot de passe: wolf2026"

@app.route("/")
@login_required
def dashboard():
    nb_clients    = Client.query.filter_by(actif=True).count()
    nb_biens      = Bien.query.filter_by(actif=True).count()
    nb_audits     = Audit.query.count()
    audits_cours  = Audit.query.filter(Audit.statut.in_(["En cours","Planifié"])).count()
    devis_envoyes = Devis.query.filter_by(statut="Envoyé").count()
    # CA total factures
    from sqlalchemy import func
    ca = db.session.query(func.sum(Facture.montant_ht)).scalar() or 0
    encaisse = db.session.query(func.sum(Facture.montant_paye)).scalar() or 0
    derniers_audits = Audit.query.order_by(Audit.date_creation.desc()).limit(5).all()
    return render_template("dashboard.html",
        nb_clients=nb_clients, nb_biens=nb_biens,
        nb_audits=nb_audits, audits_cours=audits_cours,
        devis_envoyes=devis_envoyes, ca=ca, encaisse=encaisse,
        derniers_audits=derniers_audits)

# ── CLIENTS ──────────────────────────────────

@app.route("/clients")
@login_required
def clients_liste():
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    return render_template("clients.html", clients=clients)

@app.route("/clients/nouveau", methods=["GET","POST"])
@login_required
def client_nouveau():
    if request.method == "POST":
        c = Client(
            type_client   = request.form["type_client"],
            nom           = request.form["nom"],
            prenom        = request.form.get("prenom"),
            raison_sociale= request.form.get("raison_sociale"),
            siret         = request.form.get("siret") or None,
            adresse       = request.form["adresse"],
            telephone     = request.form.get("telephone"),
            email         = request.form["email"],
            notes         = request.form.get("notes"),
        )
        db.session.add(c)
        db.session.commit()
        flash("Client créé avec succès.", "success")
        return redirect(url_for("clients_liste"))
    return render_template("client_form.html", client=None, titre="Nouveau client")

@app.route("/clients/<int:id>/modifier", methods=["GET","POST"])
@login_required
def client_modifier(id):
    c = Client.query.get_or_404(id)
    if request.method == "POST":
        c.type_client    = request.form["type_client"]
        c.nom            = request.form["nom"]
        c.prenom         = request.form.get("prenom")
        c.raison_sociale = request.form.get("raison_sociale")
        c.siret          = request.form.get("siret") or None
        c.adresse        = request.form["adresse"]
        c.telephone      = request.form.get("telephone")
        c.email          = request.form["email"]
        c.notes          = request.form.get("notes")
        db.session.commit()
        flash("Client mis à jour.", "success")
        return redirect(url_for("clients_liste"))
    return render_template("client_form.html", client=c, titre="Modifier le client")

@app.route("/clients/<int:id>/archiver")
@login_required
def client_archiver(id):
    c = Client.query.get_or_404(id)
    c.actif = False
    db.session.commit()
    flash("Client archivé.", "info")
    return redirect(url_for("clients_liste"))

# ── BIENS ─────────────────────────────────────

@app.route("/biens")
@login_required
def biens_liste():
    biens = Bien.query.filter_by(actif=True).order_by(Bien.reference_bien).all()
    return render_template("biens.html", biens=biens)

@app.route("/biens/nouveau", methods=["GET","POST"])
@login_required
def bien_nouveau():
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    if request.method == "POST":
        b = Bien(
            id_client          = request.form["id_client"],
            reference_bien     = request.form["reference_bien"],
            type_bien          = request.form["type_bien"],
            adresse            = request.form["adresse"],
            surface_m2         = request.form.get("surface_m2") or None,
            annee_construction = request.form.get("annee_construction") or None,
            nb_niveaux         = request.form.get("nb_niveaux") or None,
            type_chauffage     = request.form.get("type_chauffage"),
            type_ventilation   = request.form.get("type_ventilation"),
            type_isolation     = request.form.get("type_isolation"),
            dpe_classe         = request.form.get("dpe_classe") or None,
            dpe_date           = request.form.get("dpe_date") or None,
            notes              = request.form.get("notes"),
        )
        db.session.add(b)
        db.session.commit()
        flash("Bien créé avec succès.", "success")
        return redirect(url_for("biens_liste"))
    return render_template("bien_form.html", bien=None, clients=clients, titre="Nouveau bien")

@app.route("/biens/<int:id>/modifier", methods=["GET","POST"])
@login_required
def bien_modifier(id):
    b = Bien.query.get_or_404(id)
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    if request.method == "POST":
        b.id_client          = request.form["id_client"]
        b.reference_bien     = request.form["reference_bien"]
        b.type_bien          = request.form["type_bien"]
        b.adresse            = request.form["adresse"]
        b.surface_m2         = request.form.get("surface_m2") or None
        b.annee_construction = request.form.get("annee_construction") or None
        b.nb_niveaux         = request.form.get("nb_niveaux") or None
        b.type_chauffage     = request.form.get("type_chauffage")
        b.type_ventilation   = request.form.get("type_ventilation")
        b.type_isolation     = request.form.get("type_isolation")
        b.dpe_classe         = request.form.get("dpe_classe") or None
        b.dpe_date           = request.form.get("dpe_date") or None
        b.notes              = request.form.get("notes")
        db.session.commit()
        flash("Bien mis à jour.", "success")
        return redirect(url_for("biens_liste"))
    return render_template("bien_form.html", bien=b, clients=clients, titre="Modifier le bien")

# ── AUDITS ────────────────────────────────────

@app.route("/audits")
@login_required
def audits_liste():
    audits = Audit.query.order_by(Audit.date_creation.desc()).all()
    return render_template("audits.html", audits=audits)

@app.route("/audits/nouveau", methods=["GET","POST"])
@login_required
def audit_nouveau():
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    biens   = Bien.query.filter_by(actif=True).order_by(Bien.reference_bien).all()
    if request.method == "POST":
        a = Audit(
            id_client               = request.form["id_client"],
            id_bien                 = request.form["id_bien"],
            reference_audit         = request.form["reference_audit"],
            statut                  = request.form["statut"],
            type_audit              = request.form["type_audit"],
            date_visite             = request.form.get("date_visite") or None,
            date_livraison          = request.form.get("date_livraison") or None,
            auditeur                = request.form.get("auditeur"),
            consommation_avant_kwh  = request.form.get("consommation_avant_kwh") or None,
            consommation_apres_kwh  = request.form.get("consommation_apres_kwh") or None,
            gain_energetique_pct    = request.form.get("gain_energetique_pct") or None,
            classe_avant            = request.form.get("classe_avant") or None,
            classe_apres            = request.form.get("classe_apres") or None,
            recommandations         = request.form.get("recommandations"),
            observations            = request.form.get("observations"),
            montant_ht              = request.form.get("montant_ht") or None,
            taux_tva                = request.form.get("taux_tva") or 20.00,
            notes_internes          = request.form.get("notes_internes"),
        )
        db.session.add(a)
        db.session.commit()
        flash("Audit créé avec succès.", "success")
        return redirect(url_for("audits_liste"))
    return render_template("audit_form.html", audit=None, clients=clients, biens=biens, titre="Nouvel audit")

@app.route("/audits/<int:id>/modifier", methods=["GET","POST"])
@login_required
def audit_modifier(id):
    a = Audit.query.get_or_404(id)
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    biens   = Bien.query.filter_by(actif=True).order_by(Bien.reference_bien).all()
    if request.method == "POST":
        a.id_client              = request.form["id_client"]
        a.id_bien                = request.form["id_bien"]
        a.reference_audit        = request.form["reference_audit"]
        a.statut                 = request.form["statut"]
        a.type_audit             = request.form["type_audit"]
        a.date_visite            = request.form.get("date_visite") or None
        a.date_livraison         = request.form.get("date_livraison") or None
        a.auditeur               = request.form.get("auditeur")
        a.consommation_avant_kwh = request.form.get("consommation_avant_kwh") or None
        a.consommation_apres_kwh = request.form.get("consommation_apres_kwh") or None
        a.gain_energetique_pct   = request.form.get("gain_energetique_pct") or None
        a.classe_avant           = request.form.get("classe_avant") or None
        a.classe_apres           = request.form.get("classe_apres") or None
        a.recommandations        = request.form.get("recommandations")
        a.observations           = request.form.get("observations")
        a.montant_ht             = request.form.get("montant_ht") or None
        a.taux_tva               = request.form.get("taux_tva") or 20.00
        a.notes_internes         = request.form.get("notes_internes")
        db.session.commit()
        flash("Audit mis à jour.", "success")
        return redirect(url_for("audits_liste"))
    return render_template("audit_form.html", audit=a, clients=clients, biens=biens, titre="Modifier l'audit")

# ── DEVIS ─────────────────────────────────────

@app.route("/devis")
@login_required
def devis_liste():
    devis = Devis.query.order_by(Devis.date_creation.desc()).all()
    return render_template("devis.html", devis=devis)

@app.route("/devis/nouveau", methods=["GET","POST"])
@login_required
def devis_nouveau():
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    audits  = Audit.query.order_by(Audit.reference_audit).all()
    if request.method == "POST":
        d = Devis(
            id_client       = request.form["id_client"],
            id_audit        = request.form.get("id_audit") or None,
            reference_devis = request.form["reference_devis"],
            statut          = request.form["statut"],
            date_devis      = request.form.get("date_devis") or date.today(),
            description     = request.form.get("description"),
            montant_ht      = request.form["montant_ht"],
            taux_tva        = request.form.get("taux_tva") or 20.00,
            notes           = request.form.get("notes"),
        )
        db.session.add(d)
        db.session.commit()
        flash("Devis créé avec succès.", "success")
        return redirect(url_for("devis_liste"))
    return render_template("devis_form.html", devis=None, clients=clients, audits=audits, titre="Nouveau devis")

@app.route("/devis/<int:id>/modifier", methods=["GET","POST"])
@login_required
def devis_modifier(id):
    d = Devis.query.get_or_404(id)
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    audits  = Audit.query.order_by(Audit.reference_audit).all()
    if request.method == "POST":
        d.id_client      = request.form["id_client"]
        d.id_audit       = request.form.get("id_audit") or None
        d.reference_devis= request.form["reference_devis"]
        d.statut         = request.form["statut"]
        d.date_devis     = request.form.get("date_devis") or d.date_devis
        d.description    = request.form.get("description")
        d.montant_ht     = request.form["montant_ht"]
        d.taux_tva       = request.form.get("taux_tva") or 20.00
        d.notes          = request.form.get("notes")
        if request.form.get("date_acceptation"):
            d.date_acceptation = request.form["date_acceptation"]
        db.session.commit()
        flash("Devis mis à jour.", "success")
        return redirect(url_for("devis_liste"))
    return render_template("devis_form.html", devis=d, clients=clients, audits=audits, titre="Modifier le devis")

# ── FACTURES ──────────────────────────────────

@app.route("/factures")
@login_required
def factures_liste():
    factures = Facture.query.order_by(Facture.date_creation.desc()).all()
    return render_template("factures.html", factures=factures)

@app.route("/factures/nouvelle", methods=["GET","POST"])
@login_required
def facture_nouvelle():
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    audits  = Audit.query.order_by(Audit.reference_audit).all()
    devis   = Devis.query.order_by(Devis.reference_devis).all()
    if request.method == "POST":
        f = Facture(
            id_client         = request.form["id_client"],
            id_audit          = request.form.get("id_audit") or None,
            id_devis          = request.form.get("id_devis") or None,
            reference_facture = request.form["reference_facture"],
            type_facture      = request.form["type_facture"],
            date_facture      = request.form.get("date_facture") or date.today(),
            description       = request.form.get("description"),
            montant_ht        = request.form["montant_ht"],
            taux_tva          = request.form.get("taux_tva") or 20.00,
            montant_paye      = request.form.get("montant_paye") or 0,
            date_paiement     = request.form.get("date_paiement") or None,
            mode_paiement     = request.form.get("mode_paiement") or None,
            notes             = request.form.get("notes"),
            mentions_legales  = request.form.get("mentions_legales",
                                "TVA non applicable – article 293 B du CGI"),
        )
        db.session.add(f)
        db.session.commit()
        flash("Facture créée avec succès.", "success")
        return redirect(url_for("factures_liste"))
    return render_template("facture_form.html", facture=None,
        clients=clients, audits=audits, devis=devis, titre="Nouvelle facture")

@app.route("/factures/<int:id>/modifier", methods=["GET","POST"])
@login_required
def facture_modifier(id):
    f = Facture.query.get_or_404(id)
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    audits  = Audit.query.order_by(Audit.reference_audit).all()
    devis   = Devis.query.order_by(Devis.reference_devis).all()
    if request.method == "POST":
        f.id_client         = request.form["id_client"]
        f.id_audit          = request.form.get("id_audit") or None
        f.id_devis          = request.form.get("id_devis") or None
        f.reference_facture = request.form["reference_facture"]
        f.type_facture      = request.form["type_facture"]
        f.date_facture      = request.form.get("date_facture") or f.date_facture
        f.description       = request.form.get("description")
        f.montant_ht        = request.form["montant_ht"]
        f.taux_tva          = request.form.get("taux_tva") or 20.00
        f.montant_paye      = request.form.get("montant_paye") or 0
        f.date_paiement     = request.form.get("date_paiement") or None
        f.mode_paiement     = request.form.get("mode_paiement") or None
        f.notes             = request.form.get("notes")
        f.mentions_legales  = request.form.get("mentions_legales", f.mentions_legales)
        db.session.commit()
        flash("Facture mise à jour.", "success")
        return redirect(url_for("factures_liste"))
    return render_template("facture_form.html", facture=f,
        clients=clients, audits=audits, devis=devis, titre="Modifier la facture")

# ── DOCUMENTS ─────────────────────────────────

@app.route("/documents")
@login_required
def documents_liste():
    documents = Document.query.order_by(Document.date_ajout.desc()).all()
    return render_template("documents.html", documents=documents)

@app.route("/documents/nouveau", methods=["GET","POST"])
@login_required
def document_nouveau():
    audits  = Audit.query.order_by(Audit.reference_audit).all()
    clients = Client.query.filter_by(actif=True).order_by(Client.nom).all()
    biens   = Bien.query.filter_by(actif=True).order_by(Bien.reference_bien).all()
    if request.method == "POST":
        doc = Document(
            id_audit       = request.form.get("id_audit") or None,
            id_client      = request.form.get("id_client") or None,
            id_bien        = request.form.get("id_bien") or None,
            type_document  = request.form["type_document"],
            nom_fichier    = request.form["nom_fichier"],
            chemin_fichier = request.form["chemin_fichier"],
            format_fichier = request.form.get("format_fichier") or None,
            description    = request.form.get("description"),
            ajoute_par     = request.form.get("ajoute_par"),
            version        = request.form.get("version") or "1.0",
            confidentiel   = "confidentiel" in request.form,
        )
        db.session.add(doc)
        db.session.commit()
        flash("Document ajouté avec succès.", "success")
        return redirect(url_for("documents_liste"))
    return render_template("document_form.html", document=None,
        audits=audits, clients=clients, biens=biens, titre="Nouveau document")

if __name__ == "__main__":
    app.run(debug=True)
