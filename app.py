import os
import random
import json
from datetime import datetime
import requests
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Match, Team, TeamMember, Message, Project, Hackathon, Notification, Rating
import google.generativeai as genai
from rag_engine import retrieve_similar_projects, build_rag_context_block

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev_tinder_super_secret_hackathon_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# API Setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ----------------- COMPATIBILITY MATCHING ALGORITHM -----------------


def calculate_compatibility(user_a, user_b):
    """
    Calculates match compatibility between two users.
    Skills (30%), Complementarity (25%), Project Interest (20%), Availability (15%), Experience (10%)
    """
    if user_a.id == user_b.id:
        return 0

    skills_a = set(user_a.get_skills_list())
    skills_b = set(user_b.get_skills_list())

    # 1. Skill Similarity (30%)
    if not skills_a and not skills_b:
        skill_sim_score = 0
    else:
        union = skills_a.union(skills_b)
        intersection = skills_a.intersection(skills_b)
        skill_sim_score = (len(intersection) / len(union)) * 30 if union else 0

    # 2. Skill Complementarity (25%)
    frontend_skills = {'HTML', 'CSS', 'JavaScript', 'React', 'UI UX'}
    backend_skills = {'Node', 'Python', 'Flask', 'Django', 'DevOps'}
    ai_skills = {'AI', 'Machine Learning'}
    security_skills = {'Cybersecurity'}

    def get_categories(skills):
        cats = set()
        if skills.intersection(frontend_skills):
            cats.add('frontend')
        if skills.intersection(backend_skills):
            cats.add('backend')
        if skills.intersection(ai_skills):
            cats.add('ai')
        if skills.intersection(security_skills):
            cats.add('security')
        return cats

    cats_a = get_categories(skills_a)
    cats_b = get_categories(skills_b)

    if not cats_a and not cats_b:
        complementarity_score = 0
    else:
        # Symmetrical difference: skills one has that the other doesn't
        diff = cats_a.symmetric_difference(cats_b)
        complementarity_score = (len(diff) / 4.0) * 25
        complementarity_score = min(complementarity_score, 25)

    # 3. Project Interest Similarity (20%)
    interests = [
        'AI',
        'Web Development',
        'Cybersecurity',
        'Open Source',
        'Blockchain']
    interests_a = {
        i for i in interests if i.lower() in (
            user_a.bio or '').lower() or i.lower() in (
            user_a.skills or '').lower()}
    interests_b = {
        i for i in interests if i.lower() in (
            user_b.bio or '').lower() or i.lower() in (
            user_b.skills or '').lower()}
    if not interests_a and not interests_b:
        interest_score = 10
    else:
        union_int = interests_a.union(interests_b)
        intersect_int = interests_a.intersection(interests_b)
        interest_score = (len(intersect_int) / len(union_int)
                          ) * 20 if union_int else 10

    # 4. Availability Match (15%)
    avail_a = user_a.availability or 'Weekends'
    avail_b = user_b.availability or 'Weekends'
    if avail_a == avail_b:
        avail_score = 15
    elif avail_a == 'Full Time' or avail_b == 'Full Time':
        avail_score = 12
    else:
        avail_score = 5

    # 5. Experience Match (10%)
    exp_levels = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
    lvl_a = exp_levels.get(user_a.experience_level or 'Beginner', 1)
    lvl_b = exp_levels.get(user_b.experience_level or 'Beginner', 1)
    diff_lvl = abs(lvl_a - lvl_b)
    if diff_lvl == 0:
        exp_score = 10
    elif diff_lvl == 1:
        exp_score = 7
    else:
        exp_score = 4

    total_score = skill_sim_score + complementarity_score + \
        interest_score + avail_score + exp_score
    return round(min(max(total_score, 15), 98))

# ----------------- AI GENERATOR FALLBACKS -----------------


def generate_project_idea_mock(skills, theme, difficulty, retrieved=None):
    """Realistic offline fallback project idea generation."""
    title_themes = {
        'AI': [
            f"Smart {theme} Matcher",
            "DocuSynth AI",
            "OmniVision Health",
            "EcoAgent AI"],
        'Web Development': [
            "Dev Tinder",
            "TaskStream Flow",
            "LinkSphere",
            "HackerRank Analytics"],
        'Cybersecurity': [
            "Sentinel Shield AI",
            "ZeroTrust Portal",
            "AuthVault",
            "PhishCatcher Pro"],
        'Open Source': [
            "GitCollab Dashboard",
            "OSS ContribFinder",
            "LibCheck Security",
            "FOSS Tracker"],
        'Blockchain': [
            "SmartEscrow Ledger",
            "NFT Certificate Hub",
            "DAO Voting Mesh",
            "CryptoSafe Vault"]}

    selected_theme = theme if theme in title_themes else 'Web Development'
    title = random.choice(title_themes[selected_theme])

    problem = (
        f"Hackathon teams struggle to validate and build MVP solutions in "
        f"{theme} domains because of high friction in coordination and a lack of integrated tools."
    )
    audience = "Developers, Hackathon judges, startup founders, and technical recruiters."
    features = [
        "Real-time dashboard",
        "AI-powered recommendations",
        "Collaborative space",
        "Automatic code generation templates"]
    tech_stack = f"Python, Flask, Bootstrap 5, SQLite, Chart.js, {theme} API"
    roadmap = [
        "Phase 1: Initialize Git and setup schema",
        "Phase 2: Build responsive front-end layouts & dashboard widgets",
        "Phase 3: Connect intelligence APIs & real-time sockets",
        "Phase 4: Run end-to-end security compliance & pitch demo"
    ]
    monetization = (
        "Freemium model with premium developer templates, custom "
        "analytics packages for companies, and referral fees."
    )
    pitch = (
        f"Devs! The future of hackathons is here. {title} solves the core "
        f"friction points by introducing AI matching with immediate sandbox workspace setups."
    )
    script = (
        f"[Presenter]: Hi judges! We are presenting {title}. First, the user "
        f"creates an account, then invites members. We click generate, and boom "
        f"- immediate MVP workspace config. Thank you!"
    )
    success_score = random.randint(75, 95)

    inspired_by = ", ".join([r['title']
                            for r in retrieved]) if retrieved else None

    return {
        "title": title,
        "problem_statement": problem,
        "target_audience": audience,
        "features": ", ".join(features),
        "tech_stack": tech_stack,
        "mvp_roadmap": "\n".join(roadmap),
        "monetization": monetization,
        "pitch_summary": pitch,
        "demo_script": script,
        "success_score": success_score,
        "inspired_by": inspired_by
    }


