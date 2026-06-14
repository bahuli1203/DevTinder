# Dev Tinder 🚀
> "Find Your Perfect Hackathon Team"

Dev Tinder is a premium, AI-powered matchmaking and team-building SaaS platform designed specifically for hackathon participants. It simulates a LinkedIn-meets-Tinder experience allowing developers to discover teammates, verify public GitHub contributions, dynamically evaluate team competency radar charts, and generate hackathon pitch decks via Google Gemini API.

---

## Key Features

1. **Teammate Swipe Matchmaking**: Drag-and-swipe cards indicating compatibility index scores calculated based on skill similarity (30%), complementarity (25%), bio interest (20%), availability schedules (15%), and experience level (10%).
2. **GitHub Profile Analyzer**: Real-time integration pulling public repository metrics, dominant language counts, and contribution frequencies to authenticate skills.
3. **One-Click Balanced Team Generator**: Automatic matchmaking logic that evaluates all available single developers and pairs complementary skills (Frontend, Backend, AI, Design, Security) into a new active team.
4. **Competency Health Radar Charts**: Built on Chart.js, this radar widget analyzes the active team's strengths and exposes skill gaps with automated AI feedback (e.g. "Add a Figma designer").
5. **AI Project & Pitch Lab**: Prompts Google Gemini (with resilient local mock engines fallbacks) to produce problem statements, target audiences, MVPs, roadmaps, monetization frameworks, elevator pitches, and 30-second presentation scripts.
6. **Real-time DM & Team Chat**: Seamless poll-driven chat interface including typing indicators and interactive emoji pickers.
7. **Ranked Badge Leaderboard**: Community ranking board recognizing contributions with badges ("AI Wizard", "Design Pro", "Team Builder", "Hackathon Veteran").
8. **Admin Panel Analytics**: System dashboard reporting site-wide metrics (users, swipe logs, teams, and chat rates).

---

## File Structure

```
Dev Tinder/
│
├── static/
│   ├── css/
│   │   └── style.css            # Custom glassmorphic styling & swipe transitions
│   └── js/
│       └── main.js             # Drag gestures, AJAX chat polling, radar charts, GitHub fetching
│
├── templates/
│   ├── base.html               # Base layout containing CDN bindings & topbar
│   ├── index.html              # Visitors landing page
│   ├── login.html              # Sign In and Recovery forms
│   ├── register.html           # Multi-step account builder
│   ├── dashboard.html          # Core workspace, discovery list, and admin panels
│   ├── profile.html            # Profile configuration and GitHub widgets
│   ├── matches.html            # Tinder Swipe container card deck
│   ├── team.html               # Team health radar logs, invites, auto-match buttons
│   ├── project_generator.html  # AI Project generator and roadmaps panels
│   ├── chat.html               # DM/Team chats & emoji bars
│   └── leaderboard.html        # Badges ranking scoreboards
│
├── app.py                      # Flask Application Controller (Auth, APIs, Seeds)
├── models.py                   # SQLite Database Entity schemas (SQLAlchemy)
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation
```

---

## Installation & Deployment

Follow these quick commands to spin up the application on your local machine.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Gemini API (Optional)
If you'd like to use a live Gemini instance to generate project ideas, obtain your Gemini API key and set the environment variable:
- **Windows (Command Prompt)**:
  ```cmd
  set GEMINI_API_KEY=your_gemini_api_key_here
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:GEMINI_API_KEY="your_gemini_api_key_here"
  ```
*If not set, the app will run in offline mode using a robust local content generator, ensuring your demo never breaks!*

### 3. Run Dev Tinder
On launch, the database (`database.db`) is automatically initialized and seeded with 5 high-quality pre-populated developer profiles (AI Specialists, Designers, DevOps Engineers) complete with active matches, chat history, and hackathon events to make your demo immediate and fully interactive.

```bash
python app.py
```
Open **`http://127.0.0.1:5000`** on your browser.

---

## Demo Walkthrough Guide (Judges' 60-Second Hook)

To wow judges within the first minute of your presentation, follow this flow:
1. **Landing Page**: Start at the homepage, show the glassmorphic mesh hero panel and explain the tagline: *"Find Your Perfect Hackathon Team"*.
2. **Immediate Sign In**: Sign in with **`priya@example.com`** / password **`password123`**. This pulls a seeded account loaded with active stats.
3. **Swipe Deck**: Visit **Find Matches** and swipe right (Like) or left (Pass) on developers. Showing the dynamic Match Score badge (e.g. *88% Match*) calculated on the fly.
4. **Competency Radar**: Navigate to **My Team**. Show the animated Chart.js Radar chart indicating Team strengths and the AI role gap detector.
5. **AI Pitch Generator**: Go to the **AI Project Lab**. Generate a project. Instantly highlight the demo scripts and success forecasts generated by Gemini.
6. **Chat Console**: Go to **Messages** to showcase active matching chats with typing animations and emoji inputs.

