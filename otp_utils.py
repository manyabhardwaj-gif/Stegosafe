import random
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

OTP_EXPIRY_SECONDS = 300    # 5 minutes
MAX_ATTEMPTS       = 3      # 3 wrong tries = locked out


def generate_otp():
    """Fresh 6-digit OTP every time."""
    return str(random.randint(100000, 999999))


def send_otp_email(receiver_email, otp):
    """
    Sends OTP to receiver_email using Gmail SMTP.
    Uses app password from .env — never your real password.
    """
    sender   = os.getenv("GMAIL_ADDRESS")
    app_pass = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not sender or not app_pass:
        return False, "GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing in .env"

    # Build the email
    msg            = MIMEMultipart()
    msg['From']    = f"StegoSafe Security <{sender}>"
    msg['To']      = receiver_email
    msg['Subject'] = "🔐 StegoSafe — Your OTP Code"

    body = f"""
╔══════════════════════════════════════╗
        StegoSafe Security Alert
╚══════════════════════════════════════╝

Someone is trying to read a hidden message.

Your One-Time Password is:

         ➤  {otp}  ◄

⏳  Valid for 5 minutes only.
🔒  Do not share this with anyone.
❌  If you did not request this, ignore it.

— StegoSafe v2.0
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()                          # encrypt the connection
        server.login(sender, app_pass)
        server.send_message(msg)
        server.quit()
        return True, "sent"
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail login failed — check app password in .env"
    except Exception as e:
        return False, str(e)


def otp_flow():
    """
    Full OTP flow — called by main.py before decryption.
    Returns True if user passes, False if they fail.
    """
    print("\n─── OTP VERIFICATION ─────────────────────────")
    print("  A one-time password will be sent to your email.\n")

    # Ask for email
    email = input("  📧 Enter email address to receive OTP:\n  → ").strip()

    if "@" not in email or "." not in email:
        print("  ❌ That doesn't look like a valid email.")
        return False

    # Generate and send
    otp     = generate_otp()
    sent_at = time.time()

    print(f"\n  📤 Sending OTP to {email}...", end=" ", flush=True)
    success, message = send_otp_email(email, otp)

    if not success:
        print(f"\n  ❌ Could not send email: {message}")
        return False

    print("Sent ✓")
    print("  📥 Check your inbox — also check Spam folder!")
    print("  ⏳ OTP is valid for 5 minutes.\n")

    # 3 attempts
    for attempt in range(1, MAX_ATTEMPTS + 1):
        entered = input(
            f"  🔢 Enter the 6-digit OTP "
            f"(attempt {attempt}/{MAX_ATTEMPTS}): "
        ).strip()

        # Check expiry first
        if time.time() - sent_at > OTP_EXPIRY_SECONDS:
            print("\n  ❌ OTP has expired (5 minutes passed).")
            again = input("  📤 Send a new OTP? (yes/no): ").strip().lower()
            if again == "yes":
                return otp_flow()           # restart fresh
            return False

        # Check correctness
        if entered == otp:
            print("  ✅ OTP verified successfully!\n")
            return True

        remaining = MAX_ATTEMPTS - attempt
        if remaining > 0:
            print(f"  ❌ Wrong OTP — {remaining} attempt(s) remaining.")
        else:
            print("  ❌ Too many wrong attempts. Access denied.")
            print("     Run Option 2 again to start over.")

    return False