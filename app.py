import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user,LoginManager

# Initialize the Flask application
app = Flask(__name__)

# Configure the app (make sure you've set a secret key for sessions)
app.config['SECRET_KEY'] = 'fdtygt5e5re4ere43rt435erdrs34e56fdrde3w221234567ytgytuih8uijhu87y6fvb  '

# Initialize the LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Optionally, specify the login view
login_manager.login_view = 'login'  # Redirect to 'login' view if not logged in

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'hvfgvgyv67g8i6555436789765434576fgxfsx65756545erdf5554r676879t65re4d4d4hjgfyyuh8yyghi98y7tf6ygugbu'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///department.db'  # Use MySQL if needed
app.config['UPLOAD_FOLDER'] = 'path/to/your/static/uploads'

db = SQLAlchemy(app)


# -----------------
# Database Model
# -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    regno = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    position = db.Column(db.String(100), nullable=False)
    candidate_id = db.Column(db.Integer, nullable=True)  # can be null for 'NO' votes
    decision = db.Column(db.String(10))  # 'yes', 'no' or 'selected'

    user = db.relationship('User', backref='votes')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminAddDues(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    regno = db.Column(db.String(100), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    sessions_paid = db.Column(db.String(255), nullable=False)
    date_filled = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=False)

class ElectoralCandidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    regno = db.Column(db.String(20), unique=True, nullable=False)
    position = db.Column(db.String(50), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=False)  # path to image

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')  # <--- ADD THIS LINE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Change 'community_name' to 'name'
    description = db.Column(db.Text, nullable=False)
    profile_picture = db.Column(db.String(150), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User', backref='communities')

# -----------------
#home
@app.route('/home', methods=['GET', 'POST'])
def index():
        return render_template('index.html',)



# Signup Route
# -----------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['signupName']
        email = request.form['signupEmail']
        regno = request.form['regno']
        phone = request.form['phone']
        password = request.form['signupPassword']
        confirm = request.form['confirmpassword']

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        # Check for existing email or reg number
        existing_user = User.query.filter((User.email == email) | (User.regno == regno)).first()
        if existing_user:
            flash('Email or Registration Number already exists, please log in', 'danger')
            return redirect(url_for('login'))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(fullname=fullname, email=email, regno=regno, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Send Welcome Email
        send_welcome_email(email, fullname)

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


# -----------------
# Welcome Email Function
# -----------------
def send_welcome_email(to_email, fullname):
    msg = EmailMessage()
    msg['Subject'] = 'Welcome to Department Of Public Administration, University Of Nigeria, Nsukka Platform!'
    msg['From'] = 'yourgmail@gmail.com'
    msg['To'] = to_email
    msg.set_content(f"Dear {fullname},\n\nWelcome! Your account has been created successfully.\n\nThank you!")

    # Replace with your actual Gmail credentials
    gmail_user = 'yourgmail@gmail.com'
    gmail_password = 'your_app_password'  # App Password if 2FA is enabled

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)
    except Exception as e:
        print("Email failed:", e)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['loginEmail']
        password = request.form['loginPassword']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    flash('Welcome To Your Dashboard.', 'success')
    user = User.query.get(session['user_id'])


    return render_template('dashboard.html', user=user)

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        flash('Please log in to access settings.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings.html', user=user)

@app.route('/friendrequest', methods=['GET', 'POST'])
def friendrequest():
    if 'user_id' not in session:
        flash('Please log in to access settings.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        action = request.form.get('action')
        receiver_id = request.form.get('receiver_id')

        if action == 'send':
            # Check if request already exists
            existing_request = FriendRequest.query.filter_by(sender_id=user.id, receiver_id=receiver_id).first()
            if not existing_request:
                new_request = FriendRequest(sender_id=user.id, receiver_id=receiver_id, status='pending')
                db.session.add(new_request)
                db.session.commit()
                flash('Friend request sent successfully!', 'success')
        elif action == 'cancel':
            existing_request = FriendRequest.query.filter_by(sender_id=user.id, receiver_id=receiver_id).first()
            if existing_request:
                db.session.delete(existing_request)
                db.session.commit()
                flash('Friend request canceled.', 'info')

        return redirect(url_for('friendrequest'))

    # Get all users except current user
    all_users = User.query.filter(User.id != user.id).all()

    # IDs of users I already sent friend request to (pending)
    sent_requests = FriendRequest.query.filter_by(sender_id=user.id, status='pending').all()
    sent_request_ids = [req.receiver_id for req in sent_requests]

    # IDs of users I am already friends with (both accepted)
    my_friends = Friendship.query.filter(
        (Friendship.user1_id == user.id) | (Friendship.user2_id == user.id)
    ).all()
    friends_ids = []
    for f in my_friends:
        if f.user1_id == user.id:
            friends_ids.append(f.user2_id)
        else:
            friends_ids.append(f.user1_id)

    return render_template('friendrequest.html', 
                           user=user, 
                           all_users=all_users, 
                           sent_request_ids=sent_request_ids, 
                           friends_ids=friends_ids)

@app.route('/community', methods=['GET', 'POST'])

@app.route('/view_friends')
def view_friends():
    user_id = session.get('user_id')
    
    # Fetch accepted friends for the user
    friendships = Friendship.query.filter(
        (Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)
    ).all()
    
    friends = []
    for friendship in friendships:
        if friendship.user1_id == user_id:
            friend = User.query.get(friendship.user2_id)
        else:
            friend = User.query.get(friendship.user1_id)
        if friend:
            friends.append(friend)
    communities = Community.query.all()

    return render_template('view_friends.html', friends=friends,communitties=communities)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/create_community', methods=['GET', 'POST'])
def create_community():
    if request.method == 'POST':
        community_name = request.form['community_name']
        description = request.form['description']
        profile_picture = request.files['profile_picture']  # this is a FileStorage object

        if profile_picture:
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join('static/uploads', filename)  # choose your upload folder
            profile_picture.save(filepath)  # save the file

            # Now save only the filename (or filepath) to the database
            new_community = Community(
                name=community_name,
                description=description,
                profile_picture=filename,  # or 'filepath' if you want full path
                admin_id=session['user_id'],
                created_at=datetime.now()
            )
            db.session.add(new_community)
            db.session.commit()

            flash('Community created successfully!', 'success')
            return redirect(url_for('community_page'))

    return render_template('createcommunity.html')

@app.route('/community.html')
def community_page():
    communities = Community.query.all()
    return render_template('communities.html', communities=communities)



@app.route('/chatwithfriends', methods=['GET', 'POST'])
def privatechat():
    if 'user_id' not in session:
        flash('Please log in to access settings.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    friend_id = request.args.get('friend_id')  # 👈 Get the friend ID from the URL

    if not friend_id:
        flash('No friend selected to chat with.', 'warning')
        return redirect(url_for('friendrequest'))
    
    friend = User.query.get(friend_id)

    if not friend:
        flash('Friend not found.', 'danger')
        return redirect(url_for('friendrequest'))

    return render_template('chat.html', user=user, friend=friend)




@app.route('/block-user', methods=['POST'])
def block_user():
    user_id = request.json['userId']
    # Code to block the user goes here
    return jsonify({'success': True})

@app.route('/unblock-user', methods=['POST'])
def unblock_user():
    user_id = request.json['userId']
    # Code to unblock the user goes here
    return jsonify({'success': True})


@app.route('/payments', methods=['GET', 'POST'])
def payments():
    if 'user_id' not in session:
        flash('Please log in to access settings.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('payment.html', user=user)



@app.route('/messages')
def messages():
    if 'user_id' not in session:
        flash('Please log in to view messages.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # Get friend requests sent to this user (pending)
    incoming_requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()

    return render_template('messages.html', user=user, incoming_requests=incoming_requests)

@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    """Accept an incoming friend request."""
    friend_request = FriendRequest.query.get_or_404(request_id)

    # Use session to get the user ID instead of current_user
    user_id = session.get('user_id')

    if user_id and friend_request.receiver_id == user_id:
        # Create a new friendship
        new_friendship = Friendship(
            user1_id=friend_request.sender_id,
            user2_id=friend_request.receiver_id
        )
        db.session.add(new_friendship)

        # Update the friend request status
        friend_request.status = 'accepted'
        db.session.commit()

        flash('Friend request accepted!', 'success')
    else:
        flash('You cannot accept this request.', 'danger')

    return redirect(url_for('messages'))

@app.route('/decline_friend_request/<int:request_id>', methods=['POST'])
def decline_friend_request(request_id):
    """Decline an incoming friend request."""
    friend_request = FriendRequest.query.get_or_404(request_id)

    # Use session to get the user ID instead of current_user
    user_id = session.get('user_id')

    if user_id and friend_request.receiver_id == user_id:
        # Update the friend request status to declined
        friend_request.status = 'declined'
        db.session.commit()

        flash('Friend request declined.', 'info')
    else:
        flash('You cannot decline this request.', 'danger')

    return redirect(url_for('messages'))


@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('admin_login'))
    admin = Admin.query.get(session['admin_id'])
    flash('Admin registered successfully!.', 'success')
    admin = admin.query.get(session['admin_id'])

    return render_template('admin.html',admin=admin)



@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))  # Create this route later
        else:
            flash('Invalid credentials!', 'danger')

    return render_template('admin_login.html')


@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if Admin.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('admin_signup'))
        if Admin.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('admin_signup'))

        new_admin = Admin(fullname=fullname, email=email, username=username)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash('Admin registered successfully! Please login.', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_signup.html')


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))




