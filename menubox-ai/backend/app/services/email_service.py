"""
Email service using Resend for transactional emails.
"""

import resend
from app.core.config import get_settings

settings = get_settings()


def init_resend():
    """Initialize Resend with API key."""
    api_key = getattr(settings, 'resend_api_key', None)
    if api_key:
        resend.api_key = api_key
        return True
    return False


async def send_password_reset_email(to_email: str, reset_token: str, user_name: str = None) -> bool:
    """
    Send password reset email.
    
    Args:
        to_email: User's email address
        reset_token: The reset token
        user_name: Optional user name for personalization
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not init_resend():
        print("Resend API key not configured, skipping email")
        return False
    
    # Build reset URL - update this for production
    frontend_url = getattr(settings, 'frontend_url', 'http://localhost:5173')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 24px; 
                background-color: #f97316; 
                color: white !important; 
                text-decoration: none; 
                border-radius: 8px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🍽️ MenuBox AI - Password Reset</h2>
            <p>{greeting}</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            <div class="footer">
                <p>— The MenuBox AI Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        from_email = getattr(settings, 'from_email', 'noreply@menubox.ai')
        
        params = {
            "from": f"MenuBox AI <{from_email}>",
            "to": [to_email],
            "subject": "Reset your MenuBox AI password",
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"Password reset email sent to {to_email}: {response}")
        return True
        
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False


async def send_verification_email(to_email: str, verification_token: str, user_name: str = None) -> bool:
    """
    Send email verification link.
    """
    if not init_resend():
        print("Resend API key not configured, skipping email")
        return False
    
    frontend_url = getattr(settings, 'frontend_url', 'http://localhost:5173')
    verify_url = f"{frontend_url}/verify-email?token={verification_token}"
    
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 24px; 
                background-color: #f97316; 
                color: white !important; 
                text-decoration: none; 
                border-radius: 8px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🍽️ Welcome to MenuBox AI!</h2>
            <p>{greeting}</p>
            <p>Thanks for signing up! Please verify your email address by clicking the button below:</p>
            <a href="{verify_url}" class="button">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verify_url}</p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <div class="footer">
                <p>— The MenuBox AI Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        from_email = getattr(settings, 'from_email', 'noreply@menubox.ai')
        
        params = {
            "from": f"MenuBox AI <{from_email}>",
            "to": [to_email],
            "subject": "Verify your MenuBox AI email",
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"Verification email sent to {to_email}: {response}")
        return True
        
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


async def send_welcome_email(to_email: str, user_name: str = None) -> bool:
    """
    Send welcome email after verification.
    """
    if not init_resend():
        return False
    
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    frontend_url = getattr(settings, 'frontend_url', 'http://localhost:5173')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 24px; 
                background-color: #f97316; 
                color: white !important; 
                text-decoration: none; 
                border-radius: 8px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎉 Welcome to MenuBox AI!</h2>
            <p>{greeting}</p>
            <p>Your email is verified and you're all set! Here's what you can do:</p>
            <ul>
                <li>📸 Upload menu photos for instant recommendations</li>
                <li>🔍 Search any restaurant to find your perfect dish</li>
                <li>⚙️ Set your dietary preferences for personalized results</li>
            </ul>
            <a href="{frontend_url}/dashboard" class="button">Start Exploring</a>
            <p>Enjoy your meals! 🍽️</p>
        </div>
    </body>
    </html>
    """
    
    try:
        from_email = getattr(settings, 'from_email', 'noreply@menubox.ai')
        
        params = {
            "from": f"MenuBox AI <{from_email}>",
            "to": [to_email],
            "subject": "Welcome to MenuBox AI! 🍽️",
            "html": html_content
        }
        
        resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False