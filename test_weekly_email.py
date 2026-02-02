"""
Test Weekly Email Script
Sends a test weekly report email with AI summary to a specific email address.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the email function
from email_utils import send_weekly_report_email

def main():
    # Test email recipient
    test_email = "ujjwalguptamail@gmail.com"
    test_name = "Ujjwal"
    
    # Generate test data
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Sample subjects data (mimicking real data structure)
    subjects_data = [
        {'name': 'Data Structures', 'attended': 4, 'total': 5},
        {'name': 'Operating Systems', 'attended': 3, 'total': 4},
        {'name': 'Computer Networks', 'attended': 2, 'total': 3},
        {'name': 'Database Management', 'attended': 5, 'total': 5},
        {'name': 'Software Engineering', 'attended': 1, 'total': 2},
    ]
    
    # Calculate percentages
    total_attended = sum(sub['attended'] for sub in subjects_data)
    total_classes = sum(sub['total'] for sub in subjects_data)
    weekly_percentage = round((total_attended / total_classes) * 100) if total_classes > 0 else 0
    overall_percentage = 78  # Mock overall percentage
    
    print(f"📧 Sending test weekly report to: {test_email}")
    print(f"📊 Weekly attendance: {weekly_percentage}%")
    print(f"📈 Overall attendance: {overall_percentage}%")
    print(f"📚 Subjects: {len(subjects_data)}")
    print("\n🚀 Sending email with AI summary...")
    
    # Send the email
    success = send_weekly_report_email(
        user_email=test_email,
        user_name=test_name,
        start_date=start_date,
        end_date=end_date,
        subjects_data=subjects_data,
        weekly_percentage=weekly_percentage,
        overall_percentage=overall_percentage
    )
    
    if success:
        print("\n✅ Test weekly email sent successfully!")
        print("   Check your inbox for the email with AI summary.")
    else:
        print("\n❌ Failed to send test email. Check the error messages above.")

if __name__ == '__main__':
    main()