def generate_project_idea_ai(skills, theme, difficulty):
    """
    Generates a hackathon project idea using a RAG pipeline:
    1. Retrieve similar past winning projects (TF-IDF over knowledge_base.py)
    2. Inject them as grounding context into the Gemini prompt
    3. Fall back to an offline mock generator if no API key or on failure
    """
    retrieved = retrieve_similar_projects(skills, theme, top_k=3)
    rag_context = build_rag_context_block(retrieved)
    inspired_by = ", ".join([r['title']
                            for r in retrieved]) if retrieved else None

    if not GEMINI_API_KEY:
        return generate_project_idea_mock(
            skills, theme, difficulty, retrieved=retrieved)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        You are an AI hackathon strategist. Generate a project idea grounded
        in patterns from real past winning hackathon projects.

        Team Skills: {skills}
        Hackathon Theme: {theme}
        Difficulty: {difficulty}

        Here are similar past WINNING hackathon projects, retrieved for context.
        Use these as inspiration for what tends to win, but propose something
        DIFFERENT and original — do not copy them directly:
        {rag_context}

        Provide the response in raw JSON format with the following keys.
        Return ONLY the JSON object, do not wrap in markdown tags or write conversational text:
        {{
            "title": "A catchy project name",
            "problem_statement": "The core problem this project solves",
            "target_audience": "Who this project is built for",
            "features": "Comma-separated list of 4 key MVP features",
            "tech_stack": "A relevant tech stack list",
            "mvp_roadmap": "A newline-separated 4-phase implementation roadmap",
            "monetization": "How to monetize or sustain this project",
            "pitch_summary": "A 3-sentence powerful elevator pitch",
            "demo_script": "A short, engaging 30-second presentation script for the live demo",
            "success_score": 85,
            "differentiation": "1-2 sentences on how this idea differs from / improves on the retrieved past winners"
        }}
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text.strip())
        data["inspired_by"] = inspired_by
        return data
    except Exception as e:
        print(f"Gemini API failure: {e}. Using offline generator.")
        return generate_project_idea_mock(
            skills, theme, difficulty, retrieved=retrieved)

# ----------------- ROUTING LOGIC -----------------


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')

        user = User.query.filter(
            (User.email == email_or_username) | (
                User.username == email_or_username)).first()
        if user and user.check_password(password):
            login_user(user)
            # Log rating activity
            db.session.add(Rating(user_id=user.id, activity_score=10))
            db.session.commit()
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            email=email,
            full_name=request.form.get('full_name', username),
            college=request.form.get('college', ''),
            degree=request.form.get('degree', ''),
            grad_year=int(request.form.get('grad_year', 2026) or 2026),
            city=request.form.get('city', ''),
            country=request.form.get('country', ''),
            experience_level=request.form.get('experience_level', 'Beginner'),
            availability=request.form.get('availability', 'Weekends'),
            hackathons_attended=int(request.form.get('hackathons_attended', 0) or 0),
            hackathons_won=int(request.form.get('hackathons_won', 0) or 0),
            bio=request.form.get('bio', ''),
            skills=request.form.get('skills', ''),
            github_url=request.form.get('github_url', ''),
            linkedin_url=request.form.get('linkedin_url', ''),
            portfolio_url=request.form.get('portfolio_url', ''),
            profile_image=f"https://ui-avatars.com/api/?name={username}&background=6366f1&color=fff&size=128"
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        flash(
            f"If the email {email} exists in our database, a password reset link has been sent.",
            "info")
        return redirect(url_for('login'))
    return render_template('login.html', forgot=True)


@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch suggestions
    potential_users = User.query.filter(User.id != current_user.id).all()
    suggestions = []

    # Calculate scores on the fly for suggestions
    for u in potential_users:
        # Check if already swiped
        match_exists = Match.query.filter(
            ((Match.user_one_id == current_user.id) & (
                Match.user_two_id == u.id)) | (
                (Match.user_one_id == u.id) & (
                    Match.user_two_id == current_user.id))).first()
        if not match_exists:
            score = calculate_compatibility(current_user, u)
            suggestions.append({'user': u, 'score': score})

    suggestions = sorted(
        suggestions,
        key=lambda x: x['score'],
        reverse=True)[
        :4]

    # Active Matches Count
    active_matches = Match.query.filter(
        ((Match.user_one_id == current_user.id) | (
            Match.user_two_id == current_user.id)) & (
            Match.status == 'connected')).all()

    # Team
    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    # Seeded Hackathons
    hackathons = Hackathon.query.limit(3).all()

    # Notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).order_by(
        Notification.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        suggestions=suggestions,
        active_matches_count=len(active_matches),
        team=team,
        hackathons=hackathons,
        notifications=notifications
    )


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.college = request.form.get('college')
        current_user.degree = request.form.get('degree')
        current_user.grad_year = int(
            request.form.get(
                'grad_year', 2026) or 2026)
        current_user.city = request.form.get('city')
        current_user.country = request.form.get('country')
        current_user.experience_level = request.form.get('experience_level')
        current_user.availability = request.form.get('availability')
        current_user.hackathons_attended = int(
            request.form.get('hackathons_attended', 0) or 0)
        current_user.hackathons_won = int(
            request.form.get('hackathons_won', 0) or 0)
        current_user.bio = request.form.get('bio')

        # Read checkbox skills
        selected_skills = request.form.getlist('skills_list')
        current_user.skills = ",".join(selected_skills)

        current_user.github_url = request.form.get('github_url')
        current_user.linkedin_url = request.form.get('linkedin_url')
        current_user.portfolio_url = request.form.get('portfolio_url')

        # Avatar selection (DiceBear style)
        avatar_style = request.form.get('avatar_style')
        if avatar_style:
            current_user.profile_image = f"https://api.dicebear.com/7.x/{avatar_style}/svg?seed={
                current_user.username}"

        # Increment rating activity
        db.session.add(Rating(user_id=current_user.id, activity_score=15))
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')


