"""
AttendEase Farewell Email Script
---------------------------------
Sends a farewell email to all registered users.
Run AFTER loading env vars from Vercel:
    vercel env pull .env.local
    export $(cat .env.local | grep -v '#' | xargs)
    python send_farewell.py
"""

import os
import sys
import resend
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

# ── Resend API Setup ────────────────────────────────────────────────────────
resend.api_key = os.environ.get('RESEND_API_KEY')
if not resend.api_key:
    print("❌  RESEND_API_KEY not set. Please load your env vars first.")
    sys.exit(1)

# ── Database Setup ──────────────────────────────────────────────────────────
database_url = (
    os.environ.get('DATABASE_URL')
    or os.environ.get('POSTGRES_URL_NON_POOLING')
    or os.environ.get('POSTGRES_URL')
)

if not database_url:
    print("❌  No DATABASE_URL found. Please load your env vars first.")
    sys.exit(1)

# Fix postgres:// → postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Add SSL for hosted Postgres
parsed = urlparse(database_url)
if 'sslmode' not in database_url and parsed.scheme.startswith('postgresql'):
    sep = '&' if '?' in database_url else '?'
    database_url = f"{database_url}{sep}sslmode=require"

engine = create_engine(database_url, connect_args={'connect_timeout': 10})


# ── Fetch All Users ─────────────────────────────────────────────────────────
def get_all_users():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name, email FROM users ORDER BY id"))
        return [{"name": row[0], "email": row[1]} for row in result]


