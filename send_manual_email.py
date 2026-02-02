"""
Manual Email Sender Script
Run this script to send custom emails to all users in the database.
Email content is read from 'email_content.txt' in the root directory.

Usage:
    python send_manual_email.py              # Send to all users
    python send_manual_email.py --test       # Send test email to yourself first
    python send_manual_email.py --preview    # Preview email without sending
"""
import os
import sys
import resend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Resend
resend.api_key = os.environ.get('RESEND_API_KEY')

# Database setup
from flask import Flask
from config import Config
from models import db, User

def create_app():
    """Create a minimal Flask app for database access."""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def read_email_content():
    """Read email content from email_content.txt file."""
    content_file = os.path.join(os.path.dirname(__file__), 'email_content.txt')
    
    if not os.path.exists(content_file):
        print("❌ Error: email_content.txt not found!")
        print("   Please create the file with your email content.")
        return None, None
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        print("❌ Error: email_content.txt is empty!")
        print("   Please add your email content to the file.")
        return None, None
    
    # Parse subject and body
    # Format: First line is subject, rest is body
    lines = content.split('\n', 1)
    subject = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    
    return subject, body

def generate_email_html(user_name, body_content):
    """Generate HTML email from plain text content."""
    import re
    
    # Process the body content: convert **text** to <strong>text</strong> and handle line breaks
    # Replace **bold text** with <strong>bold text</strong>
    body_content = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #f1f5f9; font-weight: 600;">\1</strong>', body_content)
    
    # Split into paragraphs but keep them more compact
    paragraphs = body_content.split('\n\n')
    
    # Process each paragraph
    body_html = ''
    for p in paragraphs:
        # Replace single line breaks with <br>
        p = p.replace('\n', '<br>')
        body_html += f'<p style="color: #cbd5e1; margin: 12px 0; line-height: 1.5; font-size: 14px;">{p}</p>'
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; box-sizing: border-box; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .logo {{ font-size: 48px; margin-bottom: 8px; }}
        h1 {{ color: #f8fafc; margin: 0; font-size: 22px; }}
        .greeting {{ color: #e2e8f0; font-size: 15px; margin-bottom: 20px; }}
        .content {{ margin: 20px 0; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #334155; }}
        .footer p {{ color: #64748b; font-size: 12px; margin: 4px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📚</div>
            <h1>AttendEase</h1>
        </div>
        
        <div class="greeting">Hi <strong>{user_name}</strong>,</div>
        
        <div class="content">{body_html}</div>
        
        <center>
            <a href="https://attendease.vercel.app/dashboard" class="cta-button">Open AttendEase →</a>
        </center>
        
        <div class="footer">
            <p>© 2024 AttendEase. Track your attendance, ace your semester!</p>
            <p>Made with ❤ by Ujjwal Gupta</p>
        </div>
    </div>
</body>
</html>"""
    return html_content

def send_email(user_email, user_name, subject, body):
    """Send email to a single user."""
    try:
        html_content = generate_email_html(user_name, body)
        
        params = {
            "from": "AttendEase <no-reply@attendease.live>",
            "to": [user_email],
            "subject": subject,
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        return True, email
    except Exception as e:
        return False, str(e)

def preview_email(subject, body):
    """Preview the email content."""
    print("\n" + "="*60)
    print("📧 EMAIL PREVIEW")
    print("="*60)
    print(f"\n📌 Subject: {subject}")
    print(f"\n📝 Body:\n{body}")
    print("\n" + "="*60)
    
    # Generate and save preview HTML
    preview_html = generate_email_html("Preview User", body)
    preview_file = os.path.join(os.path.dirname(__file__), 'email_preview.html')
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(preview_html)
    print(f"\n✅ HTML preview saved to: email_preview.html")
    print("   Open this file in a browser to see how the email will look.")

def main():
    # Parse arguments
    args = sys.argv[1:]
    test_mode = '--test' in args
    preview_mode = '--preview' in args
    
    # Read email content
    subject, body = read_email_content()
    if not subject:
        return
    
    print(f"\n📧 Email Subject: {subject}")
    print(f"📝 Body length: {len(body)} characters")
    
    # Preview mode
    if preview_mode:
        preview_email(subject, body)
        return
    
    # Create Flask app for database access
    app = create_app()
    
    with app.app_context():
        if test_mode:
            # Test mode - send to admin email
            test_email = "ujjwalguptamail@gmail.com"
            print(f"\n🧪 TEST MODE: Sending to {test_email}")
            
            success, result = send_email(test_email, "Test User", subject, body)
            if success:
                print(f"✅ Test email sent successfully!")
            else:
                print(f"❌ Failed to send test email: {result}")
            return
        
        # Get all users
        users = User.query.all()
        total_users = len(users)
        
        if total_users == 0:
            print("\n⚠️  No users found in the database.")
            return
        
        print(f"\n📊 Found {total_users} users in the database.")
        
        # Confirmation
        confirm = input(f"\n⚠️  Are you sure you want to send emails to ALL {total_users} users? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled.")
            return
        
        # Send emails
        print(f"\n🚀 Sending emails...")
        success_count = 0
        fail_count = 0
        
        for i, user in enumerate(users, 1):
            success, result = send_email(user.email, user.name, subject, body)
            if success:
                print(f"  [{i}/{total_users}] ✅ Sent to {user.email}")
                success_count += 1
            else:
                print(f"  [{i}/{total_users}] ❌ Failed: {user.email} - {result}")
                fail_count += 1
        
        # Summary
        print(f"\n" + "="*40)
        print(f"📊 SUMMARY")
        print(f"="*40)
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"📧 Total: {total_users}")

if __name__ == '__main__':
    main()
