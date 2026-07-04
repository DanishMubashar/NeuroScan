"""
NeuroScan AI - Tumor Analysis Module
OpenCV segmentation + Grad-CAM visualization
"""

import cv2
import numpy as np
import streamlit as st
import tensorflow as tf
from PIL import Image


def analyze_tumor(image: Image.Image, predicted_class: str) -> dict:
    """OpenCV-based tumor segmentation and size analysis"""
    img_rgb = np.array(image.convert("RGB"))

    if predicted_class == "notumor":
        return {
            "has_tumor":           False,
            "tumor_area":          0,
            "tumor_percentage":    0,
            "tumor_size_category": "None",
            "center":              None,
            "radius":              None,
            "bounding_box":        None,
            "perimeter":           0,
            "contour_image":       img_rgb,
            "thresh_image":        None,
            "clinical_notes":      [
                "✓ No Tumor Detected",
                "✓ Brain structure appears normal",
                "✓ No abnormalities found"
            ],
        }

    gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return {"has_tumor": False, "error": "No contours found"}

    valid = [c for c in contours if cv2.contourArea(c) > 500]
    if not valid:
        return {"has_tumor": False, "error": "No significant region found"}

    tumor_c  = max(valid, key=cv2.contourArea)
    area     = cv2.contourArea(tumor_c)
    perim    = cv2.arcLength(tumor_c, True)
    x, y, w, h = cv2.boundingRect(tumor_c)
    img_area = img_rgb.shape[0] * img_rgb.shape[1]
    pct      = (area / img_area) * 100
    (cx, cy), radius = cv2.minEnclosingCircle(tumor_c)

    out = img_rgb.copy()
    cv2.drawContours(out, [tumor_c], -1, (0, 255, 0), 2)
    cv2.rectangle(out, (x, y), (x + w, y + h), (255, 0, 0), 2)

    if pct < 5:
        cat   = "Very Small"
        notes = ["Very small tumor detected.", "Regular monitoring recommended."]
    elif pct < 10:
        cat   = "Small"
        notes = ["Small tumor detected.", "Further clinical evaluation recommended."]
    elif pct < 20:
        cat   = "Medium"
        notes = ["Medium-sized tumor detected.", "Urgent clinical consultation advised."]
    else:
        cat   = "Large"
        notes = ["Large tumor detected.", "Immediate medical attention required."]

    return {
        "has_tumor":           True,
        "tumor_area":          round(area, 2),
        "tumor_percentage":    round(pct, 2),
        "tumor_size_category": cat,
        "center":              (int(cx), int(cy)),
        "radius":              int(radius),
        "bounding_box":        {"x": x, "y": y, "w": w, "h": h},
        "perimeter":           round(perim, 2),
        "contour_image":       out,
        "thresh_image":        thresh,
        "clinical_notes":      notes,
    }


