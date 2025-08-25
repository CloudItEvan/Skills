from app import create_app
from models import db, User, Skill, UserSkill


app = create_app()
with app.app_context():
db.drop_all(); db.create_all()


def add_user(name, email, offers, wants):
from flask_bcrypt import Bcrypt
b = Bcrypt(app)
u = User(name=name, email=email, password_hash=b.generate_password_hash('pass123').decode('utf-8'))
db.session.add(u); db.session.flush()
def ensure_skill(n):
from models import Skill
s = Skill.query.filter_by(name=n).first()
if not s:
s = Skill(name=n); db.session.add(s); db.session.flush()
return s
for o in offers:
s = ensure_skill(o)
db.session.add(UserSkill(user_id=u.id, skill_id=s.id, relation='offer'))
for w in wants:
s = ensure_skill(w)
db.session.add(UserSkill(user_id=u.id, skill_id=s.id, relation='want'))
return u


add_user('Aisha','a@a.com',["Python","Data Viz"],["UI/UX","Branding"])
add_user('Raj','r@r.com',["Guitar","Hindi"],["French","React"])
add_user('Eva','e@e.com',["SQL","UI/UX"],["Public Speaking","Photography"])
db.session.commit()
print('Seeded! Users: 3')