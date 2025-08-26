import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from models import db, User, Skill, Swap, UserSkill
from matching import find_matches_for_user
from config import Config

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # ✅ Flask-Migrate
    Migrate(app, db)

    # ---------------- ROUTES ---------------- #

    @app.route("/")
    def index():
        return render_template("index.html")

    # ---------- EXPLORE ---------- #
    @app.route("/explore")
    def explore():
        q = request.args.get("q", "")
        category = request.args.get("category", "")
        difficulty = request.args.get("difficulty", "")
        location = request.args.get("location", "")

        query = Skill.query.options(
            joinedload(Skill.users).joinedload(UserSkill.user)
        )

        if q:
            query = query.filter(Skill.name.ilike(f"%{q}%"))
        if category:
            query = query.filter(Skill.category == category)
        if difficulty:
            query = query.filter(Skill.difficulty == difficulty)
        if location:
            query = query.filter(Skill.location.ilike(f"%{location}%"))

        skills = query.all()

        matches = []
        if current_user.is_authenticated:
            matches = (
                UserSkill.query.options(joinedload(UserSkill.skill))
                .filter(UserSkill.user_id != current_user.id)
                .limit(6)
                .all()
            )

        return render_template("explore.html", skills=skills, matches=matches)

    # ---------- REGISTER ---------- #
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            pw = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

            if User.query.filter_by(email=email).first():
                flash("Email already registered", "error")
                return redirect(url_for("register"))

            u = User(name=name, email=email, password_hash=pw)
            db.session.add(u)
            db.session.commit()
            flash("Registered! Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("auth_register.html")

    # ---------- LOGIN ---------- #
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            pw = request.form["password"]

            u = User.query.filter_by(email=email).first()
            if u and bcrypt.check_password_hash(u.password_hash, pw):
                login_user(u)
                return redirect(url_for("dashboard"))

            flash("Invalid credentials", "error")
        return render_template("auth_login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    # ---------- DASHBOARD ---------- #
    @app.route("/dashboard")
    @login_required
    def dashboard():
        matches = find_matches_for_user(current_user.id, limit=8)

        offered_count = UserSkill.query.filter_by(user_id=current_user.id, relation="offer").count()
        wanted_count = UserSkill.query.filter_by(user_id=current_user.id, relation="want").count()
        active_requests = Swap.query.filter(
            ((Swap.requester_id == current_user.id) | (Swap.responder_id == current_user.id))
            & (Swap.status == "pending")
        ).count()
        completed_swaps = Swap.query.filter(
            ((Swap.requester_id == current_user.id) | (Swap.responder_id == current_user.id))
            & (Swap.status == "completed")
        ).count()

        stats = {
            "offered_count": offered_count,
            "wanted_count": wanted_count,
            "active_requests": active_requests,
            "completed_swaps": completed_swaps,
        }

        return render_template("dashboard.html", matches=matches, stats=stats)

    # ---------- PROFILE ---------- #
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            bio = request.form.get("bio", "")
            offered = [s.strip() for s in request.form.get("offered", "").split(",") if s.strip()]
            wanted = [s.strip() for s in request.form.get("wanted", "").split(",") if s.strip()]

            current_user.bio = bio

            if "profile_pic" in request.files:
                pic = request.files["profile_pic"]
                if pic and pic.filename:
                    filename = secure_filename(pic.filename)
                    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    pic.save(path)
                    current_user.profile_pic = filename

            # Clear old skills
            for us in list(current_user.skills):
                db.session.delete(us)

            # Helper
            def get_or_create_skill(name: str) -> Skill:
                name_norm = name.strip()
                sk = Skill.query.filter_by(name=name_norm).first()
                if not sk:
                    sk = Skill(name=name_norm)
                    db.session.add(sk)
                    try:
                        db.session.flush()
                    except IntegrityError:
                        db.session.rollback()
                        sk = Skill.query.filter_by(name=name_norm).first()
                return sk

            for name in offered:
                sk = get_or_create_skill(name)
                db.session.add(UserSkill(user_id=current_user.id, skill_id=sk.id, relation="offer"))

            for name in wanted:
                sk = get_or_create_skill(name)
                db.session.add(UserSkill(user_id=current_user.id, skill_id=sk.id, relation="want"))

            db.session.commit()
            flash("Profile updated", "success")
            return redirect(url_for("profile"))

        offered_skills = [us.skill.name for us in current_user.skills if us.relation == "offer"]
        wanted_skills = [us.skill.name for us in current_user.skills if us.relation == "want"]

        return render_template(
            "profile.html",
            offered_skills=offered_skills,
            wanted_skills=wanted_skills,
            bio=current_user.bio,
            profile_pic=current_user.profile_pic,
        )

    # ---------- SWAP REQUEST CREATION ---------- #
    @app.route("/request/<int:user_id>", methods=["GET", "POST"])
    @login_required
    def request_swap(user_id):
        other = db.session.get(User, user_id)
        if not other:
            flash("User not found", "error")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            offered_skill = request.form.get("offered", "").strip()
            wanted_skill = request.form.get("wanted", "").strip()

            os = Skill.query.filter_by(name=offered_skill).first()
            ws = Skill.query.filter_by(name=wanted_skill).first()

            if not os or not ws:
                flash("Invalid skills selected.", "error")
                return redirect(url_for("request_swap", user_id=user_id))

            swap = Swap(
                requester_id=current_user.id,
                responder_id=other.id,
                offered_skill_id=os.id,
                wanted_skill_id=ws.id,
                status="pending"
            )
            db.session.add(swap)
            db.session.commit()
            flash("Swap request sent!", "success")
            return redirect(url_for("dashboard"))

        return render_template("request_swap.html", other=other)

    # ---------- VIEW SENT SWAPS ---------- #
    @app.route("/sent_requests")
    @login_required
    def sent_requests():
        requests = (
            Swap.query
            .filter_by(requester_id=current_user.id)
            .order_by(Swap.created_at.desc())
            .all()
        )
        return render_template("sent_requests.html", requests=requests)

    # ---------- VIEW RECEIVED SWAPS ---------- #
    @app.route("/received_requests")
    @login_required
    def received_requests():
        requests = (
            Swap.query
            .filter_by(responder_id=current_user.id)
            .order_by(Swap.created_at.desc())
            .all()
        )
        return render_template("received_requests.html", requests=requests)

    # ---------- ACCEPT / REJECT ---------- #
    @app.route("/requests/<int:swap_id>/<action>", methods=["POST"])
    @login_required
    def update_swap_status(swap_id, action):
        swap = db.session.get(Swap, swap_id)
        if not swap:
            abort(404)

        if swap.responder_id != current_user.id:
            flash("Not authorized", "error")
            return redirect(url_for("received_requests"))

        if action == "accept":
            swap.status = "accepted"
            flash("Swap accepted!", "success")
        elif action == "reject":
            swap.status = "rejected"
            flash("Swap rejected.", "info")

        db.session.commit()
        return redirect(url_for("received_requests"))

    # ---------- SKILL DETAIL ---------- #
    @app.route("/skill/<int:skill_id>")
    def skill_detail(skill_id):
        skill = Skill.query.options(
            joinedload(Skill.users).joinedload(UserSkill.user)
        ).filter_by(id=skill_id).first()

        if not skill:
            abort(404)

        owners = [us.user for us in skill.users]
        other_skills = {}
        for owner in owners:
            owner_skills = [us.skill for us in owner.skills if us.skill.id != skill.id]
            if owner_skills:
                other_skills[owner] = owner_skills

        return render_template("skill_detail.html", skill=skill, owners=owners, other_skills=other_skills)

    # ---------- USER PROFILE ---------- #
    @app.route("/user/<int:user_id>")
    def user_profile(user_id):
        user = User.query.options(
            joinedload(User.skills).joinedload(UserSkill.skill)
        ).filter_by(id=user_id).first()

        if not user:
            abort(404)

        skills = [us.skill for us in user.skills]

        return render_template("user_profile.html", user=user, skills=skills)

    return app


# 👇 Needed for `flask run`
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
