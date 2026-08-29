import os, sys, subprocess
from getpass import getpass
from stego import hide_message, extract_message
from crypto_utils import double_encrypt, double_decrypt
from otp_utils import otp_flow

IMAGE  = "images/sample.png"    # your cover image (never changes)
OUTPUT = "images/stego_output.png"


def banner():
    print("\n" + "=" * 52)
    print("       StegoSafe v2.0 — Double Encrypted")
    print("=" * 52)
    print("  1.  Hide a secret message inside an image")
    print("  2.  Reveal hidden message from an image")
    print("  3.  Open folder (to find & share the image)")
    print("  4.  Exit")
    print("=" * 52)


def get_two_passwords(confirming=False):
    """Ask for both passwords. If confirming=True, ask twice each."""
    print("\n  ⚠️  Two different passwords required")
    print("     (both must be correct to ever read the message)\n")

    p1 = getpass("  🔑 Password 1 — AES layer   : ")
    if confirming:
        c1 = getpass("     Confirm Password 1        : ")
        if p1 != c1:
            print("\n  ❌ Password 1 mismatch. Cancelled.")
            return None, None

    p2 = getpass("\n  🔑 Password 2 — ChaCha layer : ")
    if confirming:
        c2 = getpass("     Confirm Password 2        : ")
        if p2 != c2:
            print("\n  ❌ Password 2 mismatch. Cancelled.")
            return None, None

    return p1, p2


def option_hide():
    print("\n─── HIDE A MESSAGE ───────────────────────────")
    message = input("📝 Type your secret message:\n> ").strip()

    if not message:
        print("❌ Message is empty. Cancelled.")
        return

    # Get and confirm both passwords
    p1, p2 = get_two_passwords(confirming=True)
    if not p1:
        return                            # passwords didn't match

    # Final confirmation BEFORE doing anything
    print("\n─── Confirm before hiding ────────────────────")
    print(f"  Cover image : {IMAGE}")
    print(f"  Output file : {OUTPUT}")
    print(f"  Message     : {message[:40]}{'...' if len(message)>40 else ''}")
    print("──────────────────────────────────────────────")
    go = input("  Proceed? (yes / no): ").strip().lower()

    if go != "yes":
        print("\n❌ Process stopped by you. Nothing was saved.")
        return

    # Now do the work — Ctrl+C here cancels cleanly
    try:
        print("\n  🔐 Step 1/3  Applying double encryption...", end=" ", flush=True)
        encrypted = double_encrypt(message, p1, p2)
        print("Done ✓")

        print("  🖼️  Step 2/3  Hiding data in image pixels...", end=" ", flush=True)
        hide_message(IMAGE, encrypted, OUTPUT)
        print("Done ✓")

        print("  💾 Step 3/3  Saving output image...", end=" ", flush=True)
        print("Done ✓")

        print(f"\n  ✅ SUCCESS — saved to: {OUTPUT}")
        print("  📋 Share this file (see Option 3 for how)")
        print("  ⚠️  Do NOT share via WhatsApp/Instagram — they")
        print("      compress the image and destroy the hidden data.")

    except KeyboardInterrupt:
        print("\n\n  ❌ You pressed Ctrl+C — process cancelled.")
        print("     No output file was saved.")
    except ValueError as e:
        print(f"\n  ❌ Error: {e}")


def option_reveal():
    print("\n─── REVEAL HIDDEN MESSAGE ────────────────────")
    print("  🛡️  3-factor security: OTP + Password1 + Password2\n")
    otp_passed = otp_flow()
    if not otp_passed:
        print("\n  🚫 OTP failed. Cannot proceed.")
        return
    if not os.path.exists(OUTPUT):
        print(f"❌ No output image found at {OUTPUT}")
        print("   Run Option 1 first to hide a message.")
        return

    print(f"  Reading: {OUTPUT}")
    try:
        encrypted = extract_message(OUTPUT)
    except Exception:
        print("❌ Could not read hidden data. Image may be corrupted")
        print("   or was re-saved/compressed after hiding.")
        return

    p1, p2 = get_two_passwords(confirming=False)

    try:
        message = double_decrypt(encrypted, p1, p2)
        print("\n  " + "─" * 46)
        print("  ✅ HIDDEN MESSAGE:")
        print("  " + "─" * 46)
        print(f"  {message}")
        print("  " + "─" * 46)
    except ValueError:
        print("\n  ❌ Wrong password(s). Cannot decrypt.")
        print("     Even one wrong password = complete failure.")
        print("     That's double encryption working correctly.")


def option_share():
    print("\n─── SHARE YOUR IMAGE ─────────────────────────")
    if not os.path.exists(OUTPUT):
        print(f"❌ No output image found at {OUTPUT}")
        print("   Run Option 1 first.")
        return

    folder = os.path.abspath(os.path.dirname(OUTPUT))
    print(f"  📁 Opening folder: {folder}")

    # Open File Explorer at the right folder
    if sys.platform == "win32":
        subprocess.run(["explorer", folder])
    elif sys.platform == "darwin":
        subprocess.run(["open", folder])
    else:
        subprocess.run(["xdg-open", folder])

    print("\n  The image looks like a normal picture.")
    print("  To share it safely:\n")
    print("  ✅ Email            → attach stego_output.png")
    print("  ✅ Google Drive     → upload → share link")
    print("  ✅ OneDrive/Dropbox → upload → share link")
    print("  ✅ Telegram         → tap file icon → Send as File")
    print("  ✅ USB drive        → copy the .png file")
    print()
    print("  ❌ WhatsApp         → compresses image → DATA LOST")
    print("  ❌ Instagram/Twitter→ compresses image → DATA LOST")
    print("  ❌ Screenshot       → creates new file → DATA LOST")
    print()
    print("  Recipient needs:")
    print("  • StegoSafe installed on their PC")
    print("  • Password 1 and Password 2 (tell them separately)")


def main():
    print("\n  Welcome to StegoSafe v2.0")
    print("  AES-256-GCM + ChaCha20-Poly1305 double encryption")

    while True:
        banner()
        try:
            choice = input("  Enter choice (1–4): ").strip()
        except KeyboardInterrupt:
            print("\n\n  👋 Exited safely.")
            break

        if   choice == "1": option_hide()
        elif choice == "2": option_reveal()
        elif choice == "3": option_share()
        elif choice == "4":
            print("\n  👋 Exited safely.")
            break
        else:
            print("  ❌ Invalid. Type 1, 2, 3, or 4.")

        input("\n  Press Enter to go back to menu...")


if __name__ == "__main__":
    main()
    