import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # Set slide dimensions to widescreen 16:9
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette Constants
    BG_DARK = RGBColor(15, 23, 42)        # Slate 900 (#0F172A)
    CARD_BG = RGBColor(30, 41, 59)        # Slate 800 (#1E293B)
    CARD_BORDER = RGBColor(51, 65, 85)    # Slate 700 (#334155)
    TEXT_MAIN = RGBColor(248, 250, 252)   # Slate 50 (#F8FAFC)
    TEXT_MUTED = RGBColor(148, 163, 184) # Slate 400 (#94A3B8)
    CYAN_ACCENT = RGBColor(56, 189, 248)  # Cyan 400 (#38BDF8)
    GREEN_ACCENT = RGBColor(16, 185, 129) # Emerald 500 (#10B981)
    RED_ACCENT = RGBColor(239, 68, 68)    # Red 500 (#EF4444)
    AMBER_ACCENT = RGBColor(245, 158, 11) # Amber 500 (#F59E0B)
    BLUE_BG = RGBColor(14, 116, 144)      # Cyan 700 (#0E7490)

    blank_slide_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_DARK

    def add_header(slide, category, title):
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = CYAN_ACCENT
        p_cat.font.name = "Calibri"

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_MAIN
        p_title.font.name = "Calibri"

    def add_card(slide, left, top, width, height, title="", border_color=CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
        
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.5))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(18)
            p.font.bold = True
            p.font.color.rgb = CYAN_ACCENT
            p.font.name = "Calibri"
        return shape

    def add_speaker_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        text_frame.text = notes_text

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide1)

    # Accent banner shape
    banner = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
    banner.fill.solid()
    banner.fill.fore_color.rgb = CYAN_ACCENT
    banner.line.fill.background()

    # Title & Subtitle text box
    tb1 = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "AI-BASED NETWORK INTRUSION DETECTION SYSTEM"
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_MAIN
    p1.font.name = "Calibri"

    p2 = tf1.add_paragraph()
    p2.text = "Production-Grade AI-NIDS Platform Powered by Machine Learning & Real-Time Analytics"
    p2.font.size = Pt(20)
    p2.font.color.rgb = CYAN_ACCENT
    p2.font.name = "Calibri"
    p2.space_before = Pt(15)

    p3 = tf1.add_paragraph()
    p3.text = "Trained on NSL-KDD Benchmark Dataset • Sub-Second Verdict Stream • Automated SOC Alert Management"
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_MUTED
    p3.font.name = "Calibri"
    p3.space_before = Pt(25)

    # Metadata Footer Card
    add_card(slide1, Inches(1.2), Inches(5.3), Inches(10.8), Inches(1.4), border_color=CYAN_ACCENT)
    tb_meta = slide1.shapes.add_textbox(Inches(1.4), Inches(5.45), Inches(10.4), Inches(1.1))
    tf_meta = tb_meta.text_frame
    p_m1 = tf_meta.paragraphs[0]
    p_m1.text = "ARCHITECTURE & IMPLEMENTATION OVERVIEW"
    p_m1.font.size = Pt(14)
    p_m1.font.bold = True
    p_m1.font.color.rgb = GREEN_ACCENT

    p_m2 = tf_meta.add_paragraph()
    p_m2.text = "Tech Stack: React 18 + TypeScript | FastAPI + SQLAlchemy | Scikit-Learn | WebSockets | Docker"
    p_m2.font.size = Pt(13)
    p_m2.font.color.rgb = TEXT_MAIN
    p_m2.space_before = Pt(5)

    add_speaker_notes(slide1, 
        "Welcome to the presentation of the AI-Based Network Intrusion Detection System (AI-NIDS).\n"
        "This project is an enterprise-grade cybersecurity platform that leverages supervised Machine Learning "
        "trained on the NSL-KDD benchmark dataset. It provides real-time traffic analysis, interactive SOC alert triage, "
        "and granular security management."
    )

    # -------------------------------------------------------------
    # SLIDE 2: Executive Summary & Problem Statement
    # -------------------------------------------------------------
    slide2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide2)
    add_header(slide2, "Executive Overview", "Problem Statement & Strategic AI Solution")

    # Card 1: Traditional Challenges
    add_card(slide2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="Traditional NIDS Limitations")
    tb_c1 = slide2.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    bullets_c1 = [
        ("Static Rule-Based Detection: ", "Legacy tools rely on rigid signatures that fail against mutated attack vectors."),
        ("High Alarm Fatigue: ", "Security operations centers (SOCs) are overwhelmed by thousands of false-positive alerts daily."),
        ("Bandwidth Bottlenecks: ", "Manual log inspection cannot scale with gigabit throughput modern corporate networks."),
        ("Slow Incident Response: ", "Lack of real-time streaming verdict engines delays threat containment by hours or days.")
    ]
    for idx, (b_title, b_desc) in enumerate(bullets_c1):
        p = tf_c1.paragraphs[0] if idx == 0 else tf_c1.add_paragraph()
        p.space_after = Pt(12)
        run1 = p.add_run()
        run1.text = "• " + b_title
        run1.font.bold = True
        run1.font.size = Pt(13)
        run1.font.color.rgb = RED_ACCENT
        run2 = p.add_run()
        run2.text = b_desc
        run2.font.size = Pt(13)
        run2.font.color.rgb = TEXT_MUTED

    # Card 2: AI-NIDS Solution
    add_card(slide2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="AI-NIDS Intelligent Solution")
    tb_c2 = slide2.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    bullets_c2 = [
        ("Machine Learning Driven: ", "Classifies network traffic using Random Forest & Decision Tree models with 78% test accuracy."),
        ("High-Precision Attack Verdicts: ", "Achieves 96.68% precision on attack traffic to drastically minimize false positives."),
        ("Real-Time Streaming SOC Dashboard: ", "Sub-second threat verdicts delivered via low-latency WebSocket connections."),
        ("Full Alert Lifecycle Management: ", "Automated severity scoring (CRITICAL, HIGH, MEDIUM) with role-based analyst workflows.")
    ]
    for idx, (b_title, b_desc) in enumerate(bullets_c2):
        p = tf_c2.paragraphs[0] if idx == 0 else tf_c2.add_paragraph()
        p.space_after = Pt(12)
        run1 = p.add_run()
        run1.text = "✔ " + b_title
        run1.font.bold = True
        run1.font.size = Pt(13)
        run1.font.color.rgb = GREEN_ACCENT
        run2 = p.add_run()
        run2.text = b_desc
        run2.font.size = Pt(13)
        run2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide2,
        "Here we contrast traditional legacy NIDS with our AI-NIDS platform.\n"
        "Legacy systems suffer from static rules, high false-positive rates, and slow response times.\n"
        "Our AI-NIDS solution introduces machine learning trained on network flow patterns, providing high precision "
        "(96.68%), real-time WebSocket streaming, and automated alert scoring for SOC analysts."
    )

    # -------------------------------------------------------------
    # SLIDE 3: System Architecture & Data Flow
    # -------------------------------------------------------------
    slide3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide3)
    add_header(slide3, "System Architecture", "End-to-End Full-Stack System Design")

    # 3 Architecture Tier Cards
    col_w = Inches(3.7)
    gap = Inches(0.3)
    
    # Tier 1: Frontend UI
    add_card(slide3, Inches(0.8), Inches(1.6), col_w, Inches(5.2), title="1. React SOC Frontend")
    tb_t1 = slide3.shapes.add_textbox(Inches(1.0), Inches(2.3), col_w - Inches(0.4), Inches(4.3))
    tf_t1 = tb_t1.text_frame
    tf_t1.word_wrap = True
    items_t1 = [
        ("Framework: ", "React 18 + TypeScript + Vite"),
        ("Styling: ", "Tailwind CSS + Glassmorphism"),
        ("Data Visualization: ", "Recharts charts & confusion matrix"),
        ("Live Updates: ", "Native WebSocket client"),
        ("State & Routing: ", "React Router v6 + Axios")
    ]
    for idx, (k, v) in enumerate(items_t1):
        p = tf_t1.paragraphs[0] if idx == 0 else tf_t1.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_MUTED

    # Tier 2: FastAPI Backend & Inference
    add_card(slide3, Inches(0.8) + col_w + gap, Inches(1.6), col_w, Inches(5.2), title="2. FastAPI Backend")
    tb_t2 = slide3.shapes.add_textbox(Inches(1.0) + col_w + gap, Inches(2.3), col_w - Inches(0.4), Inches(4.3))
    tf_t2 = tb_t2.text_frame
    tf_t2.word_wrap = True
    items_t2 = [
        ("REST Engine: ", "FastAPI + Pydantic v2 schemas"),
        ("Real-time Stream: ", "Async WebSocket Manager (`/ws`)"),
        ("ML Inference Engine: ", "Scikit-Learn Joblib Model Pipeline"),
        ("Traffic Adapters: ", "Demo Stream & Scapy PCAP stub"),
        ("Security: ", "OAuth2 + JWT Bearer Tokens")
    ]
    for idx, (k, v) in enumerate(items_t2):
        p = tf_t2.paragraphs[0] if idx == 0 else tf_t2.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_MUTED

    # Tier 3: Database & ML Artifacts
    add_card(slide3, Inches(0.8) + (col_w + gap) * 2, Inches(1.6), col_w, Inches(5.2), title="3. Persistence & Models")
    tb_t3 = slide3.shapes.add_textbox(Inches(1.0) + (col_w + gap) * 2, Inches(2.3), col_w - Inches(0.4), Inches(4.3))
    tf_t3 = tb_t3.text_frame
    tf_t3.word_wrap = True
    items_t3 = [
        ("ORM Layer: ", "SQLAlchemy with Session management"),
        ("Storage Engine: ", "SQLite (dev) / PostgreSQL (prod)"),
        ("Model Artifacts: ", "Serialized Joblib binary `.pkl` files"),
        ("Audit Logs: ", "Persisted DB user activity records"),
        ("Container Stack: ", "Docker Compose containerization")
    ]
    for idx, (k, v) in enumerate(items_t3):
        p = tf_t3.paragraphs[0] if idx == 0 else tf_t3.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = AMBER_ACCENT
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide3,
        "The architecture is modularly separated into three tiers:\n"
        "1. React 18 TypeScript frontend providing an interactive SOC security dashboard with Recharts visualizer.\n"
        "2. FastAPI Python backend running Uvicorn ASGI, serving REST APIs and low-latency WebSockets.\n"
        "3. Scikit-learn inference pipeline using joblib artifacts backed by SQLite or PostgreSQL."
    )

    # -------------------------------------------------------------
    # SLIDE 4: NSL-KDD Dataset & Feature Engineering
    # -------------------------------------------------------------
    slide4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide4)
    add_header(slide4, "Data Pipeline", "NSL-KDD Benchmark Dataset & Feature Selection")

    add_card(slide4, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="NSL-KDD Dataset Characteristics")
    tb_d1 = slide4.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_d1 = tb_d1.text_frame
    tf_d1.word_wrap = True
    bullets_d1 = [
        ("Standardized Benchmark: ", "Solves legacy KDD'99 redundant records issue, ensuring unbiased training & evaluation."),
        ("Dataset Volumes: ", "125,973 training samples; 22,544 independent test set samples."),
        ("Multi-Class Diversity: ", "Includes Normal traffic plus 4 attack categories: DoS, Probe, R2L, and U2R."),
        ("Realistic Evaluation: ", "Test dataset contains novel attack sub-variants not present in the training set.")
    ]
    for idx, (b_title, b_desc) in enumerate(bullets_d1):
        p = tf_d1.paragraphs[0] if idx == 0 else tf_d1.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide4, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="Top 20 Selected Features (Feature Selector)")
    tb_d2 = slide4.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_d2 = tb_d2.text_frame
    tf_d2.word_wrap = True
    
    feats = [
        "1. src_bytes & dst_bytes", "2. protocol_type (TCP/UDP/ICMP)",
        "3. service & flag", "4. logged_in status",
        "5. count & srv_count", "6. serror_rate & srv_serror_rate",
        "7. same_srv_rate & diff_srv_rate", "8. dst_host_count & dst_host_srv_count",
        "9. dst_host_same_srv_rate", "10. dst_host_diff_srv_rate",
        "11. dst_host_srv_diff_host_rate", "12. dst_host_serror_rate"
    ]
    p_f_intro = tf_d2.paragraphs[0]
    p_f_intro.text = "20 Discriminative Features Extracted from 41 Raw Attributes:"
    p_f_intro.font.size = Pt(13)
    p_f_intro.font.bold = True
    p_f_intro.font.color.rgb = TEXT_MAIN
    p_f_intro.space_after = Pt(8)

    for f in feats:
        p = tf_d2.add_paragraph()
        p.text = "▸ " + f
        p.font.size = Pt(12)
        p.font.color.rgb = GREEN_ACCENT
        p.space_after = Pt(4)

    add_speaker_notes(slide4,
        "We utilize the official NSL-KDD benchmark dataset, which addresses the duplication issues of raw KDD Cup 99.\n"
        "Our pipeline extracts 20 top discriminative features from 41 raw attributes, covering packet sizes, "
        "connection counts, error rates (serror_rate), and host service rates."
    )

    # -------------------------------------------------------------
    # SLIDE 5: Machine Learning Models & Training Pipeline
    # -------------------------------------------------------------
    slide5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide5)
    add_header(slide5, "Machine Learning", "Model Selection & Offline Training Pipeline")

    add_card(slide5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="Random Forest Classifier (Primary)")
    tb_m1 = slide5.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_m1 = tb_m1.text_frame
    tf_m1.word_wrap = True
    b_m1 = [
        ("Ensemble Strategy: ", "Combines multiple decision trees via bootstrap aggregation (bagging)."),
        ("Overfitting Resilience: ", "Sub-samples feature spaces to maintain generalization on unseen test traffic."),
        ("Feature Importance: ", "Generates Gini impurity reduction scores to rank connection indicators."),
        ("Status: ", "SELECTED AS BEST MODEL (Highest overall accuracy & precision).")
    ]
    for idx, (b_title, b_desc) in enumerate(b_m1):
        p = tf_m1.paragraphs[0] if idx == 0 else tf_m1.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide5, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="Decision Tree Classifier (Baseline)")
    tb_m2 = slide5.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_m2 = tb_m2.text_frame
    tf_m2.word_wrap = True
    b_m2 = [
        ("Single Tree Architecture: ", "Executes recursive binary splitting based on entropy & information gain."),
        ("Ultra-Fast Inference: ", "Low computational overhead with sub-millisecond execution times."),
        ("Interpretability: ", "Rule paths can be audited directly by cybersecurity analysts."),
        ("Status: ", "Evaluated as baseline comparison model.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_m2):
        p = tf_m2.paragraphs[0] if idx == 0 else tf_m2.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide5,
        "We implemented and evaluated two supervised classification algorithms:\n"
        "1. Random Forest Classifier: An ensemble model providing superior accuracy and high precision by combining decision trees.\n"
        "2. Decision Tree Classifier: A fast baseline model useful for rapid rule verification and low latency."
    )

    # -------------------------------------------------------------
    # SLIDE 6: Model Performance & Evaluation Metrics
    # -------------------------------------------------------------
    slide6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide6)
    add_header(slide6, "Performance Analytics", "Empirical Model Evaluation on NSL-KDD Test Set")

    # Table of Results
    rows, cols = 3, 6
    left, top, width, height = Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.0)
    table_shape = slide6.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    headers = ["Model Classifier", "Accuracy", "Precision", "Recall", "F1-Score", "Production Status"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = CYAN_ACCENT
        p.alignment = PP_ALIGN.CENTER

    data = [
        ["Random Forest", "78.00%", "96.68%", "63.53%", "76.68%", "SELECTED BEST"],
        ["Decision Tree", "75.96%", "96.13%", "60.19%", "74.03%", "Evaluated"]
    ]

    for row_idx, row_data in enumerate(data):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            if row_idx == 0:
                cell.fill.fore_color.rgb = RGBColor(15, 45, 75)
            else:
                cell.fill.fore_color.rgb = CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(13)
            p.font.color.rgb = GREEN_ACCENT if (row_idx == 0 and col_idx == 5) else TEXT_MAIN
            p.font.bold = (row_idx == 0)
            p.alignment = PP_ALIGN.CENTER

    # Key Highlights Card below table
    add_card(slide6, Inches(0.8), Inches(3.9), Inches(11.7), Inches(2.9), title="Key Performance Takeaways")
    tb_p1 = slide6.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.3), Inches(2.2))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    takeaways = [
        ("High Attack Precision (96.68%): ", "Crucial for enterprise SOCs—when AI-NIDS flags an attack, it is nearly 97% accurate, eliminating false alarm noise."),
        ("Test Set Challenge: ", "Evaluated on 22,544 test samples containing unknown attack variants; Random Forest demonstrated strong generalization."),
        ("Balanced Trade-off: ", "Random Forest outperforms Decision Tree across all metrics (+2.04% Accuracy, +3.34% Recall, +2.65% F1-Score).")
    ]
    for idx, (t_head, t_body) in enumerate(takeaways):
        p = tf_p1.paragraphs[0] if idx == 0 else tf_p1.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = "▸ " + t_head
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = t_body
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide6,
        "Here are the test results evaluated on 22,544 official NSL-KDD test samples.\n"
        "Random Forest achieved 78.00% accuracy and an impressive 96.68% precision.\n"
        "High precision is vital in cybersecurity because false positives ruin SOC productivity."
    )

    # -------------------------------------------------------------
    # SLIDE 7: Real-Time Traffic Stream & WebSockets
    # -------------------------------------------------------------
    slide7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide7)
    add_header(slide7, "Real-Time Engine", "Live Streaming Architecture via WebSockets")

    add_card(slide7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="WebSocket Streaming Architecture")
    tb_ws1 = slide7.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_ws1 = tb_ws1.text_frame
    tf_ws1.word_wrap = True
    b_ws1 = [
        ("Full-Duplex Endpoint (`/ws`): ", "Persistent connection broadcasting JSON event frames every 2 seconds."),
        ("Asynchronous Connection Manager: ", "Manages client sockets concurrently without blocking server event loops."),
        ("Automatic Record Persistence: ", "Each stream packet is logged to DB with ML verdict and confidence scores."),
        ("Low-Latency Telemetry: ", "Pushes live traffic metrics straight to Recharts frontend visualizers.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_ws1):
        p = tf_ws1.paragraphs[0] if idx == 0 else tf_ws1.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="Traffic Adapter Engine")
    tb_ws2 = slide7.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_ws2 = tb_ws2.text_frame
    tf_ws2.word_wrap = True
    b_ws2 = [
        ("Demo Traffic Adapter (`DemoTrafficAdapter`): ", "Generates realistic network packets with configurable attack ratio (default 30-35%)."),
        ("Live Packet Adapter Stub (`PacketCaptureAdapter`): ", "Scapy integration harness for sniffing real network interface hardware."),
        ("Severity Categorization: ", "Automatic severity scoring based on attack verdict confidence:"),
        ("  - Confidence ≥ 90%: ", "CRITICAL Severity (Red Alert)"),
        ("  - Confidence ≥ 80%: ", "HIGH Severity (Amber Alert)"),
        ("  - Confidence < 80%: ", "MEDIUM / LOW Severity")
    ]
    for idx, (b_title, b_desc) in enumerate(b_ws2):
        p = tf_ws2.paragraphs[0] if idx == 0 else tf_ws2.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = b_title
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = GREEN_ACCENT if "CRITICAL" in b_title else (AMBER_ACCENT if "HIGH" in b_title else CYAN_ACCENT)
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide7,
        "The real-time streaming engine uses WebSockets (/ws) managed asynchronously by FastAPI.\n"
        "It supports dual adapters: a Demo Traffic Adapter generating continuous streams with controllable attack ratios, "
        "and a Packet Capture Adapter stub. Live packets receive immediate confidence scoring and severity tagging."
    )

    # -------------------------------------------------------------
    # SLIDE 8: Interactive Test Bench & Presets
    # -------------------------------------------------------------
    slide8 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide8)
    add_header(slide8, "Analyst Tools", "Interactive Detection Test Bench & Presets")

    add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="Custom Vector Simulation")
    tb_tb1 = slide8.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_tb1 = tb_tb1.text_frame
    tf_tb1.word_wrap = True
    b_tb1 = [
        ("Manual Vector Inputs: ", "Form bench enabling analysts to enter exact 20-feature parameter sets."),
        ("Immediate Inference: ", "Executes instant REST API prediction call (`/api/v1/detection/predict`)."),
        ("Probability Breakdown: ", "Displays probability distribution (e.g. 98.4% ATTACK vs 1.6% NORMAL)."),
        ("Model Switching: ", "Allows analysts to toggle between Random Forest and Decision Tree on the fly.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_tb1):
        p = tf_tb1.paragraphs[0] if idx == 0 else tf_tb1.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="One-Click Attack Presets")
    tb_tb2 = slide8.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_tb2 = tb_tb2.text_frame
    tf_tb2.word_wrap = True
    b_tb2 = [
        ("⚡ DoS SYN Flood Attack: ", "High packet count, serror_rate = 1.0, protocol = TCP, same_srv_rate = 1.0."),
        ("🔍 Port Sweep Probe Attack: ", "High diff_srv_rate, low same_srv_rate, multiple distinct destination ports."),
        ("🌐 Normal HTTP Session: ", "Standard HTTP bytes, logged_in = 1, normal error rates, legitimate traffic profile.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_tb2):
        p = tf_tb2.paragraphs[0] if idx == 0 else tf_tb2.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = AMBER_ACCENT if "Probe" in b_title else (RED_ACCENT if "Flood" in b_title else GREEN_ACCENT)
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide8,
        "The Interactive Detection Test Bench lets security researchers test custom traffic vectors.\n"
        "It includes one-click attack presets like DoS SYN Flood, Port Sweep Probe, and Normal HTTP traffic, "
        "allowing immediate verification of model feature responses."
    )

    # -------------------------------------------------------------
    # SLIDE 9: SOC Alert Management & RBAC Security
    # -------------------------------------------------------------
    slide9 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide9)
    add_header(slide9, "Security & Operations", "SOC Alert Triage & Role-Based Access Control")

    add_card(slide9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="SOC Alert Lifecycle Management")
    tb_s1 = slide9.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_s1 = tb_s1.text_frame
    tf_s1.word_wrap = True
    b_s1 = [
        ("Automated Alert Triggering: ", "Attacks with high confidence instantly create alert tickets in the database."),
        ("Lifecycle Transitions: ", "OPEN ➔ ACKNOWLEDGED ➔ RESOLVED."),
        ("Analyst Workflow: ", "Allows analysts to add investigation notes and assign ownership."),
        ("Filtering & Search: ", "Filter alerts by severity (`CRITICAL`, `HIGH`), status, and protocol.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_s1):
        p = tf_s1.paragraphs[0] if idx == 0 else tf_s1.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="RBAC & Audit Compliance")
    tb_s2 = slide9.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_s2 = tb_s2.text_frame
    tf_s2.word_wrap = True
    b_s2 = [
        ("ADMIN Role: ", "Full operational control, user management, alert resolution, system config."),
        ("ANALYST Role: ", "Live traffic monitoring, manual predictions, alert acknowledgment."),
        ("VIEWER Role: ", "Read-only access to dashboards and metrics."),
        ("Audit Logging: ", "Immutable database log recording login attempts, alert updates, and model retrains.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_s2):
        p = tf_s2.paragraphs[0] if idx == 0 else tf_s2.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "🔑 " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide9,
        "Security operations require strict governance. AI-NIDS features alert lifecycle management "
        "and granular Role-Based Access Control (RBAC) backed by JWT tokens and audit logs."
    )

    # -------------------------------------------------------------
    # SLIDE 10: DevOps, Containerization & Testing
    # -------------------------------------------------------------
    slide10 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide10)
    add_header(slide10, "DevOps & Quality", "Containerization, Deployment & Automated Testing")

    add_card(slide10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="Docker Container Stack")
    tb_dv1 = slide10.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_dv1 = tb_dv1.text_frame
    tf_dv1.word_wrap = True
    b_dv1 = [
        ("Multi-Stage Dockerfile: ", "Optimized container build for FastAPI Python environment."),
        ("Docker Compose Orchestration: ", "Seamlessly spins up Backend, Frontend, and PostgreSQL database."),
        ("Environment Isolation: ", "Configured via `.env` files for seamless dev, staging, and production deployment.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_dv1):
        p = tf_dv1.paragraphs[0] if idx == 0 else tf_dv1.add_paragraph()
        p.space_after = Pt(16)
        r1 = p.add_run()
        r1.text = "🐳 " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="Automated Quality Assurance")
    tb_dv2 = slide10.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_dv2 = tb_dv2.text_frame
    tf_dv2.word_wrap = True
    b_dv2 = [
        ("Pytest Test Suite: ", "Comprehensive unit & integration tests (`test_sql_app.db`)."),
        ("API Endpoint Testing: ", "Validates auth endpoints, prediction schemas, and alert queries."),
        ("Schema Validation: ", "Strict Pydantic v2 data validation prevents malformed payload errors.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_dv2):
        p = tf_dv2.paragraphs[0] if idx == 0 else tf_dv2.add_paragraph()
        p.space_after = Pt(16)
        r1 = p.add_run()
        r1.text = "🧪 " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide10,
        "The project is production-ready with Docker containerization and automated Pytest test suites, "
        "ensuring easy deployment across cloud or on-premise environments."
    )

    # -------------------------------------------------------------
    # SLIDE 11: Technical Challenges & Strategic Roadmap
    # -------------------------------------------------------------
    slide11 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide11)
    add_header(slide11, "Future Vision", "Technical Limitations & Multi-Phase Roadmap")

    add_card(slide11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="Technical Limitations")
    tb_r1 = slide11.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf_r1 = tb_r1.text_frame
    tf_r1.word_wrap = True
    b_r1 = [
        ("Supervised ML Horizon: ", "Supervised models target known attack patterns; novel zero-day exploits require anomaly detection."),
        ("Benchmark Dataset Scope: ", "NSL-KDD provides solid baseline features, but real enterprise deployments require continuous online retraining."),
        ("Packet Privileges: ", "Raw PCAP packet capture requires elevated OS admin/root rights.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_r1):
        p = tf_r1.paragraphs[0] if idx == 0 else tf_r1.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = "⚠️ " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = AMBER_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_card(slide11, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="Future Product Roadmap")
    tb_r2 = slide11.shapes.add_textbox(Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.3))
    tf_r2 = tb_r2.text_frame
    tf_r2.word_wrap = True
    b_r2 = [
        ("Phase 4 - Zero-Day Detection: ", "Unsupervised Autoencoders for anomaly detection."),
        ("Phase 5 - Temporal Analysis: ", "LSTM / GRU Neural Networks for flow sequence modeling."),
        ("Phase 6 - SIEM Integration: ", "Syslog & CEF log forwarding to Splunk / Elastic."),
        ("Phase 7 - Automated Defense: ", "Automated API hooks for firewall IP blocking.")
    ]
    for idx, (b_title, b_desc) in enumerate(b_r2):
        p = tf_r2.paragraphs[0] if idx == 0 else tf_r2.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = "🚀 " + b_title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide11,
        "We maintain transparency regarding current technical limits and outline a strategic roadmap "
        "including Deep Learning LSTM models, Unsupervised Autoencoders for zero-day threats, and automated firewall hooks."
    )

    # -------------------------------------------------------------
    # SLIDE 12: Conclusion & Q&A
    # -------------------------------------------------------------
    slide12 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide12)

    banner12 = slide12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
    banner12.fill.solid()
    banner12.fill.fore_color.rgb = GREEN_ACCENT
    banner12.line.fill.background()

    tb12 = slide12.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(11.0), Inches(4.5))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    p_c1 = tf12.paragraphs[0]
    p_c1.text = "AI-BASED NETWORK INTRUSION DETECTION SYSTEM"
    p_c1.font.size = Pt(30)
    p_c1.font.bold = True
    p_c1.font.color.rgb = TEXT_MAIN

    p_c2 = tf12.add_paragraph()
    p_c2.text = "Empowering Enterprise Security Operations with High-Precision Machine Learning"
    p_c2.font.size = Pt(20)
    p_c2.font.color.rgb = CYAN_ACCENT
    p_c2.space_before = Pt(15)

    add_card(slide12, Inches(1.2), Inches(3.4), Inches(10.8), Inches(3.3), title="Summary of Project Accomplishments")
    tb_c_box = slide12.shapes.add_textbox(Inches(1.4), Inches(4.1), Inches(10.4), Inches(2.4))
    tf_c_box = tb_c_box.text_frame
    tf_c_box.word_wrap = True
    
    summary_points = [
        "High-Precision Classification: 96.68% attack precision minimizes SOC triage overhead.",
        "Real-Time WebSocket Stream: Low-latency continuous threat scoring and alert scoring.",
        "Full Stack Architecture: Production-ready React 18 frontend & FastAPI backend with Docker support.",
        "Thank You for your time! Questions & Discussion."
    ]
    for idx, sp in enumerate(summary_points):
        p = tf_c_box.paragraphs[0] if idx == 0 else tf_c_box.add_paragraph()
        p.space_after = Pt(10)
        r = p.add_run()
        r.text = "✔ " + sp if idx < 3 else "❓ " + sp
        r.font.size = Pt(14)
        r.font.bold = (idx == 3)
        r.font.color.rgb = GREEN_ACCENT if idx < 3 else CYAN_ACCENT

    add_speaker_notes(slide12,
        "Thank you for attending this presentation on AI-NIDS.\n"
        "We are now open for questions and technical discussion."
    )

    output_path = "AI_NIDS_Project_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_presentation()
