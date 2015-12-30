from flask import session, g, request, flash, Blueprint
from flask.ext.login import login_user, logout_user, current_user, login_required

from airtng_flask.forms import RegisterForm, LoginForm, VacationPropertyForm
from airtng_flask.view_helpers import twiml, view, redirect_to, view_with_params
from airtng_flask.models import init_models_module


def construct_view_blueprint(app, db, login_manager, bcrypt):
    views = Blueprint("views", __name__)

    init_models_module(db, bcrypt)
    from airtng_flask.models.user import User
    from airtng_flask.models.vacation_property import VacationProperty
    from airtng_flask.models.reservation import Reservation

    @views.route('/', methods=["GET", "POST"])
    @views.route('/register', methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if request.method == 'POST':
            if form.validate_on_submit():

                if User.query.filter(User.email == form.email.data).count() > 0:
                    form.email.errors.append("Email address already in use.")
                    return view('register', form)

                user = User(
                        name=form.name.data,
                        email=form.email.data,
                        password=form.password.data,
                        phone_number='+%r%r' % (form.country_code.data, form.phone_number.data)
                )
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)

                return redirect_to('views', 'home')
            else:
                return view('register', form)

        return view('register', form)

    @views.route('/login', methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                candidate_user = User.query.filter(User.email == form.email.data).first()

                if candidate_user is None or not bcrypt.check_password_hash(candidate_user.password,
                                                                            form.password.data):
                    form.password.errors.append("Invalid credentials.")
                    return view('login', form)

                login_user(candidate_user, remember=True)
                return redirect_to('views', 'home')
        return view('login', form)

    @views.route('/logout', methods=["POST"])
    def logout():
        logout_user()
        return redirect_to('views', 'home')

    @views.route('/home', methods=["GET"])
    @login_required
    def home():
        return view('home')

    @views.route('/properties', methods=["GET"])
    @login_required
    def properties():
        vacation_properties = VacationProperty.query.all()
        return view_with_params('properties', vacation_properties=vacation_properties)

    @views.route('/properties/new', methods=["GET", "POST"])
    @login_required
    def new_property():
        form = VacationPropertyForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                host = User.query.get(current_user.get_id())

                property = VacationProperty(form.description.data, form.image_url.data, host)
                db.session.add(property)
                db.session.commit()
                return redirect_to('views', 'properties')

        return view('property_new', form)

    @views.route('/reservations/<id>', methods=["GET", "POST"])
    def new_reservation(id=None):
        return "new reservation"

    # controller utils
    @views.before_request
    def before_request():
        g.user = current_user
        uri_pattern = request.url_rule
        if current_user.is_authenticated and (uri_pattern == '/login' or uri_pattern == '/register'):
            redirect_to('views', 'home')

    @login_manager.user_loader
    def load_user(id):
        try:
            return User.query.get(id)
        except:
            return None

    return views
