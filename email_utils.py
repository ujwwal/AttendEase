"""
Email utility module using Resend API
"""
import os
import resend

# Initialize Resend with API key from environment variable
resend.api_key = os.environ.get('RESEND_API_KEY')

def send_welcome_email(user_email, user_name, erp_number, password):
    """
    Send a welcome email to newly registered users with their account details.
    Note: Sending password in email is not best practice for production,
    but included as per user request for convenience.
    """
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Inter', Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 48px; margin-bottom: 10px; }}
                h1 {{ color: #f8fafc; margin: 0; font-size: 28px; }}
                .subtitle {{ color: #94a3b8; margin-top: 8px; }}
                .details-card {{ background: #334155; border-radius: 12px; padding: 24px; margin: 24px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #475569; }}
                .detail-row:last-child {{ border-bottom: none; }}
                .label {{ color: #94a3b8; font-size: 14px; }}
                .value {{ color: #f8fafc; font-weight: 600; }}
                .password-value {{ color: #10b981; font-family: monospace; background: #064e3b; padding: 4px 8px; border-radius: 4px; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #64748b; font-size: 12px; }}
                .warning {{ background: #fef3c7; color: #92400e; padding: 12px; border-radius: 8px; margin-top: 20px; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">📚</div>
                    <h1>Welcome to AttendEase!</h1>
                    <p class="subtitle">Your college attendance tracker</p>
                </div>
                
                <p style="color: #e2e8f0;">Hi <strong>{user_name}</strong>,</p>
                <p style="color: #94a3b8;">Thank you for registering with AttendEase! Here are your account details for reference:</p>
                
                <div class="details-card">
                    <div class="detail-row">
                        <span class="label">Full Name</span>
                        <span class="value">{user_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">ERP Number</span>
                        <span class="value">{erp_number}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Email</span>
                        <span class="value">{user_email}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Password</span>
                        <span class="password-value">{password}</span>
                    </div>
                </div>
                
                <div class="warning">
                    ⚠️ <strong>Security Note:</strong> Please keep your password safe and consider changing it after your first login. Never share your password with others.
                </div>
                
                <div style="text-align: center;">
                    <a href="https://attendease.vercel.app/login" class="cta-button">Login to Your Account →</a>
                </div>
                
                <div class="footer">
                    <p>© 2024 AttendEase. Track your attendance, ace your semester!</p>
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": "AttendEase <no-reply@attendease.live>",
            "to": [user_email],
            "subject": f"🎓 Welcome to AttendEase, {user_name}!",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        print(f"Welcome email sent to {user_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


def send_password_reset_email(user_email, user_name, reset_token, reset_url):
    """
    Send a password reset email with a reset link.
    """
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Inter', Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 48px; margin-bottom: 10px; }}
                h1 {{ color: #f8fafc; margin: 0; font-size: 24px; }}
                .token-box {{ background: #334155; border-radius: 12px; padding: 24px; margin: 24px 0; text-align: center; }}
                .token {{ font-size: 32px; font-family: monospace; color: #6366f1; letter-spacing: 4px; font-weight: bold; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #64748b; font-size: 12px; }}
                .warning {{ color: #fbbf24; font-size: 13px; margin-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔐</div>
                    <h1>Password Reset Request</h1>
                </div>
                
                <p style="color: #e2e8f0;">Hi <strong>{user_name}</strong>,</p>
                <p style="color: #94a3b8;">We received a request to reset your password. Use the code below to reset it:</p>
                
                <div class="token-box">
                    <div class="token">{reset_token}</div>
                    <p style="color: #64748b; margin-top: 12px; font-size: 13px;">This code expires in 15 minutes</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="cta-button">Reset Password →</a>
                </div>
                
                <p class="warning" style="text-align: center;">If you didn't request this, you can safely ignore this email.</p>
                
                <div class="footer">
                    <p>© 2024 AttendEase</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": "AttendEase <no-reply@attendease.live>",
            "to": [user_email],
            "subject": "🔐 Reset Your AttendEase Password",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        print(f"Password reset email sent to {user_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False
