from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
app = Flask(__name__)

# ---------- CONFIGURE GEMINI AI ----------
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# =================================================================
#              ANALYTICS STORAGE (NEW)
# =================================================================
analytics = {
    "total_queries": 0,
    "rule_hits": 0,
    "ai_hits": 0,
    "top_questions": {},
    "feedback": {"good": 0, "bad": 0},
    "sessions": set()
}

# =================================================================
#              DYNAMIC DATA: CANTEEN MENU & BUS ROUTES
# =================================================================

CANTEEN_MENU = {
    "Monday":    {"breakfast": "Idli, Dosa, Upma, Coconut Chutney, Tea/Coffee",
                  "lunch": "Rice, Sambar, Rasam, Poriyal, Curd, Papad",
                  "snacks": "Samosa, Bajji, Tea"},
    "Tuesday":   {"breakfast": "Puri, Vada, Pongal, Chutney, Tea/Coffee",
                  "lunch": "Rice, Dal Fry, Vegetable Curry, Rasam, Curd",
                  "snacks": "Bonda, Veg Puffs, Coffee"},
    "Wednesday": {"breakfast": "Dosa, Idli, Uttapam, Sambar, Tea/Coffee",
                  "lunch": "Rice, Sambar, Kootu, Poriyal, Curd, Papad",
                  "snacks": "Mirchi Bajji, Veg Cutlet, Tea"},
    "Thursday":  {"breakfast": "Upma, Vada, Dosa, Chutney, Tea/Coffee",
                  "lunch": "Rice, Rasam, Poriyal, Sambar, Curd",
                  "snacks": "Punugulu, Mysore Bonda, Coffee"},
    "Friday":    {"breakfast": "Idli, Puri, Pongal, Chutney, Tea/Coffee",
                  "lunch": "Rice, Sambar, Kootu, Curd, Pickle",
                  "snacks": "Veg Samosa, Onion Pakoda, Tea"},
    "Saturday":  {"breakfast": "Dosa, Vada, Upma, Sambar, Tea/Coffee",
                  "lunch": "Veg Biryani, Raita, Curd, Papad",
                  "snacks": "Veg Puffs, Bajji, Coffee"},
    "Sunday":    {"breakfast": "Puri, Dosa, Upma, Tea/Coffee",
                  "lunch": "Veg Pulao / Veg Biryani, Raita, Curd",
                  "snacks": "Snacks available till 5 PM"},
}

BUS_ROUTES = {
    "mvp colony":       {"route": "Route 1",  "bus": "AP31-GVPW-01", "pickup": "7:15 AM", "drop": "4:15 PM"},
    "gajuwaka":         {"route": "Route 2",  "bus": "AP31-GVPW-02", "pickup": "6:50 AM", "drop": "4:30 PM"},
    "dwaraka nagar":    {"route": "Route 3",  "bus": "AP31-GVPW-03", "pickup": "7:00 AM", "drop": "4:20 PM"},
    "madhurawada":      {"route": "Route 4",  "bus": "AP31-GVPW-04", "pickup": "7:20 AM", "drop": "4:10 PM"},
    "railway station":  {"route": "Route 5",  "bus": "AP31-GVPW-05", "pickup": "6:55 AM", "drop": "4:35 PM"},
    "rtc complex":      {"route": "Route 6",  "bus": "AP31-GVPW-06", "pickup": "7:05 AM", "drop": "4:25 PM"},
    "nad junction":     {"route": "Route 7",  "bus": "AP31-GVPW-07", "pickup": "7:10 AM", "drop": "4:20 PM"},
    "simhachalam":      {"route": "Route 8",  "bus": "AP31-GVPW-08", "pickup": "6:45 AM", "drop": "4:40 PM"},
    "kancharapalem":    {"route": "Route 9",  "bus": "AP31-GVPW-09", "pickup": "7:00 AM", "drop": "4:30 PM"},
    "bheemili":         {"route": "Route 10", "bus": "AP31-GVPW-10", "pickup": "6:40 AM", "drop": "4:45 PM"},
    "anakapalle":       {"route": "Route 11", "bus": "AP31-GVPW-11", "pickup": "6:30 AM", "drop": "4:50 PM"},
    "steel plant":      {"route": "Route 12", "bus": "AP31-GVPW-12", "pickup": "7:10 AM", "drop": "4:25 PM"},
}