@app.route('/profile/github', methods=['POST'])
@login_required
def github_analyzer():
    """Mock-real GitHub profile data fetcher.

    Falls back to mock UI data if API is rate limited or user doesn't have github URL.
    """
    username = request.form.get('github_username', '').strip()
    if not username:
        if current_user.github_url:
            username = current_user.github_url.split('/')[-1]

    if not username:
        return jsonify({'error': 'Please provide a GitHub username.'}), 400

    try:
        # Try fetching real public repository metadata from GitHub API
        url = f"https://api.github.com/users/{username}/repos"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            repos_data = res.json()
            repos = []
            languages = {}
            # Mock contributions as GitHub API doesn't expose it simply without
            # graphQL
            total_contributions = random.randint(100, 500)

            for repo in repos_data[:5]:
                repos.append({
                    'name': repo.get('name'),
                    'stars': repo.get('stargazers_count'),
                    'language': repo.get('language'),
                    'url': repo.get('html_url')
                })
                lang = repo.get('language')
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1

            return jsonify({
                'username': username,
                'repos': repos,
                'languages': languages,
                'contributions': total_contributions,
                'avatar': f"https://github.com/{username}.png"
            })
    except Exception as e:
        print(f"GitHub API error: {e}. Falling back to mock details.")

    # Standard high-quality mock data for demo consistency
    languages = {'Python': 4, 'JavaScript': 3, 'HTML': 2, 'TypeScript': 1}
    repos = [
        {'name': 'smart-hack-analyzer', 'stars': 12, 'language': 'Python', 'url': '#'},
        {'name': 'portfolio-website', 'stars': 8, 'language': 'HTML', 'url': '#'},
        {'name': 'ai-chat-interface', 'stars': 24, 'language': 'TypeScript', 'url': '#'},
    ]
    return jsonify({
        'username': username,
        'repos': repos,
        'languages': languages,
        'contributions': 312,
        'avatar': f"https://ui-avatars.com/api/?name={username}&background=6366f1"
    })


@app.route('/matches')
@login_required
def matches():
    return render_template('matches.html')


@app.route('/api/matches/potential')
@login_required
def potential_matches():
    potential_users = User.query.filter(User.id != current_user.id).all()
    results = []

    for u in potential_users:
        # Check if already swiped by current user
        swipe_exists = Match.query.filter(
            (Match.user_one_id == current_user.id) &
            (Match.user_two_id == u.id)
        ).first()

        if not swipe_exists:
            score = calculate_compatibility(current_user, u)
            results.append({
                'id': u.id,
                'full_name': u.full_name or u.username,
                'college': u.college or 'DeVry University',
                'degree': u.degree or 'CS',
                'skills': u.get_skills_list(),
                'experience': u.experience_level,
                'match_score': score,
                'bio': u.bio or 'Looking for high-energy teams to build disruptive software.',
                'image': u.profile_image or f"https://ui-avatars.com/api/?name={u.username}"
            })

    # Sort by score desc
    results = sorted(results, key=lambda x: x['match_score'], reverse=True)
    return jsonify(results)


@app.route('/api/matches/swipe', methods=['POST'])
@login_required
def swipe():
    target_user_id = int(request.json.get('user_id'))
    action = request.json.get('action')  # connect, pass, super_liked

    if action not in ['connect', 'pass', 'super_liked']:
        return jsonify({'error': 'Invalid swipe action'}), 400

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Check compatibility score
    score = calculate_compatibility(current_user, target_user)

    # Store current user's swipe
    new_match = Match(
        user_one_id=current_user.id,
        user_two_id=target_user_id,
        status='pending' if action != 'pass' else 'passed',
        action_by_id=current_user.id,
        match_score=score
    )
    db.session.add(new_match)

    is_match = False

    # Check if target user has already swiped positively on current user
    opposite_swipe = Match.query.filter(
        (Match.user_one_id == target_user_id) &
        (Match.user_two_id == current_user.id) &
        (Match.status.in_(['pending', 'connected']))
    ).first()

    if action != 'pass' and opposite_swipe:
        # It's a Match!
        is_match = True
        new_match.status = 'connected'
        opposite_swipe.status = 'connected'

        # Add notifications for both
        n1 = Notification(
            user_id=current_user.id,
            title="It's a Match! 🎉",
            message=f"You connected with {
                target_user.full_name or target_user.username} ({score}% match)!",
            type='match',
            link=url_for(
                'chat_user',
                chat_user_id=target_user_id))
        n2 = Notification(
            user_id=target_user_id,
            title="It's a Match! 🎉",
            message=f"You connected with {
                current_user.full_name or current_user.username} ({score}% match)!",
            type='match',
            link=url_for(
                'chat_user',
                chat_user_id=current_user.id))
        db.session.add(n1)
        db.session.add(n2)

    db.session.add(Rating(user_id=current_user.id, activity_score=5))
    db.session.commit()

    return jsonify({
        'success': True,
        'is_match': is_match,
        'match_score': score
    })

