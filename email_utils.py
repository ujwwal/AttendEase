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
                    <a href="https://www.attendease.live/login" class="cta-button">Login to Your Account →</a>
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


def send_weekly_report_email(user_email, user_name, start_date, end_date, subjects_data, weekly_percentage, overall_percentage):
    """
    Send a weekly attendance performance report.
    """
    try:
        # Generate subject rows
        subject_rows = ""
        for sub in subjects_data:
            status_color = "#10b981" if sub['attended'] == sub['total'] and sub['total'] > 0 else "#f59e0b" if sub['attended'] > 0 else "#ef4444"
            
            subject_rows += f"""
            <tr class="subject-row">
                <td class="subject-name">{sub['name']}</td>
                <td align="right">
                    <div class="subject-stats">
                        <span class="fraction">{sub['attended']}/{sub['total']}</span>
                        <span class="badge" style="background-color: {status_color}22; color: {status_color};">
                            {int(sub['attended']/sub['total']*100) if sub['total'] > 0 else 0}%
                        </span>
                    </div>
                </td>
            </tr>
            """

        # Determine mood/message based on weekly percentage
        if weekly_percentage >= 90:
            header_color = "#10b981" # Green
            message = "🌟 Amazing work! You're crushing it this week!"
        elif weekly_percentage >= 75:
            header_color = "#3b82f6" # Blue
            message = "👍 Good job! Keep confident and consistent."
        elif weekly_percentage >= 60:
            header_color = "#f59e0b" # Orange
            message = "⚠️ Keep an eye on your attendance. Every lecture counts!"
        else:
            header_color = "#ef4444" # Red
            message = "🚨 Critical: Your attendance was low this week. Please catch up!"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Inter', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; overflow: hidden; border: 1px solid #334155; }}
                .header {{ background-color: {header_color}; padding: 30px; text-align: center; }}
                .header h1 {{ color: #ffffff !important; margin: 0; font-size: 24px; text-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
                .header p {{ color: rgba(255,255,255,0.9) !important; margin-top: 5px; font-size: 14px; }}
                .content {{ padding: 30px; background-color: #1e293b; color: #f8fafc; }}
                /* Using tables for layout to ensure spacing works in all clients */
                .stats-table {{ width: 100%; border-spacing: 15px 0; margin-bottom: 25px; }}
                .stat-card {{ background-color: #334155; padding: 20px; border-radius: 12px; text-align: center; width: 100%; box-sizing: border-box; }}
                .stat-label {{ color: #cbd5e1 !important; font-size: 13px; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: {header_color} !important; }}
                .stat-value-white {{ font-size: 28px; font-weight: bold; color: #ffffff !important; }}
                
                .subject-table {{ width: 100%; border-collapse: collapse; background-color: #334155; border-radius: 12px; overflow: hidden; margin-bottom: 25px; }}
                .subject-row td {{ padding: 15px 20px; border-bottom: 1px solid #475569; }}
                .subject-row:last-child td {{ border-bottom: none; }}
                .subject-name {{ font-weight: 600; color: #f8fafc !important; font-size: 15px; text-align: left; }}
                .subject-stats {{ display: inline-flex; align-items: center; gap: 10px; justify-content: flex-end; }}
                .fraction {{ color: #cbd5e1 !important; font-size: 14px; margin-right: 8px; }}
                .badge {{ padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; display: inline-block; }}
                
                .message-box {{ background-color: {header_color}22; border-left: 4px solid {header_color}; padding: 15px; margin-bottom: 25px; border-radius: 4px; color: #e2e8f0 !important; font-size: 14px; line-height: 1.5; }}
                .footer {{ text-align: center; padding: 20px; background-color: #0f172a; color: #64748b !important; font-size: 12px; }}
                .cta-button {{ display: block; width: 100%; background-color: #6366f1; color: #ffffff !important; text-align: center; padding: 14px 0; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 5px; transition: background 0.2s; border: none; }}
                .cta-button:hover {{ background-color: #4f46e5; }}
                .attendance-warning {{ background-color: #451a03; border: 1px solid #f59e0b; color: #fcd34d !important; padding: 12px; border-radius: 8px; margin-top: 25px; text-align: center; font-size: 13px; font-weight: 500; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Weekly Report</h1>
                    <p>{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <div class="message-box">
                        {message}
                    </div>

                    <table class="stats-table" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td width="50%" valign="top">
                                <div class="stat-card">
                                    <div class="stat-label">This Week</div>
                                    <div class="stat-value">{weekly_percentage}%</div>
                                </div>
                            </td>
                            <td width="50%" valign="top">
                                <div class="stat-card">
                                    <div class="stat-label">Overall</div>
                                    <div class="stat-value-white">{overall_percentage}%</div>
                                </div>
                            </td>
                        </tr>
                    </table>

                    <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #cbd5e1 !important; font-weight: 600;">Subject Breakdown</h3>
                    
                    <table class="subject-table" width="100%" cellspacing="0" cellpadding="0" border="0">
                        {subject_rows}
                    </table>

                    <a href="https://www.attendease.live/dashboard" class="cta-button">View Detailed Dashboard</a>

                    <div class="attendance-warning">
                        ⚠️ Reminder: Please maintain your attendance above 75% to avoid any academic penalties.
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2024 AttendEase. Keep up the momentum!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": "AttendEase <no-reply@attendease.live>",
            "to": [user_email],
            "subject": f"📊 Your Weekly Attendance Report ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        print(f"Weekly report sent to {user_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send weekly report: {e}")
        return False