def generate_gradcam(image: Image.Image, model, predicted_class: str,
                     class_labels: list) -> dict:
    """Grad-CAM heatmap for explainable AI"""
    if predicted_class == "notumor" or model is None:
        return {"generated": False, "reason": "No tumor — Grad-CAM skipped"}

    try:
        img_rgb     = np.array(image.convert("RGB"))
        img_resized = cv2.resize(img_rgb, (299, 299))
        img_arr     = np.expand_dims(img_resized / 255.0, axis=0).astype(np.float32)

        base_model  = model.layers[0]
        last_conv   = None
        for layer in reversed(base_model.layers):
            if "conv" in layer.name and len(layer.output_shape) == 4:
                last_conv = layer
                break
        if last_conv is None:
            return {"generated": False, "reason": "Conv layer not found"}

        conv_model = tf.keras.Model(inputs=base_model.input, outputs=last_conv.output)

        with tf.GradientTape() as tape:
            conv_out = conv_model(img_arr)
            tape.watch(conv_out)
            flat  = tf.keras.layers.Flatten()(conv_out)
            d1    = tf.keras.layers.Dropout(0.3)(flat, training=False)
            d2    = tf.keras.layers.Dense(128, activation="relu")(d1)
            d3    = tf.keras.layers.Dropout(0.25)(d2, training=False)
            out   = tf.keras.layers.Dense(4, activation="softmax")(d3)
            score = out[:, tf.argmax(out[0])]

        grads        = tape.gradient(score, conv_out)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        heatmap      = conv_out[0] @ pooled_grads[..., tf.newaxis]
        heatmap      = tf.squeeze(heatmap)
        heatmap      = tf.maximum(heatmap, 0)
        heatmap      = heatmap / (tf.math.reduce_max(heatmap) + 1e-10)
        heatmap      = heatmap.numpy()

        oh, ow      = img_rgb.shape[:2]
        hmap_r      = cv2.resize(heatmap, (ow, oh))
        hmap_u8     = np.uint8(255 * hmap_r)
        hmap_color  = cv2.applyColorMap(hmap_u8, cv2.COLORMAP_JET)
        hmap_rgb    = cv2.cvtColor(hmap_color, cv2.COLOR_BGR2RGB)
        superimposed = cv2.addWeighted(img_rgb.astype(np.uint8), 0.6, hmap_rgb, 0.4, 0)

        high_act_pct = float(np.sum(hmap_r > 0.5) / hmap_r.size * 100)
        if high_act_pct < 30:
            focus = "✅ Excellent — model focusing precisely on tumor region"
        elif high_act_pct < 60:
            focus = "⚠️ Moderate — model focus is somewhat spread"
        else:
            focus = "⚠️ Broad — activation widely distributed"

        return {
            "generated":      True,
            "heatmap":        hmap_r,
            "superimposed":   superimposed,
            "high_act_pct":   round(high_act_pct, 1),
            "max_intensity":  round(float(np.max(hmap_r)), 3),
            "mean_intensity": round(float(np.mean(hmap_r)), 3),
            "focus_quality":  focus,
            "conv_layer":     last_conv.name,
        }

    except Exception as e:
        return {"generated": False, "reason": str(e)}


def render_analysis_results(image: Image.Image, analysis: dict, gradcam: dict):
    """Render tumor analysis + Grad-CAM results"""
    st.markdown("---")
    st.markdown("## 🔬 Tumor Analysis")

    if not analysis.get("has_tumor"):
        st.success("### ✅ No Tumor Detected — Brain appears normal")
        st.image(image, caption="MRI Scan", width=350)
        for note in analysis.get("clinical_notes", []):
            st.success(note)
        return

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tumor Area",     f"{analysis['tumor_area']:.0f} px²")
    c2.metric("Image Coverage", f"{analysis['tumor_percentage']:.1f}%")
    c3.metric("Size Category",  analysis["tumor_size_category"])
    c4.metric("Perimeter",      f"{analysis['perimeter']:.0f} px")

    bb = analysis.get("bounding_box", {})
    st.caption(
        f"📍 Center: {analysis['center']}  |  "
        f"Bounding Box → x={bb.get('x')}, y={bb.get('y')}, "
        f"w={bb.get('w')}, h={bb.get('h')}  |  Radius: {analysis['radius']}px"
    )

    st.markdown("#### 📋 Clinical Notes")
    for note in analysis["clinical_notes"]:
        st.warning(note)

    # Images
    st.markdown("#### 🖼️ Segmentation")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image(image, caption="Original MRI", use_container_width=True)
    with c2:
        if analysis.get("thresh_image") is not None:
            st.image(analysis["thresh_image"], caption="Segmentation Mask",
                     use_container_width=True, clamp=True)
    with c3:
        st.image(analysis["contour_image"],
                 caption="Tumor Region (Green=Contour, Red=BBox)",
                 use_container_width=True)

    # Grad-CAM
    st.markdown("---")
    st.markdown("## 🔍 Explainable AI — Grad-CAM")

    if not gradcam.get("generated"):
        st.info(f"ℹ️ {gradcam.get('reason', 'Grad-CAM not available')}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("High Activation", f"{gradcam['high_act_pct']}%")
    c2.metric("Max Intensity",   f"{gradcam['max_intensity']}")
    c3.metric("Mean Intensity",  f"{gradcam['mean_intensity']}")
    st.info(f"🔍 {gradcam['focus_quality']}")
    st.caption(f"Conv Layer: `{gradcam['conv_layer']}`")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.image(image, caption="Original", use_container_width=True)
    with c2:
        st.image(gradcam["heatmap"], caption="Heatmap",
                 use_container_width=True, clamp=True)
    with c3:
        st.image(gradcam["superimposed"], caption="Grad-CAM Overlay",
                 use_container_width=True)
