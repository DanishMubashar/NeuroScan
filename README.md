# 🧠 NeuroScan AI
**AI-Powered Brain Tumor Detection & Clinical Support System**

> **Author:** Muhammad Danish Mubashar | BSCS-M2-22-25 | University of Sahiwal
> **Supervisor:** Muhammad Waqas

---

## 📁 Project Structure

```
NeuroScanAI/
├── app.py                 ← Run this file
├── requirements.txt
├── .env                   ← Create this (see Step 2)
├── models/
│   └── brain_tumor_xception_model.keras  ← Put your model here
├── database/
│   ├── db_setup.py
│   └── db_operations.py
├── modules/
│   ├── auth.py            ← Login / Signup
│   ├── prediction.py      ← AI Model prediction
│   ├── tumor_analysis.py  ← OpenCV + Grad-CAM
│   ├── patient.py         ← Patient management
│   ├── analytics.py       ← Dashboard charts
│   ├── report.py          ← PDF generation
│   └── neurobot.py        ← AI chatbot (Gemini)
├── uploads/               ← MRI images saved here (auto)
└── reports/               ← PDF reports saved here (auto)
```

---

## ⚙️ Setup — 3 Steps Only

### Step 1 — Install packages
```bash
pip install -r requirements.txt
```

### Step 2 — Create .env file
Create a file named `.env` in the project root:
```
GOOGLE_API_KEY=your_gemini_key_here
```
Get free Gemini API key → https://aistudio.google.com/app/apikey

### Step 3 — Add your model
- Download `brain_tumor_model.keras` from Kaggle notebook Output tab
- Rename it to: `brain_tumor_xception_model.keras`
- Place it inside the `models/` folder

### Run the app
```bash
streamlit run app.py
```

---

## 🚀 Features

| Feature | Details |
|---------|---------|
| 🔐 Doctor Auth | Secure login/signup with bcrypt hashing |
| 🔬 MRI Analysis | Xception model — 4-class tumor classification |
| 📍 Tumor Localization | OpenCV contour detection |
| 🔍 Grad-CAM | Explainable AI heatmaps |
| 👥 Patient Records | Add, edit, delete, search patients |
| 📈 Progression Tracking | Track tumor growth over time |
| 📊 Analytics Dashboard | Plotly charts and statistics |
| 📄 PDF Reports | Professional medical report generation |
| 🤖 NeuroBot | Google Gemini AI chatbot |

---

## 📊 Model Performance

| Metric | Score |
|--------|-------|
| Train Accuracy | 96.84% |
| Validation Accuracy | 89.75% |
| Test Accuracy | 88.13% |

**Classes:** glioma · meningioma · pituitary · notumor

---

## ⚠️ Disclaimer
This system is for educational and research purposes only.
It is a decision-support tool — NOT a replacement for professional medical diagnosis.
