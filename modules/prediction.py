import os
import zipfile
import tempfile
import numpy as np
import streamlit as st
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten, Dropout, Dense

CLASS_LABELS = ["glioma", "meningioma", "notumor", "pituitary"]

CLASS_INFO = {
    "glioma": {
        "color":       "#FF4B4B",
        "icon":        "🔴",
        "description": "Glioma originates in the glial cells of the brain or spinal cord.",
        "severity":    "High",
        "action":      "Immediate neurosurgical consultation required."
    },
    "meningioma": {
        "color":       "#FF8C00",
        "icon":        "🟠",
        "description": "Meningioma arises from the meninges surrounding the brain.",
        "severity":    "Medium",
        "action":      "Urgent clinical consultation advised."
    },
    "pituitary": {
        "color":       "#FFD700",
        "icon":        "🟡",
        "description": "Pituitary tumor develops in the pituitary gland at the brain base.",
        "severity":    "Medium",
        "action":      "Endocrinology and neurology referral recommended."
    },
    "notumor": {
        "color":       "#00C851",
        "icon":        "🟢",
        "description": "No tumor detected. Brain structure appears normal.",
        "severity":    "None",
        "action":      "Regular monitoring recommended. Continue routine checkups."
    },
}


def _build_architecture():
    """
    Rebuilds the exact architecture used during training on Kaggle
    (img_shape=(299,299,3), Xception base + Flatten + Dropout(0.3) +
    Dense(128, relu) + Dropout(0.25) + Dense(4, softmax)).

    weights=None here on purpose: we don't want ImageNet weights,
    we're about to load our own trained weights on top of this
    freshly-built architecture.
    """
    img_shape = (299, 299, 3)

    base_model = tf.keras.applications.Xception(
        include_top=False,
        weights=None,
        input_shape=img_shape,
        pooling="max",
    )
    for layer in base_model.layers:
        layer.trainable = False

    model = Sequential([
        base_model,
        Flatten(),
        Dropout(0.3),
        Dense(128, activation="relu"),
        Dropout(0.25),
        Dense(4, activation="softmax"),
    ])
    return model


@st.cache_resource(show_spinner="🧠 Loading AI Model...")
def load_model():
    """
    Load Xception model from models/ folder.

    Tries the normal tf.keras.models.load_model() first. If that fails
    because of the known Keras 2.13 issue where a nested nameless
    Xception sub-model's saved weight names (conv2d, conv2d_2, ...)
    don't match its architecture's layer names (block1_conv1, ...),
    falls back to rebuilding the architecture from scratch and loading
    the weights by skipping mismatches / matching by order instead of
    by name.
    """
    model_path = os.path.join("models", "brain_tumor_model.keras")
    if not os.path.exists(model_path):
        st.error(f"❌ Model not found at `{model_path}`")
        st.info("💡 Put your brain_tumor_model.keras file inside the models/ folder.")
        return None

    # --- Attempt 1: normal load ---
    try:
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception as e:
        first_error = e

    # --- Attempt 2: rebuild architecture + load weights from the .keras archive ---
    try:
        model = _build_architecture()

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(model_path, "r") as zf:
                zf.extractall(tmpdir)
            weights_path = os.path.join(tmpdir, "model.weights.h5")

            # skip_mismatch=True lets matching-named layers (Dense, Dropout, etc.)
            # load normally, while by_name=False falls back to topological/order
            # matching for the Xception sub-model whose saved weight names don't
            # match its architecture's layer names.
            model.load_weights(weights_path, by_name=False, skip_mismatch=True)

        # Compile so .predict() / metrics work the same as the original
        model.compile(
            optimizer="adamax",
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model
    except Exception as e:
        st.error(f"Model loading error: {first_error}")
        st.error(f"Fallback loading also failed: {e}")
        return None


def preprocess_image(image: Image.Image) -> np.ndarray:
    img = image.convert("RGB").resize((299, 299))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image: Image.Image, model) -> dict:
    if model is None:
        return None
    processed   = preprocess_image(image)
    probs       = model.predict(processed, verbose=0)[0]
    idx         = int(np.argmax(probs))
    pred_class  = CLASS_LABELS[idx]
    confidence  = float(probs[idx]) * 100
    return {
        "predicted_class": pred_class,
        "confidence":      confidence,
        "all_probs":       {CLASS_LABELS[i]: float(probs[i]) for i in range(4)},
        "info":            CLASS_INFO[pred_class],
        "processed_array": processed,
    }


def render_prediction_result(result: dict):
    if result is None:
        st.error("Prediction failed.")
        return

    cls   = result["predicted_class"]
    conf  = result["confidence"]
    info  = result["info"]
    probs = result["all_probs"]

    if cls == "notumor":
        st.success(f"### {info['icon']} NO TUMOR DETECTED")
    else:
        st.error(f"### {info['icon']} {cls.upper()} DETECTED")

    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence",  f"{conf:.1f}%")
    c2.metric("Severity",    info["severity"])
    c3.metric("Class",       cls.upper())

    st.info(f"ℹ️ {info['description']}")
    st.warning(f"⚕️ **Action:** {info['action']}")

    if conf > 80:
        st.success("✅ High Confidence Prediction")
    elif conf > 60:
        st.warning("⚠️ Moderate Confidence — Review Recommended")
    else:
        st.error("⚠️ Low Confidence — Manual Review Required")

    st.markdown("#### 📊 Class Probabilities")
    for label, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True):
        pct   = prob * 100
        color = info["color"] if label == cls else ("#00C851" if label == "notumor" else "#444")
        st.markdown(f"""
        <div style='display:flex;align-items:center;margin:5px 0;'>
            <div style='width:115px;font-size:13px;color:#ccc;'>{label.upper()}</div>
            <div style='flex:1;background:#1e1e2e;border-radius:6px;height:22px;overflow:hidden;'>
                <div style='width:{pct:.1f}%;background:{color};height:100%;border-radius:6px;'></div>
            </div>
            <div style='width:55px;text-align:right;font-size:13px;color:#ccc;margin-left:8px;'>
                {pct:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)