# =================================================================
#              COMPLETE RULE-BASED KNOWLEDGE BASE
# =================================================================
rule_base = {

    "college timings": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:6px;">⏰ College Timings</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.6;">
        <b>Monday – Friday:</b> 8:40 AM to 3:30 PM<br>
        <b>Saturday & Sunday:</b> Closed
      </div>
    </div>""",

    "principal": """
    <div style="background:linear-gradient(135deg,#fff4e6,#fffbf5); padding:14px 18px; border-radius:14px; border-left:5px solid #ff9800;">
      <div style="font-weight:700; color:#e67e00; font-size:14px; margin-bottom:6px;">👩‍💼 Principal</div>
      <div style="color:#1a1a2e; font-size:13px;">Dr. R. K. Goswami</div>
    </div>""",

    "about college": """
    <div style="background:linear-gradient(135deg,#f0f4ff,#fafbff); padding:14px 18px; border-radius:14px; border-left:5px solid #4A3FBF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:6px;">🏫 About GVPW</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.6;">GVPW College of Engineering for Women is a premier women's institution established in 2001, affiliated with Andhra University.</div>
    </div>""",

    "contact": """
    <div style="background:linear-gradient(135deg,#e8f7f0,#f5fdfa); padding:14px 18px; border-radius:14px; border-left:5px solid #00a86b;">
      <div style="font-weight:700; color:#007a4d; font-size:14px; margin-bottom:8px;">📞 Contact Us</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.8;">
        <b>Phone:</b> +91-XXXXXXXXXX<br>
        <b>Email:</b> info@gvpcew.ac.in<br>
        <b>Website:</b> <a href="https://www.gvpcew.ac.in" style="color:#6C63FF;">gvpcew.ac.in</a><br>
        <b>Address:</b> GVPW Campus, Visakhapatnam, AP
      </div>
    </div>""",

    "college map": '''
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:12px; border-radius:16px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:8px;">🗺️ GVPW Campus Blueprint</div>
      <svg viewBox="0 0 600 500" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:500px; border-radius:12px; background:#fff; display:block; margin:0 auto;">
        <polyline points="300,480 300,280 380,280 380,180" fill="none" stroke="#a0aab8" stroke-width="28" stroke-linecap="round" stroke-linejoin="round"/>
        <polyline points="300,480 300,280 380,280 380,180" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="12,6"/>
        <polygon points="300,410 288,425 312,425" fill="#4A3FBF" />
        <polygon points="340,280 360,268 360,292" fill="#4A3FBF" />
        <polygon points="380,240 368,255 392,255" fill="#4A3FBF" />
        <circle cx="300" cy="480" r="10" fill="#4A3FBF" stroke="#fff" stroke-width="2" />
        <text x="260" y="505" font-size="14" font-weight="bold" fill="#1a1a2e">🚪 Main Gate</text>
        <text x="310" y="380" font-size="14" fill="#6C63FF" font-weight="700">⬇️ 500m</text>
        <text x="390" y="270" font-size="14" fill="#6C63FF" font-weight="700">↩️ Right Turn</text>
        <text x="390" y="230" font-size="14" fill="#6C63FF" font-weight="700">⬇️ 200m</text>
        <rect x="230" y="20" width="240" height="160" fill="#fff" stroke="#1a1a2e" stroke-width="4" rx="8" />
        <polygon points="380,180 365,200 395,200" fill="#e83a6b" />
        <text x="400" y="195" font-size="13" fill="#e83a6b" font-weight="700">⬆️ Entrance</text>
        <rect x="230" y="20" width="240" height="40" fill="#d5c4ff" stroke="#1a1a2e" stroke-width="2" />
        <text x="350" y="42" font-size="13" font-weight="bold" fill="#1a1a2e" text-anchor="middle">🏢 3rd Floor</text>
        <text x="350" y="56" font-size="11" fill="#333" text-anchor="middle">📡 ECE &amp; ⚡ EEE</text>
        <rect x="230" y="60" width="240" height="40" fill="#c0d6ff" stroke="#1a1a2e" stroke-width="2" />
        <text x="350" y="82" font-size="13" font-weight="bold" fill="#1a1a2e" text-anchor="middle">🏢 2nd Floor</text>
        <text x="350" y="96" font-size="11" fill="#333" text-anchor="middle">🖥️ IT</text>
        <rect x="230" y="100" width="240" height="40" fill="#b7e0c1" stroke="#1a1a2e" stroke-width="2" />
        <text x="350" y="122" font-size="13" font-weight="bold" fill="#1a1a2e" text-anchor="middle">🏢 1st Floor</text>
        <text x="350" y="136" font-size="11" fill="#333" text-anchor="middle">💻 CSE</text>
        <rect x="230" y="140" width="120" height="40" fill="#ffd8b2" stroke="#1a1a2e" stroke-width="2" />
        <text x="290" y="160" font-size="12" font-weight="bold" fill="#1a1a2e" text-anchor="middle">🎭 Big</text>
        <text x="290" y="173" font-size="11" fill="#555" text-anchor="middle">Auditorium</text>
        <rect x="350" y="140" width="120" height="40" fill="#cfe2ff" stroke="#1a1a2e" stroke-width="2" />
        <text x="410" y="160" font-size="12" font-weight="bold" fill="#1a1a2e" text-anchor="middle">📚 1st Year</text>
        <text x="410" y="173" font-size="11" fill="#555" text-anchor="middle">Classrooms</text>
      </svg>
    </div>''',

    "admission process": """
    <div style="background:linear-gradient(135deg,#e8f7f0,#f5fdfa); padding:14px 18px; border-radius:14px; border-left:5px solid #00a86b;">
      <div style="font-weight:700; color:#007a4d; font-size:14px; margin-bottom:10px;">🎓 Admission Process</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.9;">
        <b>Step 1:</b> Online application<br>
        <b>Step 2:</b> Submit documents (10+2 marksheet, TC)<br>
        <b>Step 3:</b> GVPW-EE Entrance Exam + Counselling<br>
        <b>Step 4:</b> Fee payment &amp; verification
      </div>
    </div>""",

    "admission form": """
    <div style="background:linear-gradient(135deg,#e8f7f0,#f5fdfa); padding:14px 18px; border-radius:14px; border-left:5px solid #00a86b;">
      <div style="font-weight:700; color:#007a4d; font-size:14px; margin-bottom:6px;">📝 Admission Form</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.7;">
        Apply online at <a href="https://www.gvpcew.ac.in" style="color:#6C63FF;">gvpcew.ac.in</a><br>
        Or collect from the college office (10 AM – 4 PM).
      </div>
    </div>""",

    "library timings": """
    <div style="background:linear-gradient(135deg,#fff4e6,#fffbf5); padding:14px 18px; border-radius:14px; border-left:5px solid #ff9800;">
      <div style="font-weight:700; color:#e67e00; font-size:14px; margin-bottom:6px;">📚 Library Timings</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.6;">
        <b>Mon – Sat:</b> 9:00 AM – 7:00 PM<br>
        <b>Sundays & Holidays:</b> Closed
      </div>
    </div>""",

    "library": """
    <div style="background:linear-gradient(135deg,#fff4e6,#fffbf5); padding:14px 18px; border-radius:14px; border-left:5px solid #ff9800;">
      <div style="font-weight:700; color:#e67e00; font-size:14px; margin-bottom:6px;">📚 Library</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.7;">50,000+ books, 200+ journals, and a digital section with IEEE, Springer, and J-Gate access.</div>
    </div>""",

    "branches": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:10px;">🏛️ B.Tech Branches</div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:12px;">
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>1.</b> CSE</div>
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>2.</b> AI-ML</div>
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>3.</b> Cyber Security</div>
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>4.</b> ECE</div>
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>5.</b> EEE</div>
        <div style="background:white; padding:8px 10px; border-radius:8px; border:1px solid #e0e0f5;"><b>6.</b> IT</div>
      </div>
      <div style="margin-top:10px; font-size:12px; color:#555;">💡 Type a branch name to get the syllabus PDF link.</div>
    </div>""",

    "cse faculty": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF; max-height:520px; overflow-y:auto;">
      <div style="font-weight:700; color:#4A3FBF; font-size:15px; margin-bottom:10px;">👩‍🏫 Department of CSE — Faculty</div>
      <div style="font-size:11px; color:#666; margin-bottom:10px;">Total: 24 Faculty + 3 Adjunct</div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #e83a6b; margin-bottom:8px;">
        <b style="color:#b3194f; font-size:13px;">1. Prof. Dr. P. V. S. Lakshmi Jagadamba</b><br>
        <span style="font-size:11px;">Professor &amp; HOD • M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 drpvsljagadamba@gvpcew.ac.in • 📞 9848483016</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #6C63FF; margin-bottom:8px;">
        <b style="color:#4A3FBF; font-size:13px;">2. Prof. Dr. P. S. Avadhani</b><br>
        <span style="font-size:11px;">Professor • B.E., M.E., Ph.D</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #6C63FF; margin-bottom:8px;">
        <b style="color:#4A3FBF; font-size:13px;">3. Dr. C. Srinivas</b><br>
        <span style="font-size:11px;">Professor &amp; CoE • B.E., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 csrinivas@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #6C63FF; margin-bottom:8px;">
        <b style="color:#4A3FBF; font-size:13px;">4. Dr. N. Sharmili</b><br>
        <span style="font-size:11px;">Professor • B.E., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 logintosharmi@gmail.com</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #27ae60; margin-bottom:8px;">
        <b style="color:#1e8449; font-size:13px;">5. Dr. V. Lakshmana Rao</b><br>
        <span style="font-size:11px;">Associate Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 lakshman@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">6. Mrs. K. Suneetha</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 suneetha.k@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">7. Dr. S. Sumahasan</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 sumahasan@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">8. Dr. K. Rohini</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 krohini@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">9. Dr. G. Sankara Rao</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 sankararao@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">10. Mrs. Y. Soumya</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 yaraganisowmya@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">11. Dr. D. Indu</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 indumati29@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">12. Mrs. V. Gowtami Annapurna</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 dinavahigowtami@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">13. Mrs. K. V. S. Mounica</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 mounicakona@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">14. Mr. G. Appaji</b><br>
        <span style="font-size:11px;">Assistant Professor (Cyber Security) • M.Tech</span><br>
        <span style="font-size:11px;">📧 appajeeguruvu@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">15. Mrs. M. Aswini</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 aswini.m@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">16. Mrs. R. Archana</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 archana.r@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">17. Dr. Patruni Muralidhara Rao</b><br>
        <span style="font-size:11px;">Assistant Professor (Selection Grade) • Officer In-charge, Cyber Security</span><br>
        <span style="font-size:11px;">B.Tech., M.Tech., Ph.D • 📧 muralidharp@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">18. Mrs. Y. A. V. Lakshmi Prasanna</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 prasanna.ssv@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">19. Mrs. K. Sirisha</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 sirisha.koribilli01@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">20. Ms. D. Sarvani</b><br>
        <span style="font-size:11px;">Assistant Professor • B.Tech., M.Tech.</span><br>
        <span style="font-size:11px;">📧 sarvani1_sd@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">21. Ms. V. Sai Swathi Priya</b><br>
        <span style="font-size:11px;">Assistant Professor • B.E., M.Tech.</span><br>
        <span style="font-size:11px;">📧 swathipriya@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">22. Ms. P. Sreelakshmi Sravani</b><br>
        <span style="font-size:11px;">Assistant Professor • B.E., M.Tech.</span><br>
        <span style="font-size:11px;">📧 sravani.psl@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">23. Ms. P. Mounika</b><br>
        <span style="font-size:11px;">Assistant Professor • B.E., M.Tech.</span><br>
        <span style="font-size:11px;">📧 mounika.p@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">24. Ms. K. Lakshmi</b><br>
        <span style="font-size:11px;">Assistant Professor • B.E., M.Tech.</span><br>
        <span style="font-size:11px;">📧 lakshmikanchani0225@gvpcew.ac.in</span>
      </div>
      <div style="margin-top:12px; padding:10px 12px; background:#fff4e6; border-radius:10px; border-left:4px solid #e67e00;">
        <div style="font-weight:700; color:#e67e00; font-size:13px; margin-bottom:8px;">🎓 Adjunct Professors</div>
        <div style="font-size:12px; color:#1a1a2e; line-height:1.7; margin-bottom:6px;"><b>25. Dr. Sitarama Brahmam</b><br><span style="color:#666; font-size:11px;">Former Principal Consultant &amp; Head, TCS Hyderabad • Ph.D (IIT Madras)</span></div>
        <div style="font-size:12px; color:#1a1a2e; line-height:1.7; margin-bottom:6px;"><b>26. Mr. Sairam Bollapragada</b><br><span style="color:#666; font-size:11px;">Former Global Delivery Head, Microfocus • M.Sc, MBA (IIM-B)</span></div>
        <div style="font-size:12px; color:#1a1a2e; line-height:1.7;"><b>27. Mrs. Abhilasha</b><br><span style="color:#666; font-size:11px;">Centre Director, Edmium Overseas • B.E., M.Tech.</span></div>
      </div>
    </div>""",

    "csm faculty": """
    <div style="background:linear-gradient(135deg,#f0e6ff,#faf5ff); padding:14px 18px; border-radius:14px; border-left:5px solid #8e44ad; max-height:520px; overflow-y:auto;">
      <div style="font-weight:700; color:#6c3483; font-size:15px; margin-bottom:10px;">🤖 CSM (AI-ML) — Faculty</div>
      <div style="font-size:11px; color:#666; margin-bottom:10px;">Total: 12 + 1 Adjunct</div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #6C63FF; margin-bottom:8px;">
        <b style="color:#4A3FBF; font-size:13px;">1. Prof. Dr. M. R. K. Krishna Rao</b><br>
        <span style="font-size:11px;">Professor • Ph.D (TIFR, Bombay)</span><br>
        <span style="font-size:11px;">📧 krishna@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #e83a6b; margin-bottom:8px;">
        <b style="color:#b3194f; font-size:13px;">2. Dr. Dwiti Krishna Bebarta</b><br>
        <span style="font-size:11px;">Professor &amp; HOD • M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 dkbebarta@gvpcew.ac.in • 📞 9381343954</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #6C63FF; margin-bottom:8px;">
        <b style="color:#4A3FBF; font-size:13px;">3. Prof. Dr. G. Sudheer</b><br>
        <span style="font-size:11px;">Professor &amp; Vice-Principal</span><br>
        <span style="font-size:11px;">📧 g.sudheer@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #27ae60; margin-bottom:8px;">
        <b style="color:#1e8449; font-size:13px;">4. Dr. K. Purushotham Naidu</b><br>
        <span style="font-size:11px;">Associate Professor • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 kpnaidu@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">5. Ms. D. B. Santhoshi</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">6. Mrs. H. Gouthami</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">7. Mr. P. Siva</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">8. Mrs. K. Sirisha</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">9. Mr. D. Dileep Kumar</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">10. Mrs. G. Venkata Lakshmi</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">11. Ms. Kanika Soni</b><br>
        <span style="font-size:11px;">Assistant Professor</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #95a5a6; margin-bottom:8px;">
        <b style="color:#5d6d7e; font-size:13px;">12. Ms. G. Jhansi Rani</b><br>
        <span style="font-size:11px;">Ad-hoc Faculty</span>
      </div>
      <div style="margin-top:12px; padding:10px 12px; background:#fff4e6; border-radius:10px; border-left:4px solid #e67e00;">
        <div style="font-weight:700; color:#e67e00; font-size:13px; margin-bottom:6px;">🎓 Adjunct</div>
        <div style="font-size:12px;"><b>13. Dr. B. L. V. Vinay Kumar</b><br><span style="color:#666; font-size:11px;">Syren Technologies • M.Tech., Ph.D</span></div>
      </div>
    </div>""",

    "eee faculty": """
    <div style="background:linear-gradient(135deg,#fffbe0,#fffff5); padding:14px 18px; border-radius:14px; border-left:5px solid #f39c12; max-height:520px; overflow-y:auto;">
      <div style="font-weight:700; color:#b9770e; font-size:15px; margin-bottom:10px;">⚡ Department of EEE — Faculty</div>
      <div style="font-size:11px; color:#666; margin-bottom:10px;">Total: 11 Faculty</div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #e83a6b; margin-bottom:8px;">
        <b style="color:#b3194f; font-size:13px;">1. Dr. R. V. S. Lakshmi Kumari</b><br>
        <span style="font-size:11px;">Professor &amp; HOD • B.Tech., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 sharmalaks@gvpcew.ac.in • 📞 7093413324</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">2. Dr. A. S. V. Vijaya Lakshmi</b><br>
        <span style="font-size:11px;">Assistant Professor • Ph.D</span><br>
        <span style="font-size:11px;">📧 vijayalakshmi.asv@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">3. Dr. M. Krishna</b><br>
        <span style="font-size:11px;">Assistant Professor • Ph.D</span><br>
        <span style="font-size:11px;">📧 mkrishna@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">4. Ms. V. Sree Vidhya</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 sri.vydhyanadhan@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">5. Mr. Y. Ramu</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 ramuyenni6@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">6. Ms. P. Sai Jyothi</b><br>
        <span style="font-size:11px;">Assistant Professor</span><br>
        <span style="font-size:11px;">📧 saijyothip@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">7. Mrs. B. Kusuma Kumari</b><br>
        <span style="font-size:11px;">Assistant Professor</span><br>
        <span style="font-size:11px;">📧 kusuma.kala@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">8. Mr. D. Srinivas Reddy</b><br>
        <span style="font-size:11px;">Assistant Professor</span><br>
        <span style="font-size:11px;">📧 dallisrinivas@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #95a5a6; margin-bottom:8px;">
        <b style="color:#5d6d7e; font-size:13px;">9. Ms. TVSS Madhavi (Ad-hoc)</b><br>
        <span style="font-size:11px;">Assistant Professor</span><br>
        <span style="font-size:11px;">📧 madhavi.tvvs@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">10. Mr. A. Srinivas Rao</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 srinivasallam@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">11. Ms. P. Hemalatha</b><br>
        <span style="font-size:11px;">Assistant Professor</span><br>
        <span style="font-size:11px;">📧 hema.pothuraju@gvpcew.ac.in</span>
      </div>
    </div>""",

    "it faculty": """
    <div style="background:linear-gradient(135deg,#e0f7fa,#f5feff); padding:14px 18px; border-radius:14px; border-left:5px solid #00838f; max-height:520px; overflow-y:auto;">
      <div style="font-weight:700; color:#006064; font-size:15px; margin-bottom:10px;">🖥️ Department of IT — Faculty</div>
      <div style="font-size:11px; color:#666; margin-bottom:10px;">Total: 6 Faculty</div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #e83a6b; margin-bottom:8px;">
        <b style="color:#b3194f; font-size:13px;">1. Dr. M. Bhanu Sridhar</b><br>
        <span style="font-size:11px;">Professor &amp; HOD • B.E., M.Tech., Ph.D</span><br>
        <span style="font-size:11px;">📧 sridharbhanu@gmail.com</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">2. Mrs. R. Sridevi</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 srideviravada@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">3. Mrs. P. Sridevi</b><br>
        <span style="font-size:11px;">Assistant Professor • M.Tech</span><br>
        <span style="font-size:11px;">📧 psridevi@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">4. Mr. Ch. V. V. D. Prasad</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 prasadchelluri@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">5. Mrs. M. Deepthi</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 deepthim@gvpcew.ac.in</span>
      </div>
      <div style="background:white; padding:10px 12px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
        <b style="color:#b9770e; font-size:13px;">6. Mr. G. Tirupathi</b><br>
        <span style="font-size:11px;">Assistant Professor • (Ph.D)</span><br>
        <span style="font-size:11px;">📧 gtr@gvpcew.ac.in</span>
      </div>
    </div>""",

    "cse": """<div style="background:linear-gradient(135deg,#e0f0ff,#f5faff); padding:14px 18px; border-radius:14px; border-left:5px solid #0078d4;"><b style="color:#005a9e; font-size:14px;">💻 CSE Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/CSE%20AUTONOMOUS%20FOUR%20YEAR%20SYLLABUS.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#0078d4; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",
    "aiml": """<div style="background:linear-gradient(135deg,#f0e6ff,#faf5ff); padding:14px 18px; border-radius:14px; border-left:5px solid #8e44ad;"><b style="color:#6c3483; font-size:14px;">🤖 AI-ML Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/CSM%20AUTONOMOUS%20FOUR%20YEAR%20SYLLABUS.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#8e44ad; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",
    "cybersecurity": """<div style="background:linear-gradient(135deg,#ffe6e6,#fff5f5); padding:14px 18px; border-radius:14px; border-left:5px solid #c0392b;"><b style="color:#922b21; font-size:14px;">🔒 Cyber Security Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/2-1%20Course%20Structure%20%20&%20SYllabus%20of%20CSE-Cybersecurity.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#c0392b; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",
    "ece": """<div style="background:linear-gradient(135deg,#e0ffe0,#f5fff5); padding:14px 18px; border-radius:14px; border-left:5px solid #27ae60;"><b style="color:#1e8449; font-size:14px;">📡 ECE Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/ECE%20%20AUTONOMOUS%20SYLLABUS.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#27ae60; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",
    "eee": """<div style="background:linear-gradient(135deg,#fffbe0,#fffff5); padding:14px 18px; border-radius:14px; border-left:5px solid #f39c12;"><b style="color:#b9770e; font-size:14px;">⚡ EEE Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/EEE%20AUTONOMOUS%20FOUR%20YEAR%20SYLLABUS.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#f39c12; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",
    "it": """<div style="background:linear-gradient(135deg,#e0f7fa,#f5feff); padding:14px 18px; border-radius:14px; border-left:5px solid #00838f;"><b style="color:#006064; font-size:14px;">🖥️ IT Syllabus</b><br><a href="https://www.gvpcew.ac.in/Regulations_Syllabus/IT%20AUTONOMOUS%20FINAL%20SYLLABUS.pdf" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 16px; background:#00838f; color:white; border-radius:20px; text-decoration:none; font-size:12px; font-weight:600;">📄 Open PDF</a></div>""",

    "exam schedule": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:8px;">📅 Exam Schedule</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.8;">
        <b>Mid-term:</b> September & March<br>
        <b>Final Exams:</b> November & May
      </div>
    </div>""",

    "exam form": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:6px;">📝 Exam Form</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.7;">Deadline: 1 month before exams.<br>Fee: ₹500 per subject.<br>Fill online on the student portal.</div>
    </div>""",

    "hostel": """
    <div style="background:linear-gradient(135deg,#ffe6f0,#fff5f9); padding:14px 18px; border-radius:14px; border-left:5px solid #e83a6b;">
      <div style="font-weight:700; color:#b3194f; font-size:14px; margin-bottom:8px;">🏠 Women's Hostel</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.8;">
        • On-campus hostel (women only)<br>
        • Wi-Fi + 24/7 electricity<br>
        • Hygienic mess facility<br>
        • <b>Fee:</b> ₹75,000 per year
      </div>
    </div>""",

    "clubs": """
    <div style="background:linear-gradient(135deg,#f0e6ff,#faf5ff); padding:14px 18px; border-radius:14px; border-left:5px solid #8e44ad;">
      <div style="font-weight:700; color:#6c3483; font-size:14px; margin-bottom:10px;">🎯 GVPW Clubs</div>
      <div style="display:grid; gap:6px; font-size:12px;">
        <div style="background:white; padding:8px 12px; border-radius:8px; border:1px solid #e8d5ff;">🎨 <b>Cosengers Club</b></div>
        <div style="background:white; padding:8px 12px; border-radius:8px; border:1px solid #e8d5ff;">🎯 <b>Aimers Club</b></div>
        <div style="background:white; padding:8px 12px; border-radius:8px; border:1px solid #e8d5ff;">💻 <b>GDG Club</b></div>
        <div style="background:white; padding:8px 12px; border-radius:8px; border:1px solid #e8d5ff;">📖 <b>Literary Club</b></div>
        <div style="background:white; padding:8px 12px; border-radius:8px; border:1px solid #e8d5ff;">🤝 <b>NSS</b></div>
      </div>
    </div>""",

    "fee structure": """
    <div style="background:linear-gradient(135deg,#e8f7f0,#f5fdfa); padding:14px 18px; border-radius:14px; border-left:5px solid #00a86b;">
      <div style="font-weight:700; color:#007a4d; font-size:14px; margin-bottom:10px;">💰 B.Tech Fee Structure (per year)</div>
      <div style="display:grid; gap:8px; font-size:12px;">
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #6C63FF;"><b>CSE / CSM</b><br>₹2,10,000 <span style="color:#888;">+ ₹5,000 VAF</span></div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #27ae60;"><b>ECE / IT</b><br>₹1,25,000 <span style="color:#888;">+ ₹5,000 VAF</span></div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #f39c12;"><b>EEE</b><br>₹1,10,000 <span style="color:#888;">+ ₹5,000 VAF</span></div>
      </div>
    </div>""",

    "fees": """
    <div style="background:linear-gradient(135deg,#e8f7f0,#f5fdfa); padding:14px 18px; border-radius:14px; border-left:5px solid #00a86b;">
      <div style="font-weight:700; color:#007a4d; font-size:14px; margin-bottom:8px;">💰 Fees (per year)</div>
      <div style="font-size:12px; color:#1a1a2e; line-height:1.9;">
        <b>CSE / CSM:</b> ₹2,10,000 + ₹5,000 VAF<br>
        <b>ECE / IT:</b> ₹1,25,000 + ₹5,000 VAF<br>
        <b>EEE:</b> ₹1,10,000 + ₹5,000 VAF
      </div>
    </div>""",

    "dress code": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:6px;">👕 Dress Code</div>
      <div style="color:#1a1a2e; font-size:13px;">Casual dress code — No uniform. Dress modestly.</div>
    </div>""",

    "placements": """
    <div style="background:linear-gradient(135deg,#e0f0ff,#f5faff); padding:16px 20px; border-radius:14px; border-left:5px solid #0078d4;">
      <div style="font-weight:700; color:#005a9e; font-size:15px; margin-bottom:12px;">💼 Placement Highlights</div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
        <div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #d0e5ff;">
          <div style="font-size:20px; font-weight:700; color:#0078d4;">90%+</div>
          <div style="font-size:11px; color:#555;">Placement Rate</div>
        </div>
        <div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #d0e5ff;">
          <div style="font-size:20px; font-weight:700; color:#0078d4;">₹6.5 LPA</div>
          <div style="font-size:11px; color:#555;">Average Package</div>
        </div>
        <div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #d0e5ff;">
          <div style="font-size:20px; font-weight:700; color:#0078d4;">₹24 LPA</div>
          <div style="font-size:11px; color:#555;">Highest Package</div>
        </div>
        <div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #d0e5ff;">
          <div style="font-size:20px; font-weight:700; color:#0078d4;">60+</div>
          <div style="font-size:11px; color:#555;">Recruiters</div>
        </div>
      </div>
      <div style="background:white; padding:12px; border-radius:10px; border:1px solid #d0e5ff;">
        <div style="font-size:12px; font-weight:700; color:#005a9e; margin-bottom:6px;">🏢 Top Recruiters</div>
        <div style="font-size:12px; color:#333; line-height:1.7;">
          TCS • Infosys • Wipro • Cognizant • Accenture<br>
          Capgemini • Amazon • Deloitte • Tech Mahindra
        </div>
      </div>
      <div style="margin-top:10px; font-size:11px; color:#666; font-style:italic;">
        📈 Training & Placement Cell conducts aptitude, mock interviews, and soft-skill workshops from 3rd year.
      </div>
    </div>""",

    "internships": """
    <div style="background:linear-gradient(135deg,#f0e6ff,#faf5ff); padding:16px 20px; border-radius:14px; border-left:5px solid #8e44ad; max-height:450px; overflow-y:auto;">
      <div style="font-weight:700; color:#6c3483; font-size:15px; margin-bottom:12px;">🎓 Internship Opportunities</div>
      <div style="font-size:12px; color:#1a1a2e; line-height:1.7;">
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #0078d4; margin-bottom:8px;">
          <b style="color:#005a9e;">🔵 TCS iON</b><br>
          Data Analytics Intern (Remote)<br>
          <span style="color:#777; font-size:11px;">Duration: 2 months • Stipend: ₹10,000/month</span>
        </div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #27ae60; margin-bottom:8px;">
          <b style="color:#1e8449;">🟢 Infosys Springboard</b><br>
          AI/ML Virtual Internship<br>
          <span style="color:#777; font-size:11px;">Duration: 3 months • Certificate + LOR</span>
        </div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #f39c12; margin-bottom:8px;">
          <b style="color:#b9770e;">🟠 Amazon</b><br>
          SDE Summer Intern (Bangalore)<br>
          <span style="color:#777; font-size:11px;">Duration: 6 months • Stipend: ₹80,000/month</span>
        </div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #c0392b; margin-bottom:8px;">
          <b style="color:#922b21;">🔴 Wipro</b><br>
          Cyber Security Trainee<br>
          <span style="color:#777; font-size:11px;">Duration: 3 months • Stipend: ₹15,000/month</span>
        </div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #8e44ad; margin-bottom:8px;">
          <b style="color:#6c3483;">🟣 Local Startups</b><br>
          Web/App Development Internships<br>
          <span style="color:#777; font-size:11px;">Location: Visakhapatnam • Flexible hours</span>
        </div>
        <div style="background:white; padding:10px 14px; border-radius:10px; border-left:4px solid #00838f;">
          <b style="color:#006064;">🔷 Smart India Hackathon (SIH)</b><br>
          Annual internship-linked competition<br>
          <span style="color:#777; font-size:11px;">Top performers get direct internship offers</span>
        </div>
      </div>
      <div style="margin-top:12px; padding:10px 14px; background:#fff4e6; border-radius:10px; border-left:4px solid #e67e00; font-size:12px;">
        📝 <b>Register at:</b> <a href="https://www.gvpcew.ac.in" style="color:#8e44ad; font-weight:600;">gvpcew.ac.in/training</a><br>
        📞 Contact: Training & Placement Cell — Room 204, Admin Block
      </div>
    </div>""",

    "bus routes": """
    <div style="background:linear-gradient(135deg,#fffbe0,#fffff5); padding:14px 18px; border-radius:14px; border-left:5px solid #f39c12; max-height:400px; overflow-y:auto;">
      <div style="font-weight:700; color:#b9770e; font-size:15px; margin-bottom:10px;">🚌 College Bus Routes (Vizag)</div>
      <div style="font-size:12px; color:#1a1a2e; line-height:1.9;">
        <b>Route 1</b> — MVP Colony<br>
        <b>Route 2</b> — Gajuwaka<br>
        <b>Route 3</b> — Dwaraka Nagar<br>
        <b>Route 4</b> — Madhurawada<br>
        <b>Route 5</b> — Railway Station<br>
        <b>Route 6</b> — RTC Complex<br>
        <b>Route 7</b> — NAD Junction<br>
        <b>Route 8</b> — Simhachalam<br>
        <b>Route 9</b> — Kancharapalem<br>
        <b>Route 10</b> — Bheemili<br>
        <b>Route 11</b> — Anakapalle<br>
        <b>Route 12</b> — Steel Plant<br><br>
        💡 Ask a specific area (e.g., <b>"MVP Colony bus"</b>) for exact bus number & timings!
      </div>
    </div>""",

    "canteen": """
    <div style="background:linear-gradient(135deg,#fff4e6,#fffbf5); padding:14px 18px; border-radius:14px; border-left:5px solid #ff9800;">
      <div style="font-weight:700; color:#e67e00; font-size:14px; margin-bottom:6px;">🍴 Canteen Info</div>
      <div style="font-size:13px; color:#1a1a2e; line-height:1.7;">
        <b>Timings:</b> 8:00 AM – 5:00 PM<br>
        <b>Type:</b> Pure Vegetarian 🥗<br><br>
        Type <b>"today menu"</b> or <b>"canteen menu"</b> to see today's menu!
      </div>
    </div>""",

    "events": """
    <div style="background:linear-gradient(135deg,#ffe6f0,#fff5f9); padding:14px 18px; border-radius:14px; border-left:5px solid #e83a6b; max-height:400px; overflow-y:auto;">
      <div style="font-weight:700; color:#b3194f; font-size:15px; margin-bottom:10px;">📅 GVPW Events Calendar 2026</div>
      <div style="font-size:12px; color:#1a1a2e; line-height:1.9;">
        <b>Jan 26:</b> Republic Day Celebration<br>
        <b>Feb 14:</b> Sanskriti Cultural Fest<br>
        <b>Mar 8:</b> Women's Day Program<br>
        <b>Mar 15:</b> Mid-term Exams Begin<br>
        <b>Apr 10:</b> Sports Meet<br>
        <b>May 1:</b> Labour Day Holiday<br>
        <b>May 20:</b> Final Exams Begin<br>
        <b>Jun 15:</b> Summer Vacation<br>
        <b>Jul 20:</b> New Academic Year<br>
        <b>Aug 15:</b> Independence Day<br>
        <b>Sep 5:</b> Teachers' Day<br>
        <b>Sep 20:</b> Mid-term Exams Begin<br>
        <b>Oct 10:</b> TechTitan Tech Fest<br>
        <b>Oct 25:</b> CodeStorm Hackathon<br>
        <b>Nov 14:</b> Children's Day<br>
        <b>Nov 20:</b> Final Exams Begin<br>
        <b>Dec 20:</b> Annual Day Celebration
      </div>
    </div>""",

    "faculty": """
    <div style="background:linear-gradient(135deg,#eef0ff,#f8f9ff); padding:14px 18px; border-radius:14px; border-left:5px solid #6C63FF;">
      <div style="font-weight:700; color:#4A3FBF; font-size:14px; margin-bottom:8px;">👩‍🏫 Faculty</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.8;">
        GVPW has <b>120+ qualified faculty members</b>.<br><br>
        👉 Type a department to see details:<br>
        • <b>cse faculty</b><br>
        • <b>csm faculty</b><br>
        • <b>eee faculty</b><br>
        • <b>it faculty</b>
      </div>
    </div>""",

    "sports": """
    <div style="background:linear-gradient(135deg,#e0ffe0,#f5fff5); padding:14px 18px; border-radius:14px; border-left:5px solid #27ae60;">
      <div style="font-weight:700; color:#1e8449; font-size:14px; margin-bottom:8px;">⚽ Sports Facilities</div>
      <div style="color:#1a1a2e; font-size:13px; line-height:1.8;">
        • Cricket ground<br>
        • Basketball court<br>
        • Badminton court<br>
        • Table tennis<br>
        • Chess<br>
        • Gymnasium<br>
        <b>Annual Sports Meet:</b> January
      </div>
    </div>""",
}

# =================================================================
#              HYBRID ENGINE (with memory + analytics)
# =================================================================
conversation_memory = {}
feedback_log = []

def get_bot_response(user_question, session_id="default", lang="en"):
    # ANALYTICS
    analytics["total_queries"] += 1
    analytics["sessions"].add(session_id)

    clean_q = user_question.lower().strip()

    # --- DYNAMIC: CANTEEN MENU ---
    if "canteen" in clean_q or "menu" in clean_q or "today menu" in clean_q:
        today = datetime.now().strftime("%A")
        menu = CANTEEN_MENU.get(today, {})
        html = f'''
        <div style="background:linear-gradient(135deg,#fff4e6,#fffbf5); padding:14px 18px; border-radius:14px; border-left:5px solid #ff9800;">
          <div style="font-weight:700; color:#e67e00; font-size:14px; margin-bottom:8px;">🍴 Today's Canteen Menu ({today})</div>
          <div style="font-size:13px; color:#1a1a2e; line-height:1.8;">
            <b>🌅 Breakfast:</b> {menu.get("breakfast","")}<br>
            <b>🍛 Lunch:</b> {menu.get("lunch","")}<br>
            <b>🍵 Snacks:</b> {menu.get("snacks","")}
          </div>
          <div style="margin-top:8px; font-size:11px; color:#888; font-style:italic;">🥗 100% Pure Vegetarian</div>
        </div>'''
        analytics["rule_hits"] += 1
        return {"answer": html, "source": "Canteen (Live)", "icon": "🍴"}

    # --- DYNAMIC: BUS ROUTES ---
    for area, info in BUS_ROUTES.items():
        if area in clean_q:
            html = f'''
            <div style="background:linear-gradient(135deg,#fffbe0,#fffff5); padding:14px 18px; border-radius:14px; border-left:5px solid #f39c12;">
              <div style="font-weight:700; color:#b9770e; font-size:14px; margin-bottom:8px;">🚌 {area.title()} Bus Route</div>
              <div style="font-size:13px; color:#1a1a2e; line-height:1.8;">
                <b>Route:</b> {info["route"]}<br>
                <b>Bus No:</b> {info["bus"]}<br>
                <b>Pickup:</b> {info["pickup"]}<br>
                <b>Drop:</b> {info["drop"]}
              </div>
            </div>'''
            analytics["rule_hits"] += 1
            return {"answer": html, "source": "Bus Route", "icon": "🚌"}

    # --- RULE-BASED (longest match first) ---
    sorted_keywords = sorted(rule_base.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in clean_q:
            print(f"✅ RULE HIT: '{keyword}'")
            analytics["rule_hits"] += 1
            analytics["top_questions"][keyword] = analytics["top_questions"].get(keyword, 0) + 1
            if session_id not in conversation_memory:
                conversation_memory[session_id] = []
            conversation_memory[session_id].append({"user": user_question, "bot": keyword})
            conversation_memory[session_id] = conversation_memory[session_id][-10:]
            return {
                "answer": rule_base[keyword],
                "source": "Rule-Based (Instant)",
                "icon": "⚡"
            }

    # --- AI FALLBACK ---
    print("🤖 NO RULE MATCH. Asking Gemini AI (with strict college scope)...")
    analytics["ai_hits"] += 1
    past = conversation_memory.get(session_id, [])
    context_history = "\n".join([f"User: {m['user']}\nBot: (matched {m['bot']})" for m in past[-3:]])

    context = f"""
    You are a helpful assistant ONLY for GVPW College of Engineering for Women (GVPCEW).
    You may ONLY answer questions related to:
    - College timings, admissions, exams, library, hostel, faculty, fees, branches, syllabus, placements, internships, bus routes, canteen, clubs, sports, events.
    - Anything about GVPW campus life.

    If the user's question is NOT related to GVPW or college topics (e.g., general knowledge, movies, weather, personal questions, coding help unrelated to college, etc.), 
    you MUST reply with EXACTLY this sentence and nothing else:
    "Sorry, I couldn't understand that. Please ask me something related to GVPW — like timings, exams, faculty, fees, syllabus, placements, bus routes, canteen, or events."

    Recent conversation:
    {context_history}

    User Question: {user_question}
    """

    try:
        response = model.generate_content(context)
        reply_text = response.text.strip()
        sorry_msg = "Sorry, I couldn't understand that. Please ask me something related to GVPW — like timings, exams, faculty, fees, syllabus, placements, bus routes, canteen, or events."
        gvpw_keywords = ["gvpw", "college", "campus", "cse", "ece", "eee", "it ", "csm", "ai-ml", "cyber",
                         "faculty", "exam", "library", "hostel", "fee", "syllabus", "placement",
                         "internship", "bus", "canteen", "club", "sport", "event", "admission",
                         "principal", "hod", "department", "branch", "semester", "sorry"]
        reply_lower = reply_text.lower()
        if not any(kw in reply_lower for kw in gvpw_keywords):
            reply_text = sorry_msg

        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        conversation_memory[session_id].append({"user": user_question, "bot": "AI fallback"})
        conversation_memory[session_id] = conversation_memory[session_id][-10:]

        return {"answer": reply_text, "source": "AI (Gemini)", "icon": "🧠"}
    except Exception as e:
        return {
            "answer": "Sorry, I couldn't understand that. Please ask me something related to GVPW — like timings, exams, faculty, fees, syllabus, placements, bus routes, canteen, or events.",
            "source": "Error", "icon": "❌"
        }

# =================================================================
#                    FLASK ROUTES
# =================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    session_id = data.get("session_id", "default")
    lang = data.get("lang", "en")
    if not user_msg:
        return jsonify({"error": "No message"}), 400
    result = get_bot_response(user_msg, session_id, lang)
    return jsonify(result)

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    rating = data.get("rating", "")
    if rating in analytics["feedback"]:
        analytics["feedback"][rating] += 1
    feedback_log.append({
        "message": data.get("message", ""),
        "response": data.get("response", ""),
        "rating": rating,
        "timestamp": datetime.now().isoformat(),
    })
    print(f"📝 Feedback received: {rating}")
    return jsonify({"status": "ok"})
@app.route("/admin")
def admin():
    top_qs = sorted(analytics["top_questions"].items(), key=lambda x: x[1], reverse=True)[:10]
    top_html = ''.join(f'<li>{kw.title()} <span class="badge">{cnt}</span></li>' for kw, cnt in top_qs) or '<li>No data yet</li>'
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GVPW Admin - Analytics</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #f8faff; margin: 0; padding: 24px; }}
            h1 {{ color: #4A3FBF; margin-bottom: 8px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 24px 0; }}
            .card {{ background: white; padding: 20px; border-radius: 16px; box-shadow: 0 4px 16px rgba(108, 99, 255, 0.08); border-left: 5px solid #6C63FF; }}
            .card h3 {{ font-size: 13px; color: #666; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .card .num {{ font-size: 32px; font-weight: 700; color: #4A3FBF; }}
            .section {{ background: white; padding: 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); }}
            .section h2 {{ color: #4A3FBF; font-size: 18px; margin-bottom: 16px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ padding: 10px 14px; border-bottom: 1px solid #f0f0f5; display: flex; justify-content: space-between; }}
            li:last-child {{ border-bottom: none; }}
            .badge {{ background: #f0edff; color: #4A3FBF; padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 12px; }}
            a {{ color: #6C63FF; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>📊 GVPW Analytics Dashboard</h1>
        <p style="color: #666;">Real-time stats. <a href="/">← Back to chat</a></p>
        <div class="grid">
            <div class="card"><h3>Total Queries</h3><div class="num">{analytics['total_queries']}</div></div>
            <div class="card" style="border-left-color: #27ae60;"><h3>Rule Hits</h3><div class="num">{analytics['rule_hits']}</div></div>
            <div class="card" style="border-left-color: #f39c12;"><h3>AI Fallbacks</h3><div class="num">{analytics['ai_hits']}</div></div>
            <div class="card" style="border-left-color: #e83a6b;"><h3>Sessions</h3><div class="num">{len(analytics['sessions'])}</div></div>
            <div class="card" style="border-left-color: #27ae60;"><h3>👍 Good</h3><div class="num">{analytics['feedback']['good']}</div></div>
            <div class="card" style="border-left-color: #c0392b;"><h3>👎 Bad</h3><div class="num">{analytics['feedback']['bad']}</div></div>
        </div>
        <div class="section">
            <h2>🔥 Top 10 Questions</h2>
            <ul>{top_html}</ul>
        </div>
    </body>
    </html>
    """


@app.route("/analytics-data")
def analytics_data():
    """Returns analytics as JSON for the in-chat dashboard."""
    top_qs = sorted(analytics["top_questions"].items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({
        "total_queries": analytics["total_queries"],
        "rule_hits": analytics["rule_hits"],
        "ai_hits": analytics["ai_hits"],
        "sessions": len(analytics["sessions"]),
        "good_feedback": analytics["feedback"]["good"],
        "bad_feedback": analytics["feedback"]["bad"],
        "top_questions": [{"keyword": k, "count": v} for k, v in top_qs]
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)