# ----------------- TEAMS SYSTEM -----------------


@app.route('/team')
@login_required
def team():
    # Find current user's active team
    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    # Find active invitations
    invites = TeamMember.query.filter_by(
        user_id=current_user.id, status='invited').all()

    # List users to invite
    potential_invites = User.query.filter(User.id != current_user.id).all()

    # If in team, show team health metrics
    health_metrics = None
    health_suggestions = []

    if team:
        # Core skill categories evaluation
        roles_strength = {
            'frontend': 0,
            'backend': 0,
            'design': 0,
            'ai': 0,
            'security': 0}

        frontend_skills = {'HTML', 'CSS', 'JavaScript', 'React', 'UI UX'}
        backend_skills = {'Node', 'Python', 'Flask', 'Django', 'DevOps'}
        ai_skills = {'AI', 'Machine Learning'}
        security_skills = {'Cybersecurity'}

        for m in team.members:
            if m.status != 'active':
                continue
            user_skills = set(m.user.get_skills_list())

            # Rate strength based on skill presence
            for s in user_skills:
                if s in frontend_skills:
                    roles_strength['frontend'] += 20
                if s in backend_skills:
                    roles_strength['backend'] += 20
                if s in ai_skills:
                    roles_strength['ai'] += 30
                if s in security_skills:
                    roles_strength['security'] += 40

        # Caps strengths at 100
        for k in roles_strength:
            roles_strength[k] = min(
                roles_strength[k] + 20,
                100) if roles_strength[k] > 0 else 10  # small default baseline if empty

        overall_health = round(sum(roles_strength.values()) / 5.0)
        health_metrics = roles_strength
        health_metrics['overall'] = overall_health

        # Build health recommendations
        if roles_strength['frontend'] < 50:
            health_suggestions.append(
                "Add a Frontend developer or UI/UX Designer to enhance visual aesthetic.")
        if roles_strength['backend'] < 50:
            health_suggestions.append(
                "Incorporate Python/Flask backend expertise to handle databases securely.")
        if roles_strength['design'] < 40:
            health_suggestions.append(
                "Team lacks UI/UX design strength. Suggest recruiting a Figma designer.")
        if roles_strength['ai'] < 30:
            health_suggestions.append(
                "AI and ML capabilities are low. Add a member skilled in NLP or Gemini API integrations.")
        if roles_strength['security'] < 30:
            health_suggestions.append(
                "Ensure your app is secure. Recruit a Cybersecurity specialist.")

        if len(health_suggestions) == 0:
            health_suggestions.append(
                "Excellent team balance! You are fully equipped to win the hackathon.")

    return render_template(
        'team.html',
        team=team,
        invites=invites,
        potential_invites=potential_invites,
        health_metrics=health_metrics,
        health_suggestions=health_suggestions
    )


@app.route('/team/create', methods=['POST'])
@login_required
def create_team():
    name = request.form.get('team_name')
    desc = request.form.get('team_description')

    if not name:
        flash('Team name is required', 'danger')
        return redirect(url_for('team'))

    # Check if team name already exists
    if Team.query.filter_by(name=name).first():
        flash('Team name already taken', 'danger')
        return redirect(url_for('team'))

    # Leave current team if any
    old_membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    if old_membership:
        db.session.delete(old_membership)

    # Create new team
    new_team = Team(name=name, description=desc, creator_id=current_user.id)
    db.session.add(new_team)
    db.session.flush()  # gets new_team.id

    # Add creator as Lead Backend or default Lead role
    member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role='Team Lead / Full Stack',
        status='active'
    )
    db.session.add(member)
    db.session.add(Rating(user_id=current_user.id, activity_score=20))
    db.session.commit()

    flash(f"Team '{name}' created successfully!", 'success')
    return redirect(url_for('team'))


@app.route('/team/invite', methods=['POST'])
@login_required
def invite_member():
    target_user_id = int(request.form.get('user_id'))
    role = request.form.get('role', 'Developer')

    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    if not membership:
        flash('You must have a team to invite members.', 'danger')
        return redirect(url_for('team'))

    team = membership.team

    # Check if target is already in the team
    already_member = TeamMember.query.filter_by(
        team_id=team.id, user_id=target_user_id).first()
    if already_member:
        flash('User is already invited or a member of this team.', 'warning')
        return redirect(url_for('team'))

    # Invite member
    invite = TeamMember(
        team_id=team.id,
        user_id=target_user_id,
        role=role,
        status='invited'
    )
    db.session.add(invite)

    # Notify target user
    notif = Notification(
        user_id=target_user_id,
        title="Team Invitation 🚀",
        message=f"You have been invited to join team '{
            team.name}' as a {role}!",
        type='invite',
        link=url_for('team'))
    db.session.add(notif)
    db.session.commit()

    flash('Invitation sent successfully!', 'success')
    return redirect(url_for('team'))


@app.route('/team/respond-invite/<int:invite_id>/<action>')
@login_required
def respond_invite(invite_id, action):
    invite = TeamMember.query.get_or_404(invite_id)
    if invite.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('team'))

    if action == 'accept':
        # Leave current team if any
        old_membership = TeamMember.query.filter_by(
            user_id=current_user.id, status='active').first()
        if old_membership:
            db.session.delete(old_membership)

        invite.status = 'active'
        invite.joined_at = datetime.utcnow()

        # Notify team owner
        n = Notification(
            user_id=invite.team.creator_id,
            title="Member Joined! 👥",
            message=f"{
                current_user.full_name or current_user.username} accepted your invitation to join '{
                invite.team.name}'!",
            type='invite',
            link=url_for('team'))
        db.session.add(n)
        db.session.add(Rating(user_id=current_user.id, activity_score=15))
        db.session.commit()
        flash(f"Joined team '{invite.team.name}'!", 'success')
    else:
        db.session.delete(invite)
        db.session.commit()
        flash('Invitation declined.', 'info')

    return redirect(url_for('team'))


