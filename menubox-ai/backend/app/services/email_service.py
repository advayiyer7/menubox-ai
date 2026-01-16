"""
Email service using Brevo (formerly Sendinblue) for transactional emails.
Free tier: 300 emails/day, can send to ANY email address.
"""

import httpx
from app.core.config import get_settings

settings = get_settings()

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an email using Brevo API.
    """
    api_key = getattr(settings, 'brevo_api_key', None)
    if not api_key:
        print("Brevo API key not configured, skipping email")
        return False
    
    from_email = getattr(settings, 'from_email', 'noreply@menubox.ai')
    from_name = getattr(settings, 'from_name', 'MenuBox AI')
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "sender": {
            "name": from_name,
            "email": from_email
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BREVO_API_URL,
                headers=headers,
                json=payload,
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                print(f"Email sent to {to_email}: {response.json()}")
                return True
            else:
                print(f"Brevo API error: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


async def send_password_reset_email(to_email: str, reset_token: str, user_name: str = None) -> bool:
    """
    Send password reset email.
    """
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
    
    return await send_email(to_email, "Reset your MenuBox AI password", html_content)


async def send_verification_email(to_email: str, verification_token: str, user_name: str = None) -> bool:
    """
    Send email verification link.
    """
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
    
    return await send_email(to_email, "Verify your MenuBox AI email", html_content)


async def send_welcome_email(to_email: str, user_name: str = None) -> bool:
    """
    Send welcome email after verification.
    """
    frontend_url = getattr(settings, 'frontend_url', 'http://localhost:5173')
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
    
    return await send_email(to_email, "Welcome to MenuBox AI! 🍽️", html_content)