"""
NeuroScan AI - Analytics Dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from database.db_operations import get_analytics


def render_analytics(doctor_id: int, doctor_name: str):
    st.markdown(f"## 📊 Dashboard")
    st.markdown(f"*Welcome back, Dr. {doctor_name}*")

    data = get_analytics(doctor_id)

    tp   = data["total_patients"]
    ts   = data["total_scans"]
    dist = data["tumor_distribution"]

    tumor_count  = sum(r["count"] for r in dist if r["predicted_class"] != "notumor")
    normal_count = next((r["count"] for r in dist if r["predicted_class"] == "notumor"), 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Patients", tp)
    c2.metric("🔬 Total Scans",    ts)
    c3.metric("⚠️ Tumor Cases",    tumor_count)
    c4.metric("✅ Normal Scans",   normal_count)

    st.markdown("---")

    col_l, col_r = st.columns(2)

    # Pie chart
    with col_l:
        st.markdown("### 🧠 Tumor Distribution")
        if dist:
            labels = [r["predicted_class"].upper() for r in dist]
            values = [r["count"] for r in dist]
            colors = ["#FF4B4B", "#FF8C00", "#FFD700", "#00C851"]
            fig = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.4,
                marker=dict(colors=colors[:len(labels)]),
                textinfo="label+percent"
            ))
            fig.update_layout(template="plotly_dark", height=330,
                              margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No scan data yet.")

    # Bar chart
    with col_r:
        st.markdown("### 📅 Monthly Scans")
        monthly = data["monthly_scans"]
        if monthly:
            months = [r["month"] for r in reversed(monthly)]
            counts = [r["count"] for r in reversed(monthly)]
            fig = go.Figure(go.Bar(
                x=months, y=counts,
                marker_color="#00d4ff",
                text=counts, textposition="outside"
            ))
            fig.update_layout(template="plotly_dark", height=330,
                              xaxis_title="Month", yaxis_title="Scans",
                              margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly data yet.")

    # Recent scans
    st.markdown("---")
    st.markdown("### 🕒 Recent Scans")
    recent = data["recent_scans"]
    if recent:
        df = pd.DataFrame([{
            "Date":       r["scan_date"][:10],
            "Patient":    r["full_name"],
            "Diagnosis":  r["predicted_class"].upper(),
            "Confidence": f"{r['confidence']:.1f}%",
        } for r in recent])
        st.dataframe(df, use_container_width=True, height=280)
    else:
        st.info("No recent scans.")

    # Detection rate
    if ts > 0:
        st.markdown("---")
        st.markdown("### 📈 Detection Insights")
        det_rate = (tumor_count / ts) * 100
        nor_rate = (normal_count / ts) * 100
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(f"""
            <div style='background:#1a1a2e;border-radius:12px;padding:1.5rem;text-align:center;
                        border:1px solid #FF4B4B55;'>
                <div style='font-size:2.5rem;color:#FF4B4B;font-weight:bold;'>{det_rate:.1f}%</div>
                <div style='color:#aaa;margin-top:4px;'>Tumor Detection Rate</div>
            </div>""", unsafe_allow_html=True)
        with cc2:
            st.markdown(f"""
            <div style='background:#1a1a2e;border-radius:12px;padding:1.5rem;text-align:center;
                        border:1px solid #00C85155;'>
                <div style='font-size:2.5rem;color:#00C851;font-weight:bold;'>{nor_rate:.1f}%</div>
                <div style='color:#aaa;margin-top:4px;'>Normal Scan Rate</div>
            </div>""", unsafe_allow_html=True)
