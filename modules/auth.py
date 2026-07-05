"""
NeuroScan AI - Authentication Module
Mandatory Login / Signup — collects Name, Gender, Age, Address
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
        "id":      st.session_state.get("doctor_id"),
        "name":    st.session_state.get("doctor_name"),
        "email":   st.session_state.get("doctor_email"),
        "gender":  st.session_state.get("doctor_gender"),
        "age":     st.session_state.get("doctor_age"),
        "address": st.session_state.get("doctor_address"),
    }


def logout():
    for key in ["doctor_id", "doctor_name", "doctor_email",
                "doctor_gender", "doctor_age", "doctor_address"]:
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
        "<div class='auth-sub'>Please login or create an account to continue</div>",
        unsafe_allow_html=True
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_signup = st.tabs(["🔐  Login", "📝  Sign Up"])

        # ── LOGIN ────────────────────────────────────────────────
        with tab_login:
            st.markdown("### Welcome Back")
            email    = st.text_input("Email Address", key="l_email",
                                     placeholder="you@example.com")
            password = st.text_input("Password", type="password",
                                     key="l_pass", placeholder="••••••••")

            if st.button("Login →", use_container_width=True, type="primary", key="l_btn"):
                if not email or not password:
                    st.error("Please fill all fields.")
                else:
                    doctor = get_doctor_by_email(email)
                    if doctor and verify_password(password, doctor["password"]):
                        st.session_state["doctor_id"]      = doctor["id"]
                        st.session_state["doctor_name"]    = doctor["full_name"]
                        st.session_state["doctor_email"]   = doctor["email"]
                        st.session_state["doctor_gender"]  = doctor["gender"]
                        st.session_state["doctor_age"]     = doctor["age"]
                        st.session_state["doctor_address"] = doctor["address"]
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        # ── SIGN UP ──────────────────────────────────────────────
        with tab_signup:
            st.markdown("### Create Your Account")

            full_name = st.text_input("Full Name", key="r_name",
                                      placeholder="John Smith")

            c1, c2 = st.columns(2)
            with c1:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="r_gender")
            with c2:
                age = st.number_input("Age", min_value=1, max_value=120,
                                      step=1, key="r_age")

            address = st.text_area("Address", key="r_address",
                                   placeholder="House #, Street, City")

            r_email = st.text_input("Email Address", key="r_email",
                                    placeholder="you@example.com")

            c3, c4 = st.columns(2)
            with c3:
                r_pass = st.text_input("Password", type="password", key="r_pass1")
            with c4:
                r_pass2 = st.text_input("Confirm Password", type="password", key="r_pass2")

            if st.button("Create Account →", use_container_width=True,
                         type="primary", key="r_btn"):
                if not all([full_name, gender, age, address, r_email, r_pass, r_pass2]):
                    st.error("Please fill all required fields.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = add_doctor(
                        full_name=full_name,
                        email=r_email,
                        hashed_password=hash_password(r_pass),
                        gender=gender,
                        age=int(age),
                        address=address,
                    )
                    if ok:
                        st.success("✅ Account created! Please login from the Login tab.")
                    else:
                        st.error(msg)
