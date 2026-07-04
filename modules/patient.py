"""
NeuroScan AI - Patient Management Module
"""

import streamlit as st
import pandas as pd
from database.db_operations import (
    add_patient, get_patients_by_doctor, update_patient,
    delete_patient, search_patients, get_scans_by_patient, get_progression
)
import plotly.graph_objects as go


def render_patient_management(doctor_id: int):
    st.markdown("## 👥 Patient Management")
    tab1, tab2, tab3 = st.tabs(["📋 All Patients", "➕ Add Patient", "📈 Progression"])

    # ── ALL PATIENTS ──────────────────────────────────────────────
    with tab1:
        query    = st.text_input("🔍 Search by name, phone, or email", key="pat_search")
        patients = search_patients(doctor_id, query) if query else get_patients_by_doctor(doctor_id)

        if not patients:
            st.info("No patients found. Add your first patient!")
        else:
            st.caption(f"{len(patients)} patient(s) found")
            for p in patients:
                with st.expander(
                    f"👤 {p['full_name']}  |  Age: {p['age']}  |  {p['gender']}  |  📞 {p['phone'] or 'N/A'}"
                ):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"""
| Field | Value |
|-------|-------|
| **Email** | {p['email'] or 'N/A'} |
| **Address** | {p['address'] or 'N/A'} |
| **Medical History** | {p['medical_history'] or 'N/A'} |
| **Registered** | {p['created_at'][:10]} |
                        """)
                    with c2:
                        scans = get_scans_by_patient(p['id'])
                        st.metric("Scans", len(scans))
                        if st.button("✏️ Edit", key=f"edit_{p['id']}"):
                            st.session_state["editing_patient"] = p['id']
                        if st.button("🗑️ Delete", key=f"del_{p['id']}"):
                            st.session_state["confirm_delete"] = p['id']

                    # Edit form
                    if st.session_state.get("editing_patient") == p['id']:
                        _edit_form(p)

                    # Delete confirmation
                    if st.session_state.get("confirm_delete") == p['id']:
                        st.error("⚠️ Delete this patient and all their scans?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Yes, Delete", key=f"yes_{p['id']}", type="primary"):
                                delete_patient(p['id'])
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()
                        with cc2:
                            if st.button("Cancel", key=f"no_{p['id']}"):
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()

                    # Scan history table
                    if scans:
                        st.markdown("**📁 Scan History**")
                        df = pd.DataFrame([{
                            "Date":       s['scan_date'][:10],
                            "Diagnosis":  s['predicted_class'].upper(),
                            "Confidence": f"{s['confidence']:.1f}%",
                            "Size":       s['tumor_size_category'],
                            "Coverage":   f"{s['tumor_percentage']:.1f}%",
                        } for s in scans])
                        st.dataframe(df, use_container_width=True)

    # ── ADD PATIENT ───────────────────────────────────────────────
    with tab2:
        _add_form(doctor_id)

    # ── PROGRESSION ───────────────────────────────────────────────
    with tab3:
        _progression(doctor_id)


def _add_form(doctor_id):
    st.markdown("### ➕ Add New Patient")
    c1, c2 = st.columns(2)
    with c1:
        name   = st.text_input("Full Name *", key="np_name")
        age    = st.number_input("Age *", 1, 120, 30, key="np_age")
        phone  = st.text_input("Phone", key="np_phone")
    with c2:
        gender  = st.selectbox("Gender *", ["Male", "Female", "Other"], key="np_gender")
        email   = st.text_input("Email", key="np_email")
        address = st.text_input("Address", key="np_addr")
    history = st.text_area("Medical History / Notes", key="np_hist",
                            placeholder="Previous diagnoses, medications, allergies...")

    if st.button("💾 Save Patient", type="primary", use_container_width=True):
        if not name:
            st.error("Patient name is required.")
        else:
            pid = add_patient(doctor_id, name, age, gender, phone, email, address, history)
            st.success(f"✅ Patient '{name}' added! (ID: {pid})")
            st.balloons()


def _edit_form(p):
    st.markdown("**✏️ Edit Patient**")
    c1, c2 = st.columns(2)
    with c1:
        n  = st.text_input("Name",   value=p['full_name'],  key=f"en_{p['id']}")
        a  = st.number_input("Age",  value=p['age'] or 25,  key=f"ea_{p['id']}")
        ph = st.text_input("Phone",  value=p['phone'] or "", key=f"ep_{p['id']}")
    with c2:
        opts = ["Male", "Female", "Other"]
        g  = st.selectbox("Gender", opts,
                          index=opts.index(p['gender']) if p['gender'] in opts else 0,
                          key=f"eg_{p['id']}")
        em = st.text_input("Email",   value=p['email'] or "",   key=f"ee_{p['id']}")
        ad = st.text_input("Address", value=p['address'] or "", key=f"ead_{p['id']}")
    hi = st.text_area("Medical History", value=p['medical_history'] or "", key=f"eh_{p['id']}")

    cs, cc = st.columns(2)
    with cs:
        if st.button("💾 Save", key=f"sv_{p['id']}", type="primary"):
            update_patient(p['id'], n, a, g, ph, em, ad, hi)
            st.session_state.pop("editing_patient", None)
            st.success("Patient updated!")
            st.rerun()
    with cc:
        if st.button("Cancel", key=f"cx_{p['id']}"):
            st.session_state.pop("editing_patient", None)
            st.rerun()


def _progression(doctor_id):
    st.markdown("### 📈 Tumor Progression Tracker")
    patients = get_patients_by_doctor(doctor_id)
    if not patients:
        st.info("No patients available.")
        return

    opts     = {f"{p['full_name']} (ID:{p['id']})": p['id'] for p in patients}
    selected = st.selectbox("Select Patient", list(opts.keys()))
    prog     = get_progression(opts[selected])

    if len(prog) < 2:
        st.info("At least 2 scans needed to show progression.")
        if prog:
            st.metric("Latest Scan", prog[0]['predicted_class'].upper(),
                      f"{prog[0]['tumor_percentage']:.1f}% coverage")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[p['scan_date'][:10] for p in prog],
        y=[p['tumor_percentage'] for p in prog],
        mode="lines+markers",
        name="Coverage %",
        line=dict(color="#00d4ff", width=2),
        marker=dict(size=8),
    ))
    fig.update_layout(
        title=f"Tumor Progression — {selected}",
        xaxis_title="Date", yaxis_title="Coverage (%)",
        template="plotly_dark", height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame([{
        "Date":       p['scan_date'][:10],
        "Diagnosis":  p['predicted_class'].upper(),
        "Coverage %": p['tumor_percentage'],
        "Confidence": p['confidence'],
    } for p in prog])
    st.dataframe(df, use_container_width=True)
