"""
NeuroScan AI - Authentication Module
"""

import bcrypt
import streamlit as st
from database.db_operations import add_doctor, get_doctor_by_email


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def is_logged_in() -> bool:
    return st.session_state.get("doctor_id") is not None


def get_current_doctor():
    return {
        "id":        st.session_state.get("doctor_id"),
        "name":      st.session_state.get("doctor_name"),
        "email":     st.session_state.get("doctor_email"),
        "specialty": st.session_state.get("doctor_specialty"),
    }


def logout():
    for key in ["doctor_id", "doctor_name", "doctor_email", "doctor_specialty"]:
        st.session_state.pop(key, None)
    st.rerun()


def render_login_page():
    st.markdown("""
    <style>
    .auth-title {
        text-align:center; font-size:3rem; font-weight:800;
        background:linear-gradient(135deg,#00d4ff,#0066cc);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .auth-sub { text-align:center; color:#888; margin-bottom:2rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='auth-title'>🧠 NeuroScan AI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='auth-sub'>AI-Powered Brain Tumor Detection & Clinical Support System</div>",
        unsafe_allow_html=True
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_signup = st.tabs(["🔐  Login", "📝  Register"])

        with tab_login:
            st.markdown("### Welcome Back, Doctor")
            email    = st.text_input("Email Address", key="l_email",
                                     placeholder="doctor@hospital.com")
            password = st.text_input("Password", type="password",
                                     key="l_pass", placeholder="••••••••")

            if st.button("Login →", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please fill all fields.")
                else:
                    doctor = get_doctor_by_email(email)
                    if doctor and verify_password(password, doctor["password"]):
                        st.session_state["doctor_id"]        = doctor["id"]
                        st.session_state["doctor_name"]      = doctor["full_name"]
                        st.session_state["doctor_email"]     = doctor["email"]
                        st.session_state["doctor_specialty"] = doctor["specialty"]
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        with tab_signup:
            st.markdown("### Create Your Account")
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full Name", key="r_name",
                                          placeholder="Dr. John Smith")
            with c2:
                specialty = st.selectbox("Specialty", [
                    "Neurologist", "Neurosurgeon", "Radiologist",
                    "Oncologist", "General Physician", "Researcher"
                ], key="r_spec")

            r_email = st.text_input("Email Address", key="r_email",
                                    placeholder="doctor@hospital.com")
            phone   = st.text_input("Phone Number", key="r_phone",
                                    placeholder="+92-XXX-XXXXXXX")
            c3, c4  = st.columns(2)
            with c3:
                r_pass  = st.text_input("Password", type="password", key="r_pass1")
            with c4:
                r_pass2 = st.text_input("Confirm Password", type="password", key="r_pass2")

            if st.button("Create Account →", use_container_width=True, type="primary"):
                if not all([full_name, r_email, r_pass, r_pass2]):
                    st.error("Please fill all required fields.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = add_doctor(full_name, r_email,
                                         hash_password(r_pass), specialty, phone)
                    if ok:
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error(msg)
