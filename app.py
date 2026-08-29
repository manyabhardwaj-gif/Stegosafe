import streamlit as st
import tempfile, os, time
from dotenv import load_dotenv
from stego import extract_message
from crypto_utils import double_decrypt
from otp_utils import generate_otp, send_otp_email

load_dotenv()
AUTHORIZED_EMAIL = os.getenv("AUTHORIZED_EMAIL", "")

st.set_page_config(
    page_title="StegoSafe",
    page_icon="🔐",
    layout="centered"
)

st.markdown("""
<style>
    .stButton>button {
        background-color: #2980B9;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: bold;
        width: 100%;
    }
    .success-box {
        background: #D5F5E3;
        border-left: 5px solid #1E8449;
        padding: 16px; border-radius: 8px;
        font-size: 16px; color: #1E8449;
        font-weight: bold;
    }
    .error-box {
        background: #FADBD8;
        border-left: 5px solid #C0392B;
        padding: 16px; border-radius: 8px;
        color: #C0392B; font-weight: bold;
    }
    .info-box {
        background: #D6EAF8;
        border-left: 5px solid #2980B9;
        padding: 14px; border-radius: 8px;
        color: #154360;
    }
    .warn-box {
        background: #FEF9E7;
        border-left: 5px solid #D4AC0D;
        padding: 14px; border-radius: 8px;
        color: #7D6608;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────
st.markdown("# 🔐 StegoSafe")
st.markdown("**Reveal secret messages hidden inside ordinary images.**")
st.markdown("---")

# ── Session state ─────────────────────────────────────────
for key in ["otp","otp_sent_at","otp_verified"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ══════════════════════════════════════════════════════════
# STEP 0 — Upload image
# ══════════════════════════════════════════════════════════
st.markdown("### Step 1 — Upload the Image")
st.markdown('<div class="info-box">Upload the stego PNG image you received.</div>',
            unsafe_allow_html=True)
st.markdown("")

stego_upload = st.file_uploader("Upload stego PNG image", type=["png"])

if stego_upload:
    st.image(stego_upload,
             caption="Uploaded Image — hidden message inside!",
             use_container_width=True)
    st.markdown("---")

    # ══════════════════════════════════════════════════════
    # STEP 1 — OTP (always goes to YOUR email)
    # ══════════════════════════════════════════════════════
    st.markdown("### Step 2 — OTP Verification")
    st.markdown(
        '<div class="warn-box">📧 OTP will be sent to the authorized email. '
        'Ask the sender to share the OTP with you.</div>',
        unsafe_allow_html=True
    )
    st.markdown("")

    col1, col2 = st.columns([2,1])
    with col1:
        send_btn = st.button("📧 Send OTP to Authorized Email")
    with col2:
        if st.session_state.otp_verified:
            st.success("✅ Verified!")

    if send_btn:
        with st.spinner("Sending OTP..."):
            otp = generate_otp()
            success, msg = send_otp_email(AUTHORIZED_EMAIL, otp)
        if success:
            st.session_state.otp = otp
            st.session_state.otp_sent_at = time.time()
            st.session_state.otp_verified = False
            st.markdown(
                '<div class="success-box">✅ OTP sent! '
                'Ask the sender for the code.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="error-box">❌ Failed to send OTP: {msg}</div>',
                unsafe_allow_html=True
            )

    if st.session_state.otp and not st.session_state.otp_verified:
        st.markdown("")
        entered_otp = st.text_input(
            "Enter the 6-digit OTP (get it from the sender)",
            max_chars=6,
            placeholder="e.g. 847392"
        )
        if st.button("✅ Verify OTP"):
            if time.time() - st.session_state.otp_sent_at > 300:
                st.markdown(
                    '<div class="error-box">❌ OTP expired. '
                    'Click Send OTP again.</div>',
                    unsafe_allow_html=True
                )
                st.session_state.otp = None
            elif entered_otp == st.session_state.otp:
                st.session_state.otp_verified = True
                st.rerun()
            else:
                st.markdown(
                    '<div class="error-box">❌ Wrong OTP. Try again.</div>',
                    unsafe_allow_html=True
                )

    # ══════════════════════════════════════════════════════
    # STEP 2 — Passwords
    # ══════════════════════════════════════════════════════
    if st.session_state.otp_verified:
        st.markdown("---")
        st.markdown("### Step 3 — Enter Both Passwords")
        st.markdown(
            '<div class="info-box">Ask the sender for both passwords.</div>',
            unsafe_allow_html=True
        )
        st.markdown("")

        rp1 = st.text_input("Password 1 — AES layer",
                             type="password",
                             placeholder="Enter Password 1")
        rp2 = st.text_input("Password 2 — ChaCha layer",
                             type="password",
                             placeholder="Enter Password 2")

        if st.button("🔍 Reveal Hidden Message"):
            if not rp1 or not rp2:
                st.markdown(
                    '<div class="error-box">❌ Both passwords required.</div>',
                    unsafe_allow_html=True
                )
            else:
                try:
                    with st.spinner("Decrypting your message..."):
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        ) as tmp:
                            tmp.write(stego_upload.read())
                            tmp_path = tmp.name

                        payload = extract_message(tmp_path)
                        result  = double_decrypt(payload, rp1, rp2)
                        os.unlink(tmp_path)

                    st.markdown(
                        f'<div class="success-box">'
                        f'✅ Hidden Message Revealed!<br><br>'
                        f'💬 {result}</div>',
                        unsafe_allow_html=True
                    )
                    st.balloons()
                    st.session_state.otp_verified = False
                    st.session_state.otp = None

                except ValueError:
                    st.markdown(
                        '<div class="error-box">❌ Wrong password(s). '
                        'Cannot decrypt.</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.markdown(
                        f'<div class="error-box">❌ Error: {e}</div>',
                        unsafe_allow_html=True
                    )

# ── Footer ────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "Made by **Manya Bhardwaj · Mahi Kumari · Paras Panwar** "
    "| Guide: **Rohit Gupta**"
)