# ── Email HTML Builder ──────────────────────────────────────────────────────
def build_farewell_html(user_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>A Farewell from AttendEase</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    body {{
      font-family: 'Inter', Arial, sans-serif;
      background-color: #0a0f1e;
      color: #e2e8f0;
      margin: 0;
      padding: 24px 16px;
    }}

    .wrapper {{
      max-width: 620px;
      margin: 0 auto;
    }}

    .card {{
      background: linear-gradient(160deg, #1a2236 0%, #0f172a 100%);
      border-radius: 20px;
      border: 1px solid #1e3a5f;
      overflow: hidden;
    }}

    /* Header */
    .header {{
      background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 50%, #1a1a4e 100%);
      padding: 48px 40px 40px;
      text-align: center;
      border-bottom: 1px solid #1e3a5f;
    }}

    .logo-mark {{
      font-size: 52px;
      display: block;
      margin-bottom: 16px;
      filter: drop-shadow(0 4px 12px rgba(99,102,241,0.5));
    }}

    .header h1 {{
      margin: 0;
      font-size: 28px;
      font-weight: 700;
      color: #f1f5f9;
      letter-spacing: -0.5px;
    }}

    .header .batch-tag {{
      display: inline-block;
      margin-top: 12px;
      background: rgba(99,102,241,0.15);
      border: 1px solid rgba(99,102,241,0.4);
      color: #a5b4fc;
      font-size: 13px;
      font-weight: 600;
      padding: 5px 16px;
      border-radius: 100px;
      letter-spacing: 0.5px;
    }}

    /* Body */
    .body {{
      padding: 40px;
    }}

    .greeting {{
      font-size: 17px;
      font-weight: 600;
      color: #f1f5f9;
      margin: 0 0 20px;
    }}

    p {{
      color: #94a3b8;
      font-size: 15px;
      line-height: 1.8;
      margin: 0 0 18px;
    }}

    /* Shutdown Notice Box */
    .notice-box {{
      background: rgba(239,68,68,0.07);
      border: 1px solid rgba(239,68,68,0.25);
      border-radius: 12px;
      padding: 20px 24px;
      margin: 28px 0;
    }}

    .notice-box .notice-title {{
      color: #fca5a5;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 14px;
    }}

    .notice-box ul {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}

    .notice-box ul li {{
      color: #cbd5e1;
      font-size: 14px;
      line-height: 1.7;
      padding: 4px 0;
      padding-left: 20px;
      position: relative;
    }}

    .notice-box ul li::before {{
      content: "—";
      position: absolute;
      left: 0;
      color: #ef4444;
      font-weight: 600;
    }}

    /* Stats Bar */
    .stats-bar {{
      display: table;
      width: 100%;
      background: rgba(99,102,241,0.07);
      border: 1px solid rgba(99,102,241,0.2);
      border-radius: 12px;
      margin: 28px 0;
      padding: 20px 24px;
      box-sizing: border-box;
    }}

    .stat {{
      display: table-cell;
      text-align: center;
      width: 33%;
    }}

    .stat-num {{
      font-size: 22px;
      font-weight: 700;
      color: #818cf8;
      display: block;
    }}

    .stat-label {{
      font-size: 12px;
      color: #64748b;
      margin-top: 4px;
      display: block;
    }}

    /* Divider */
    .divider {{
      border: none;
      border-top: 1px solid #1e293b;
      margin: 28px 0;
    }}

    /* CTA */
    .cta-section {{
      background: rgba(99,102,241,0.07);
      border: 1px solid rgba(99,102,241,0.2);
      border-radius: 12px;
      padding: 24px;
      margin: 28px 0;
      text-align: center;
    }}

    .cta-section p {{
      margin: 0 0 16px;
      font-size: 14px;
      color: #94a3b8;
    }}

    .cta-button {{
      display: inline-block;
      background: linear-gradient(135deg, #4f46e5, #7c3aed);
      color: #ffffff !important;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      padding: 12px 28px;
      border-radius: 8px;
      letter-spacing: 0.3px;
    }}

    /* Sign off */
    .signoff {{
      margin-top: 32px;
    }}

    .signoff p {{
      margin: 2px 0;
      color: #94a3b8;
      font-size: 14px;
    }}

    .signoff .name {{
      font-size: 16px;
      font-weight: 700;
      color: #f1f5f9;
    }}

    .signoff .role {{
      color: #6366f1;
      font-size: 13px;
      font-weight: 500;
    }}

    .signoff .domains {{
      margin-top: 6px;
    }}

    .signoff .domains a {{
      color: #6366f1;
      text-decoration: none;
      font-size: 13px;
      margin-right: 10px;
    }}

    /* Footer */
    .footer {{
      text-align: center;
      padding: 24px 40px;
      border-top: 1px solid #1e293b;
      background: rgba(0,0,0,0.2);
    }}

    .footer p {{
      margin: 4px 0;
      font-size: 12px;
      color: #475569;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="card">

      <!-- Header -->
      <div class="header">
        <span class="logo-mark">📚</span>
        <h1>A Farewell from AttendEase</h1>
        <span class="batch-tag">BCA Morning 2023 – 2026</span>
      </div>

      <!-- Body -->
      <div class="body">

        <p class="greeting">Hi {user_name},</p>

        <p>
          AttendEase started as a simple idea at the beginning of our final year.
        </p>

        <p>
          As students ourselves, we knew the anxiety of checking attendance percentages,
          calculating how many classes we could miss, and wondering whether we'd stay above
          that infamous 75% mark. So we built something to make college life just a little easier.
        </p>

        <p>
          Today, as the BCA Morning 2023–2026 batch reaches the end of its journey,
          <strong style="color:#f1f5f9;">AttendEase reaches the end of its journey too.</strong>
        </p>

        <!-- Shutdown Notice -->
        <div class="notice-box">
          <div class="notice-title">⚡ Effective Immediately — AttendEase is shutting down</div>
          <ul>
            <li>Weekly attendance update emails will no longer be sent.</li>
            <li>Attendance marking on the platform has been discontinued.</li>
            <li>The dashboard will remain accessible for a short period for anyone who wishes to revisit their records.</li>
          </ul>
        </div>

        <p>
          What began as a small side project gradually became a part of our college experience.
          Over the years, thousands of attendance entries were recorded, countless emails were delivered,
          and hopefully, a few panic attacks before attendance reviews were prevented. 😄
        </p>

        <p>
          But more importantly, <strong style="color:#f1f5f9;">AttendEase became something built by a student, for fellow students.</strong>
        </p>

        <hr class="divider">

        <p>
          To everyone who used the platform, reported bugs, suggested improvements, shared it with friends,
          or simply trusted it throughout these three years — <strong style="color:#f1f5f9;">thank you.</strong>
          Your support is what kept it alive.
        </p>

        <p>
          And to the BCA Morning 2023–2026 batch: <strong style="color:#f1f5f9;">congratulations.</strong>
        </p>

        <p>
          We've attended our last lectures, submitted our final assignments, survived exams,
          and created memories that will stay with us long after college ends. As we move on to
          the next chapter of our lives and careers, AttendEase will quietly take its final bow alongside us.
        </p>

        <p>
          Wishing each one of you the very best in whatever comes next — whether that's a job you love, a master's you've been dreaming of, or a path you're still figuring out. You've put in the work, and you deserve everything good that's coming your way. Go make it count. 🌟
        </p>

        <!-- CTA for juniors -->
        <div class="cta-section">
          <p>
            If there are <strong style="color:#f1f5f9;">juniors or future batches</strong> who could benefit from this
            platform and would like to continue its story, we'd love to hear from you.
            Reach out to the owner of the app — you probably already know who that is. 😉
          </p>
          <a href="mailto:ujwwalgupta@gmail.com" class="cta-button">Reach Out →</a>
        </div>

        <p>
          Building AttendEase has been one of the most rewarding experiences of my college life.
          Thank you for being a part of it.
        </p>

        <p>
          Here's to new beginnings, bigger goals, and everything that comes next.
        </p>

        <!-- Sign Off -->
        <div class="signoff">
          <p>With gratitude,</p>
          <p class="name">Ujjwal Gupta</p>
          <p class="role">Creator, AttendEase</p>
          <div class="domains">
            <a href="https://attendease.vercel.app">attendease.vercel.app</a>
            <a href="https://attendease.live">attendease.live</a>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="footer">
        <p>© 2023–2026 AttendEase &nbsp;·&nbsp; Built with ❤️ by a BCA Morning student, for BCA Morning students.</p>
        <p>This is the last automated email you will receive from AttendEase.</p>
      </div>

    </div>
  </div>
</body>
</html>"""


# ── Send Farewell Email ─────────────────────────────────────────────────────
def send_farewell_email(user_email: str, user_name: str) -> bool:
    try:
        params = {
            "from": "Ujjwal @ AttendEase <no-reply@attendease.live>",
            "to": [user_email],
            "subject": "📚 A Farewell from AttendEase — Thank You, BCA 2023–2026",
            "html": build_farewell_html(user_name),
        }
        response = resend.Emails.send(params)
        print(f"  ✅  Sent to {user_email} ({user_name}) — ID: {response.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"  ❌  Failed for {user_email} ({user_name}): {e}")
        return False


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("\n🎓  AttendEase Farewell Email Sender")
    print("=" * 42)

    print("\n📦  Fetching users from database...")
    users = get_all_users()
    print(f"    Found {len(users)} user(s).\n")

    if not users:
        print("No users found. Exiting.")
        return

    # ── Preview first, then confirm ──────────────────────────────────────
    print("Users to be notified:")
    for i, u in enumerate(users, 1):
        print(f"  {i:3}. {u['name']:<30} {u['email']}")

    print("\n" + "=" * 42)
    confirm = input("\n🚀  Type  SEND  to send the farewell email to all users: ").strip()

    if confirm != "SEND":
        print("\n⛔  Aborted. No emails were sent.")
        return

    print("\n📨  Sending emails...\n")
    success, failed = 0, 0
    for u in users:
        if send_farewell_email(u["email"], u["name"]):
            success += 1
        else:
            failed += 1

    print(f"\n{'=' * 42}")
    print(f"✅  Successfully sent : {success}")
    print(f"❌  Failed            : {failed}")
    print(f"📬  Total             : {success + failed}")
    print("\nAttendEase signing off. 🎓\n")


if __name__ == "__main__":
    main()