@app.route('/add-dues', methods=['GET', 'POST'])
def add_dues():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        regno = request.form.get('reg_number')
        sessions = request.form.getlist('session[]')

        if not fullname or not regno or not sessions:
            flash('All fields are required.', 'danger')
            return redirect(url_for('add_dues'))

        admin_id = session.get('admin_id')  # assuming admin is logged in
        if not admin_id:
            flash('Admin login required to submit form.', 'danger')
            return redirect(url_for('admin_login'))  # redirect to login or some safe page

        dues = AdminAddDues(
            fullname=fullname,
            regno=regno,
            admin_id=admin_id,
            user_id=admin_id,  # Make sure this matches your model if user_id is required
            sessions_paid=', '.join(sessions)
        )

        db.session.add(dues)
        db.session.commit()
        flash('Dues successfully recorded.', 'success')
        return redirect(url_for('add_dues'))

    return render_template('admin_adddues.html')
@app.route('/admin_addcandidate', methods=['GET', 'POST'])
def add_candidate():
    if 'admin_id' not in session:
        flash("You must be logged in as admin to access this page.", "warning")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        fullname = request.form['fullname']
        regno = request.form['regno']
        position = request.form['position']
        profile_pic = request.files['profile_pic']

        dues_paid = AdminAddDues.query.filter_by(regno=regno).first()
        if not dues_paid:
            flash("Candidate has not paid departmental dues.", "danger")
            return redirect(url_for('add_candidate'))

        already_registered = ElectoralCandidate.query.filter_by(regno=regno).first()
        if already_registered:
            flash("Candidate already registered.", "warning")
            return redirect(url_for('add_candidate'))

        if not profile_pic:
            flash("Please upload a profile picture.", "danger")
            return redirect(url_for('add_candidate'))

        filename = secure_filename(profile_pic.filename)
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        profile_path = os.path.join(upload_folder, filename)
        profile_pic.save(profile_path)

        new_candidate = ElectoralCandidate(
            fullname=fullname,
            regno=regno,
            position=position,
            profile_pic=filename
        )
        db.session.add(new_candidate)
        db.session.commit()

        flash("Candidate added successfully.", "success")
        return redirect(url_for('add_candidate'))

    # GET request - fetch candidates and their vote counts
    all_candidates = ElectoralCandidate.query.all()
    vote_counts = db.session.query(
        Vote.candidate_id,
        db.func.count(Vote.id).label('vote_count')
    ).group_by(Vote.candidate_id).all()
    
    vote_dict = {candidate_id: count for candidate_id, count in vote_counts}

    candidates_by_position = {}

    for candidate in all_candidates:
        position = candidate.position
        candidate.vote_count = vote_dict.get(candidate.id, 0)  # Add vote_count dynamically
        if position not in candidates_by_position:
            candidates_by_position[position] = []
        candidates_by_position[position].append(candidate)

    return render_template('admin_addcandidates.html', candidates_by_position=candidates_by_position)