@app.route('/team/remove/<int:member_id>', methods=['POST'])
@login_required
def remove_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    team = member.team

    # Only creator can remove members, and cannot remove themselves
    if team.creator_id != current_user.id:
        flash('Only the Team Creator can remove members.', 'danger')
        return redirect(url_for('team'))

    if member.user_id == current_user.id:
        flash('You cannot remove yourself. Delete the team instead.', 'warning')
        return redirect(url_for('team'))

    db.session.delete(member)

    # Notify removed user
    n = Notification(
        user_id=member.user_id,
        title="Removed from Team ⚠️",
        message=f"You have been removed from team '{team.name}'.",
        type='invite',
        link=url_for('team')
    )
    db.session.add(n)
    db.session.commit()

    flash("Removed member from team.", 'success')
    return redirect(url_for('team'))


@app.route('/team/one-click-generator', methods=['POST'])
@login_required
def one_click_team_generator():
    """Automatically forms a balanced team based on skill sets."""
    # Find all available single users (not in any active team)
    in_teams = db.session.query(
        TeamMember.user_id).filter_by(
        status='active').subquery()
    available_users = User.query.filter(
        User.id != current_user.id).filter(
        ~User.id.in_(in_teams)).all()

    if not available_users:
        flash(
            "No available single users at the moment to construct a team.",
            "warning")
        return redirect(url_for('team'))

    # Filter candidates based on complementarity
    # Current user needs roles. Let's find:
    # 1. UI UX Designer
    # 2. Python Backend Dev
    # 3. AI Engineer

    # Categorize candidates
    team_candidates = []

    for user in available_users:
        score = calculate_compatibility(current_user, user)
        team_candidates.append({'user': user, 'score': score})

    # Sort candidates by complementarity score
    team_candidates = sorted(
        team_candidates,
        key=lambda x: x['score'],
        reverse=True)

    # Create the team
    team_name = f"Autobuild Team {random.randint(100, 999)}"
    new_team = Team(
        name=team_name,
        description="AI-generated balanced hackathon team.",
        creator_id=current_user.id)
    db.session.add(new_team)
    db.session.flush()

    # Join creator
    db.session.add(
        TeamMember(
            team_id=new_team.id,
            user_id=current_user.id,
            role='Team Lead (Fullstack)',
            status='active'))

    # Add top 2 complementary users
    added = 0
    roles = ['Backend Architect', 'UI/UX Lead', 'AI Integration Lead']
    for candidate in team_candidates[:2]:
        user = candidate['user']
        role = roles[added] if added < len(roles) else 'Developer'

        # Add to team
        member = TeamMember(
            team_id=new_team.id,
            user_id=user.id,
            role=role,
            status='active')
        db.session.add(member)

        # Notify
        n = Notification(
            user_id=user.id,
            title="Auto-matched into Team! 🤖",
            message=f"You have been auto-matched into team '{team_name}' as {role} due to complementary skills!",
            type='invite',
            link=url_for('team'))
        db.session.add(n)
        added += 1

    db.session.commit()
    flash(
        f"Auto-generated team '{team_name}' successfully with {
            added +
            1} balanced members!",
        'success')
    return redirect(url_for('team'))

# ----------------- AI PROJECT GENERATOR -----------------


@app.route('/project-generator')
@login_required
def project_generator():
    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    # Retrieve existing projects generated for this team/user
    saved_projects = []
    if team:
        saved_projects = Project.query.filter_by(
            team_id=team.id).order_by(
            Project.created_at.desc()).all()
    else:
        saved_projects = Project.query.filter_by(
            creator_id=current_user.id).order_by(
            Project.created_at.desc()).all()

    return render_template(
        'project_generator.html',
        team=team,
        saved_projects=saved_projects)


@app.route('/project-generator/generate', methods=['POST'])
@login_required
def generate_project():
    theme = request.form.get('theme', 'AI')
    difficulty = request.form.get('difficulty', 'Intermediate')

    # Fetch team skills
    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    skills_list = []
    if team:
        for m in team.members:
            if m.status == 'active':
                skills_list.extend(m.user.get_skills_list())
    else:
        skills_list = current_user.get_skills_list()

    skills_str = ", ".join(list(set(skills_list))) or "HTML, CSS, JavaScript"

    # Generate content via Gemini or Mock
    ai_data = generate_project_idea_ai(skills_str, theme, difficulty)

    # Create Project model instance
    project = Project(
        team_id=team.id if team else None,
        creator_id=current_user.id,
        title=ai_data.get('title'),
        theme=theme,
        difficulty=difficulty,
        problem_statement=ai_data.get('problem_statement'),
        target_audience=ai_data.get('target_audience'),
        features=ai_data.get('features'),
        tech_stack=ai_data.get('tech_stack'),
        mvp_roadmap=ai_data.get('mvp_roadmap'),
        monetization=ai_data.get('monetization'),
        pitch_summary=ai_data.get('pitch_summary'),
        demo_script=ai_data.get('demo_script'),
        success_score=ai_data.get('success_score', 80),
        inspired_by=ai_data.get('inspired_by'),
        differentiation=ai_data.get('differentiation')
    )

    db.session.add(project)
    # Add activity score
    db.session.add(Rating(user_id=current_user.id, activity_score=25))
    db.session.commit()

    flash(
        f"Generated new AI Project recommendation: '{
            project.title}'!",
        'success')
    return redirect(url_for('project_generator'))

# ----------------- CHAT SYSTEM -----------------


