# ----------------- RAG KNOWLEDGE BASE -----------------
# A curated set of past winning hackathon project patterns used to ground
# the AI Project Lab's idea generation via lightweight retrieval (TF-IDF).
# This acts as the "retrieval corpus" in our RAG pipeline.

WINNING_PROJECTS = [
    {
        "title": "MedScribe AI",
        "theme": "AI",
        "skills": "Python, Machine Learning, NLP, Flask, React",
        "summary": "An AI scribe that listens to doctor-patient conversations and auto-generates structured clinical notes, cutting documentation time by 70%. Won Best AI Hack at MedHacks for its real-world impact and clean demo flow.",
        "why_it_won": "Solved a painful, recurring problem for a clearly defined audience (doctors) with a tight, working demo and a believable monetization story (SaaS per-clinic licensing)."
    },
    {
        "title": "EcoRoute",
        "theme": "AI",
        "skills": "Python, Machine Learning, Maps API, React",
        "summary": "A route optimizer that recalculates delivery routes in real time to minimize carbon emissions, using a small ML model trained on traffic + vehicle load data. Won Sustainability Track at Hack the North.",
        "why_it_won": "Combined a niche but timely theme (sustainability) with a quantifiable metric (CO2 saved per route) that judges could immediately grasp."
    },
    {
        "title": "CodeBuddy Live",
        "theme": "Web Development",
        "skills": "React, Node, Socket.io, Flask",
        "summary": "A real-time collaborative coding interview platform with built-in AI hints and automatic candidate scoring. Won Best Developer Tool at MLH Local Hack Day.",
        "why_it_won": "Polished UI with real-time sync that 'just worked' live on stage, plus a clear B2B monetization angle (recruiting platforms)."
    },
    {
        "title": "PhishNet Guardian",
        "theme": "Cybersecurity",
        "skills": "Python, Machine Learning, Cybersecurity, Flask",
        "summary": "A browser extension + ML backend that flags phishing emails and fake login pages in real time using a lightweight classifier trained on URL and content features. Won Best Security Hack at CyberHack.",
        "why_it_won": "Tackled an everyday threat with a visible, easy-to-demo browser extension and a model accuracy stat (94%) that judges could verify live."
    },
    {
        "title": "GitPulse",
        "theme": "Open Source",
        "skills": "Python, React, GitHub API, Data Visualization",
        "summary": "A dashboard that visualizes contributor health and 'first-issue friendliness' for open source repos, helping new contributors find welcoming projects. Won Best Open Source Tool at HackOSS.",
        "why_it_won": "Used a real public API (GitHub) for live data, had a strong visual dashboard, and addressed a known OSS community pain point (contributor onboarding)."
    },
    {
        "title": "ChainCert",
        "theme": "Blockchain",
        "skills": "Solidity, React, Node, Blockchain",
        "summary": "A blockchain-based certificate verification system for hackathons and online courses, letting employers instantly verify credentials. Won Best Blockchain Use Case at ETHGlobal local event.",
        "why_it_won": "Picked a blockchain use case beyond 'another token,' with a clear non-technical audience (HR/recruiters) and a working verification demo."
    },
    {
        "title": "StudyMatch AI",
        "theme": "AI",
        "skills": "Python, Machine Learning, NLP, Flask, React",
        "summary": "Matches students into study groups based on course schedules, learning style, and topic gaps, using embeddings + a similarity matching engine, then auto-generates a personalized study plan via an LLM. Won Best AI Hack at a university hackathon.",
        "why_it_won": "The team showed a live embedding-based matching demo plus AI-generated plans, directly mirroring the kind of matching engine many platforms need."
    },
    {
        "title": "DevRadar",
        "theme": "Web Development",
        "skills": "React, Flask, Chart.js, Python",
        "summary": "A 'team strength radar' tool that analyzes each teammate's GitHub languages and self-reported skills to visualize team coverage gaps before a hackathon starts. Won Most Useful Tool award.",
        "why_it_won": "Directly useful to other hackers in the room (meta value), simple radar chart visualization made the insight instantly understandable."
    },
    {
        "title": "RescueLink",
        "theme": "AI",
        "skills": "Python, Machine Learning, Computer Vision, Flask",
        "summary": "A computer vision pipeline that scans drone footage to detect stranded people after natural disasters and plots them on a live map for rescue teams. Won Grand Prize at a global AI for Good hackathon.",
        "why_it_won": "High emotional and social impact theme, combined with a working CV model demo on sample footage and a clear deployment story for NGOs."
    },
    {
        "title": "SkillSwap",
        "theme": "Web Development",
        "skills": "React, Node, Flask, AI",
        "summary": "A peer-to-peer micro-learning marketplace where users trade skills (e.g. 'I'll teach you React if you teach me UI design'), matched via an AI compatibility score similar to dating-app matching. Won Best UX at a regional hackathon.",
        "why_it_won": "Familiar 'matching app' mental model applied to a fresh use case, with strong visual design and a frictionless onboarding flow demoed live."
    },
]


def get_corpus_texts():
    """Returns list of combined text blobs for TF-IDF vectorization."""
    return [
        f"{p['title']} {p['theme']} {p['skills']} {p['summary']}"
        for p in WINNING_PROJECTS
    ]