@app.route('/results')
def results():
    if 'user_id' not in session:
        flash("Please log in or sign up to view the election results.", "warning")
        return redirect(url_for('login'))

     # GET request - fetch candidates and their vote counts
    all_candidates = ElectoralCandidate.query.all()
    vote_counts = db.session.query(
        Vote.candidate_id,
        db.func.count(Vote.id).label('vote_count')
    ).group_by(Vote.candidate_id).all()
    
    vote_dict = {candidate_id: count for candidate_id, count in vote_counts}

    candidates_by_position = {}

    for candidate in all_candidates:
        position = candidate.position
        candidate.vote_count = vote_dict.get(candidate.id, 0)  # Add vote_count dynamically
        if position not in candidates_by_position:
            candidates_by_position[position] = []
        candidates_by_position[position].append(candidate)

    return render_template('results.html', candidates_by_position=candidates_by_position)

@app.route('/students-vote', methods=['GET', 'POST'])
def vote():
    if 'user_id' not in session:
        flash("Please log in to access the voting page.", "danger")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    dues_record = AdminAddDues.query.filter_by(regno=user.regno).first()
    if not dues_record:
        flash("You are not eligible to vote. Please ensure your dues are cleared.", "warning")
        return redirect(url_for('dashboard'))

    # Prevent multiple votes
    previous_votes = Vote.query.filter_by(user_id=user.id).first()
    if previous_votes:
        flash("You have already voted.", "warning")
        return redirect(url_for('results'))

    candidates = ElectoralCandidate.query.all()
    candidates_by_position = {}
    for candidate in candidates:
        candidates_by_position.setdefault(candidate.position, []).append(candidate)

    if request.method == 'POST':
        for position, candidates_list in candidates_by_position.items():
            vote_value = request.form.get(position)

            if not vote_value:
                flash(f"You must vote for the position: {position}", "danger")
                return redirect(url_for('vote'))

            # Handle YES/NO votes
            if vote_value.startswith('yes-') or vote_value.startswith('no-'):
                vote_type, candidate_id = vote_value.split('-')
                decision = vote_type  # yes or no
                candidate_id = int(candidate_id)
            else:
                decision = 'selected'
                candidate_id = int(vote_value)

            # Save vote
            vote = Vote(user_id=user.id, position=position, candidate_id=candidate_id, decision=decision)
            db.session.add(vote)

        db.session.commit()
        flash("Your vote has been submitted successfully.", "success")
        return redirect(url_for('dashboard'))

    return render_template('vote_dashboard.html', candidates_by_position=candidates_by_position)

  

@app.route('/vote_timer')
def vote_timer():
    if 'user_id' not in session:
        flash("Please log in or sign up to view the election results.", "warning")
        return redirect(url_for('login'))

    now = datetime.now()

    if now < ELECTION_START:
        return redirect(url_for('wait_page'))
    elif ELECTION_START <= now <= ELECTION_END:
        return render_template('vote_dashboard.html')  # Your actual voting page
    else:
        return redirect(url_for('results'))

@app.route('/wait')
def wait_page():
    return render_template('wait.html')


@app.route("/admin-dashboard_details")
def details():
    if 'admin_id' not in session:
        flash("You must be logged in as admin to access this page.", "warning")
        return redirect(url_for('admin_login'))

    users = User.query.all()

    voters = (
        db.session.query(User)
        .join(Vote)
        .filter(Vote.candidate_id.isnot(None))
        .distinct()
        .all()
    )

    dues_payers = (
        db.session.query(User)
        .join(AdminAddDues, AdminAddDues.user_id == User.id)
        .distinct()
        .all()
    )

    candidates = ElectoralCandidate.query.all()

    return render_template("details.html", users=users, voters=voters, dues_payers=dues_payers, candidates=candidates)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