@app.route('/chat')
@login_required
def chat():
    # Find all users currently matched (connected)
    matches_one = Match.query.filter_by(
        user_one_id=current_user.id,
        status='connected').all()
    matches_two = Match.query.filter_by(
        user_two_id=current_user.id,
        status='connected').all()

    chat_users = []
    for m in matches_one:
        user = User.query.get(m.user_two_id)
        if user:
            chat_users.append(user)
    for m in matches_two:
        user = User.query.get(m.user_one_id)
        if user:
            chat_users.append(user)

    # Active team for team chats
    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    return render_template(
        'chat.html',
        chat_users=chat_users,
        active_chat_user=None,
        team=team)


@app.route('/chat/<int:chat_user_id>')
@login_required
def chat_user(chat_user_id):
    # Same as /chat, but sets specific active user
    matches_one = Match.query.filter_by(
        user_one_id=current_user.id,
        status='connected').all()
    matches_two = Match.query.filter_by(
        user_two_id=current_user.id,
        status='connected').all()

    chat_users = []
    for m in matches_one:
        user = User.query.get(m.user_two_id)
        if user:
            chat_users.append(user)
    for m in matches_two:
        user = User.query.get(m.user_one_id)
        if user:
            chat_users.append(user)

    active_chat_user = User.query.get_or_404(chat_user_id)

    # Mark messages as read
    Message.query.filter_by(sender_id=chat_user_id,
                            receiver_id=current_user.id,
                            is_read=False).update({Message.is_read: True})
    db.session.commit()

    membership = TeamMember.query.filter_by(
        user_id=current_user.id, status='active').first()
    team = membership.team if membership else None

    return render_template(
        'chat.html',
        chat_users=chat_users,
        active_chat_user=active_chat_user,
        team=team,
        is_team_chat=False)


@app.route('/chat/team/<int:team_id>')
@login_required
def chat_team(team_id):
    # Verify user is in this team
    member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=current_user.id,
        status='active').first_or_404()

    matches_one = Match.query.filter_by(
        user_one_id=current_user.id,
        status='connected').all()
    matches_two = Match.query.filter_by(
        user_two_id=current_user.id,
        status='connected').all()

    chat_users = []
    for m in matches_one:
        user = User.query.get(m.user_two_id)
        if user:
            chat_users.append(user)
    for m in matches_two:
        user = User.query.get(m.user_one_id)
        if user:
            chat_users.append(user)

    return render_template(
        'chat.html',
        chat_users=chat_users,
        active_chat_user=None,
        team=member.team,
        is_team_chat=True)


@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    content = request.json.get('content')
    receiver_id = request.json.get('receiver_id')
    team_id = request.json.get('team_id')

    if not content:
        return jsonify({'error': 'Message content is empty'}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=int(receiver_id) if receiver_id else None,
        team_id=int(team_id) if team_id else None,
        content=content
    )
    db.session.add(msg)

    # Increment rating activity
    db.session.add(Rating(user_id=current_user.id, activity_score=2))
    db.session.commit()

    # Send live notification to receiver if DMs
    if receiver_id:
        # Create non-duplicate notification for chat message
        n_exists = Notification.query.filter_by(
            user_id=receiver_id, type='chat', is_read=False).first()
        if not n_exists:
            n = Notification(
                user_id=receiver_id,
                title=f"New Message from {current_user.full_name or current_user.username}",
                message=f"\"{content[:30]}...\"",
                type='chat',
                link=url_for('chat_user', chat_user_id=current_user.id)
            )
            db.session.add(n)
            db.session.commit()

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': current_user.full_name or current_user.username,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%H:%M')
        }
    })


@app.route('/api/chat/messages')
@login_required
def get_messages():
    receiver_id = request.args.get('receiver_id')
    team_id = request.args.get('team_id')
    last_id = int(request.args.get('last_id', 0))

    query = Message.query

    if team_id:
        query = query.filter_by(team_id=int(team_id))
    elif receiver_id:
        query = query.filter(
            ((Message.sender_id == current_user.id) & (
                Message.receiver_id == int(receiver_id))) | (
                (Message.sender_id == int(receiver_id)) & (
                    Message.receiver_id == current_user.id)))
    else:
        return jsonify([])

    messages = query.filter(
        Message.id > last_id).order_by(
        Message.created_at.asc()).all()

    # Mark incoming read
    if receiver_id:
        Message.query.filter_by(sender_id=int(receiver_id),
                                receiver_id=current_user.id,
                                is_read=False).update({Message.is_read: True})
        db.session.commit()

    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.full_name or m.sender.username,
        'content': m.content,
        'created_at': m.created_at.strftime('%H:%M')
    } for m in messages])

# ----------------- LEADERBOARD & HACKATHONS -----------------


@app.route('/leaderboard')
@login_required
def leaderboard():
    # User Leaderboard based on aggregate Activity Ratings
    users_ranking = db.session.query(
        User,
        db.func.sum(
            Rating.activity_score).label('total_activity')).join(
        Rating,
        User.id == Rating.user_id).group_by(
                User.id).order_by(
                    db.desc('total_activity')).limit(10).all()

    # Map back structure
    ranked_users = []
    for rank, (u, score) in enumerate(users_ranking, 1):
        ranked_users.append({
            'rank': rank,
            'user': u,
            'score': score or 0,
            'badge': u.get_badge()
        })

    # Best Teams based on overall Team Health Score
    teams = Team.query.all()
    ranked_teams = []

    frontend_skills = {'HTML', 'CSS', 'JavaScript', 'React', 'UI UX'}
    backend_skills = {'Node', 'Python', 'Flask', 'Django', 'DevOps'}
    ai_skills = {'AI', 'Machine Learning'}
    security_skills = {'Cybersecurity'}

    for t in teams:
        strengths = {
            'frontend': 0,
            'backend': 0,
            'design': 0,
            'ai': 0,
            'security': 0}
        for m in t.members:
            if m.status == 'active':
                user_skills = set(m.user.get_skills_list())
                for s in user_skills:
                    if s in frontend_skills:
                        strengths['frontend'] += 20
                    if s in backend_skills:
                        strengths['backend'] += 20
                    if s in ai_skills:
                        strengths['ai'] += 30
                    if s in security_skills:
                        strengths['security'] += 40
        for k in strengths:
            strengths[k] = min(
                strengths[k] + 20,
                100) if strengths[k] > 0 else 10
        overall = round(sum(strengths.values()) / 5.0)
        ranked_teams.append({
            'team': t,
            'score': overall
        })

    ranked_teams = sorted(
        ranked_teams,
        key=lambda x: x['score'],
        reverse=True)[
        :5]

    return render_template(
        'leaderboard.html',
        ranked_users=ranked_users,
        ranked_teams=ranked_teams)


@app.route('/hackathons')
@login_required
def hackathons():
    cat_filter = request.args.get('category')
    if cat_filter:
        hacks = Hackathon.query.filter_by(category=cat_filter).all()
    else:
        hacks = Hackathon.query.all()

    return render_template(
        'dashboard.html',
        hack_discover_only=True,
        hacks=hacks,
        active_filter=cat_filter)

# ----------------- ADMIN PANEL -----------------


@app.route('/admin')
@login_required
def admin_panel():
    # Analytics
    total_users = User.query.count()
    total_matches = Match.query.count()
    total_teams = Team.query.count()
    total_messages = Message.query.count()

    all_users = User.query.all()
    all_teams = Team.query.all()

    return render_template(
        'dashboard.html',
        admin_panel_only=True,
        total_users=total_users,
        total_matches=total_matches,
        total_teams=total_teams,
        total_messages=total_messages,
        all_users=all_users,
        all_teams=all_teams
    )

# ----------------- NOTIFICATIONS API -----------------


@app.route('/api/notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id).order_by(
        Notification.created_at.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d %b, %H:%M')
        } for n in notifs]
    })


@app.route('/api/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def read_notification(notif_id):
    notif = Notification.query.filter_by(
        id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({'success': True})

# ----------------- DATABASE SEEDING FUNCTION -----------------


def migrate_new_columns():
    """Adds new columns to existing SQLite tables if they don't exist yet."""
    from sqlalchemy import text
    with db.engine.connect() as conn:
        existing_cols = [
            row[1] for row in conn.execute(
                text("PRAGMA table_info(projects)"))]
        if 'inspired_by' not in existing_cols:
            conn.execute(
                text("ALTER TABLE projects ADD COLUMN inspired_by TEXT"))
        if 'differentiation' not in existing_cols:
            conn.execute(
                text("ALTER TABLE projects ADD COLUMN differentiation TEXT"))
        conn.commit()


def seed_database():
    """Seeds the SQLite database on launch if empty."""
    db.create_all()
    migrate_new_columns()
    if User.query.first():
        return  # Database is already populated

    print("Database empty. Starting Seeding...")

    # 1. Dummy Users
    users_data = [{'username': 'priya_ai',
                   'email': 'priya@example.com',
                   'full_name': 'Priya Sharma',
                   'college': 'IIT Delhi',
                   'degree': 'B.Tech Computer Science',
                   'grad_year': 2027,
                   'city': 'New Delhi',
                   'country': 'India',
                   'skills': 'AI,Machine Learning,Python,HTML,CSS',
                   'experience_level': 'Advanced',
                   'availability': 'Full Time',
                   'hackathons_attended': 8,
                   'hackathons_won': 4,
                   'bio': ('PhD AI student interested in LLMs, Prompt Engineering, '
                           'and Natural Language Processing. Looking for frontend experts to team up with!'),
                   'profile_image': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop',
                   'github': 'priya-ai',
                   'linkedin': 'in/priyasharma'},
                  {'username': 'alex_dev',
                   'email': 'alex@example.com',
                   'full_name': 'Alex Johnson',
                   'college': 'Stanford University',
                   'degree': 'BS Computer Science',
                   'grad_year': 2026,
                   'city': 'San Francisco',
                   'country': 'USA',
                   'skills': 'JavaScript,React,HTML,CSS,UI UX',
                   'experience_level': 'Advanced',
                   'availability': 'Weekends',
                   'hackathons_attended': 6,
                   'hackathons_won': 2,
                   'bio': ('React Native and Tailwind absolute wizard. '
                           'I construct interactive animations and stunning dashboard aesthetics.'),
                   'profile_image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop',
                   'github': 'alex-johnson-dev',
                   'linkedin': 'in/alexjohnson'},
                  {'username': 'kabir_sec',
                   'email': 'kabir@example.com',
                   'full_name': 'Kabir Mehta',
                   'college': 'BITS Pilani',
                   'degree': 'B.E. Computer Science',
                   'grad_year': 2026,
                   'city': 'Bangalore',
                   'country': 'India',
                   'skills': 'Cybersecurity,Python,Flask,DevOps',
                   'experience_level': 'Advanced',
                   'availability': 'Weekdays',
                   'hackathons_attended': 12,
                   'hackathons_won': 5,
                   'bio': ('Vulnerability analyst and penetration tester. '
                           'Love securing REST APIs and working on Blockchain networks.'),
                   'profile_image': 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150&h=150&fit=crop',
                   'github': 'kabirsecur',
                   'linkedin': 'in/kabirmehta'},
                  {'username': 'sarah_uiux',
                   'email': 'sarah@example.com',
                   'full_name': 'Sarah Al-Farsi',
                   'college': 'MIT',
                   'degree': 'MS Design',
                   'grad_year': 2026,
                   'city': 'Boston',
                   'country': 'USA',
                   'skills': 'UI UX,HTML,CSS,JavaScript',
                   'experience_level': 'Intermediate',
                   'availability': 'Weekends',
                   'hackathons_attended': 3,
                   'hackathons_won': 1,
                   'bio': ('Passionate designer. I create detailed Figma prototype boards, '
                           'wireframes, and design systems for web apps.'),
                   'profile_image': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop',
                   'github': 'sarahdesign',
                   'linkedin': 'in/sarahdesign'},
                  {'username': 'rohit_backend',
                   'email': 'rohit@example.com',
                   'full_name': 'Rohit Sen',
                   'college': 'Vellore Institute of Technology',
                   'degree': 'B.Tech Information Technology',
                   'grad_year': 2025,
                   'city': 'Chennai',
                   'country': 'India',
                   'skills': 'Python,Flask,Django,Node,DevOps',
                   'experience_level': 'Intermediate',
                   'availability': 'Weekdays',
                   'hackathons_attended': 4,
                   'hackathons_won': 0,
                   'bio': ('Backend builder. I design secure endpoints, '
                           'write fast SQL queries, and manage Docker pipelines.'),
                   'profile_image': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop',
                   'github': 'rohitsendev',
                   'linkedin': 'in/rohitsen'}]

    users_created = []
    for u in users_data:
        usr = User(
            username=u['username'],
            email=u['email'],
            full_name=u['full_name'],
            college=u['college'],
            degree=u['degree'],
            grad_year=u['grad_year'],
            city=u['city'],
            country=u['country'],
            skills=u['skills'],
            experience_level=u['experience_level'],
            availability=u['availability'],
            hackathons_attended=u['hackathons_attended'],
            hackathons_won=u['hackathons_won'],
            bio=u['bio'],
            profile_image=u['profile_image'],
            github_url=f"https://github.com/{u['github']}",
            linkedin_url=f"https://linkedin.com/{u['linkedin']}",
            portfolio_url='https://portfolio.example.com'
        )
        usr.set_password('password123')
        db.session.add(usr)
        users_created.append(usr)

    db.session.flush()  # assign user IDs

    # 2. Seed Hackathons
    hacks_data = [
        {
            'name': 'Google Gemini AI Hackathon',
            'start_date': 'July 15 - 17, 2026',
            'prize_pool': '$50,000',
            'category': 'AI',
            'location': 'Online',
            'link': 'https://devpost.com',
            'logo': 'fa-brain'
        },
        {
            'name': 'Global Cyber Shield Hack',
            'start_date': 'August 02 - 05, 2026',
            'prize_pool': '$25,000',
            'category': 'Cybersecurity',
            'location': 'Washington D.C. (Hybrid)',
            'link': 'https://devpost.com',
            'logo': 'fa-shield-halved'
        },
        {
            'name': 'OpenSource Summit Ignite',
            'start_date': 'September 10 - 12, 2026',
            'prize_pool': '$10,000',
            'category': 'Open Source',
            'location': 'Berlin, Germany',
            'link': 'https://devpost.com',
            'logo': 'fa-code-branch'
        },
        {
            'name': 'Solana Blockchain Masters',
            'start_date': 'October 24 - 28, 2026',
            'prize_pool': '$100,000',
            'category': 'Blockchain',
            'location': 'Lisbon, Portugal',
            'link': 'https://devpost.com',
            'logo': 'fa-coins'
        },
        {
            'name': 'Vite+Flask Web Dev Clash',
            'start_date': 'November 18 - 20, 2026',
            'prize_pool': '$15,000',
            'category': 'Web Development',
            'location': 'Online',
            'link': 'https://devpost.com',
            'logo': 'fa-laptop-code'
        }
    ]
    for h in hacks_data:
        db.session.add(Hackathon(
            name=h['name'], start_date=h['start_date'],
            prize_pool=h['prize_pool'], category=h['category'],
            location=h['location'], link=h['link'], logo=h['logo']
        ))

    # 3. Dummy Teams
    t1 = Team(
        name='Neural Ninjas',
        description='Building AI agents to map evolutionary conservation data.',
        creator_id=users_created[0].id)
    t2 = Team(
        name='ZeroTrust Crusaders',
        description='Implementing zero-trust architecture in educational APIs.',
        creator_id=users_created[2].id)
    db.session.add(t1)
    db.session.add(t2)
    db.session.flush()

    # 4. Team Members
    db.session.add(
        TeamMember(
            team_id=t1.id,
            user_id=users_created[0].id,
            role='AI Specialist',
            status='active'))
    db.session.add(
        TeamMember(
            team_id=t1.id,
            user_id=users_created[1].id,
            role='UI UX Designer',
            status='active'))

    db.session.add(
        TeamMember(
            team_id=t2.id,
            user_id=users_created[2].id,
            role='Security Lead',
            status='active'))
    db.session.add(
        TeamMember(
            team_id=t2.id,
            user_id=users_created[4].id,
            role='Backend Architect',
            status='active'))

    # 5. Activity Ratings (for Leaderboard)
    for u in users_created:
        db.session.add(
            Rating(
                user_id=u.id,
                activity_score=random.randint(
                    50,
                    200)))

    # 6. Matches
    # Priya and Kabir connect
    db.session.add(
        Match(
            user_one_id=users_created[0].id,
            user_two_id=users_created[2].id,
            status='connected',
            action_by_id=users_created[0].id,
            match_score=78))
    # Priya and Sarah connect
    db.session.add(
        Match(
            user_one_id=users_created[0].id,
            user_two_id=users_created[3].id,
            status='connected',
            action_by_id=users_created[3].id,
            match_score=85))

    # Priya messages Sarah
    db.session.add(
        Message(
            sender_id=users_created[3].id,
            receiver_id=users_created[0].id,
            content=("Hi Priya! I saw your post. I would love to design "
                     "the mock UI panels for your AI platform!")))
    db.session.add(
        Message(
            sender_id=users_created[0].id,
            receiver_id=users_created[3].id,
            content=("Awesome Sarah! I am looking exactly for design "
                     "profiles. Let's discuss on team tab.")))

    db.session.commit()
    print("Database seeding completed successfully!")


if __name__ == '__main__':
    with app.app_context():
        seed_database()
    app.run(debug=True)
