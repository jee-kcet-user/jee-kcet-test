import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "test_history.json"
MAX_Q = 10

def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def parse_mcqs(text):
    lines = text.strip().split("
")
    questions = []
    current = {}
    q_num = 0
    for line in lines:
        line = line.strip()
        if line.startswith("Q") and "." in line:
            if current:
                questions.append(current)
            q_num += 1
            current = {
                "number": q_num,
                "question": line,
                "options": [],
                "answer": "",
                "solution": ""
            }
        elif current:
            if line.startswith("A)") or line.startswith("B)") or line.startswith("C)") or line.startswith("D)"):
                current["options"].append(line)
            elif line.lower().startswith("answer:"):
                current["answer"] = line.split(":", 1)[1].strip().upper()
            elif line.lower().startswith("solution:"):
                current["solution"] = line.split(":", 1)[1].strip()
    if current:
        questions.append(current)
    return questions

def evaluate_test(user_answers, questions):
    total = len(questions)
    correct = 0
    details = []
    for idx, q in enumerate(questions):
        user_choice_idx = user_answers[idx]
        correct_label = q["answer"]
        correct_idx = ord(correct_label) - ord("A")
        is_correct = (user_choice_idx == correct_idx)
        if is_correct:
            correct += 1
        details.append({
            "q_num": q["number"],
            "question": q["question"],
            "options": q["options"],
            "user_choice_idx": user_choice_idx,
            "correct_label": correct_label,
            "is_correct": is_correct,
            "solution": q["solution"]
        })
    percentage = (correct / total * 100) if total > 0 else 0
    return {
        "total": total,
        "correct": correct,
        "percentage": percentage,
        "accuracy": percentage,
        "details": details
    }

def save_test_result(subject, exam, result):
    history = load_history()
    record = {
        "timestamp": datetime.now().isoformat(),
        "subject": subject,
        "exam": exam,
        "total": result["total"],
        "correct": result["correct"],
        "percentage": result["percentage"]
    }
    history.append(record)
    save_history(history)

def compute_analytics():
    history = load_history()
    if not history:
        return "No test records yet. Take a test first."
    best = max(history, key=lambda x: x["percentage"])
    worst = min(history, key=lambda x: x["percentage"])
    subject_stats = {}
    for rec in history:
        subj = rec["subject"]
        if subj not in subject_stats:
            subject_stats[subj] = {"sum": 0.0, "count": 0}
        subject_stats[subj]["sum"] += rec["percentage"]
        subject_stats[subj]["count"] += 1
    subject_avg = {subj: stats["sum"]/stats["count"] for subj, stats in subject_stats.items()}
    best_subject = max(subject_avg.items(), key=lambda x: x[1])
    worst_subject = min(subject_avg.items(), key=lambda x: x[1])
    recent = history[-5:]
    recent_str = "
".join(f"{i+1}. {r['subject']} ({r['exam']}) – {r['percentage']:.1f}%" for i, r in enumerate(recent))
    text = (
        f"Total tests: {len(history)}

"
        f"Best test: {best['subject']} ({best['exam']}) – {best['percentage']:.1f}% ({best['correct']}/{best['total']}) on {best['timestamp'][:10]}
"
        f"Worst test: {worst['subject']} ({worst['exam']}) – {worst['percentage']:.1f}% ({worst['correct']}/{worst['total']}) on {worst['timestamp'][:10]}
"
        f"Best subject: {best_subject[0]} – {best_subject[1]:.1f}%
"
        f"Weakest subject: {worst_subject[0]} – {worst_subject[1]:.1f}%

"
        f"Recent 5 tests:
{recent_str}"
    )
    return text

st.title("JEE + KCET MCQ Test & Analytics Portal")

st.header("1. Paste MCQs (from AI)")
mcq_text = st.text_area("MCQs in required format", height=150,
    placeholder="Q1. ...
A) ...
B) ...
C) ...
D) ...
Answer: A
Solution: ...")

with st.row():
    subject = st.selectbox("Subject", ["Physics", "Chemistry", "Maths"])
    exam = st.selectbox("Exam focus", ["JEE", "KCET", "Both"])

if st.button("Load Quiz"):
    questions = parse_mcqs(mcq_text)
    if not questions:
        st.warning("No valid MCQs. Check format.")
        st.session_state["questions"] = []
    else:
        n = min(len(questions), MAX_Q)
        st.session_state["questions"] = questions[:n]
        st.success(f"Loaded {n} questions. Answer all and click Submit Test.")

if "questions" not in st.session_state:
    st.session_state["questions"] = []

questions = st.session_state["questions"]

if questions:
    st.header("2. Take the Test")
    user_answers = []
    for i, q in enumerate(questions):
        opts = [o[2:].strip() for o in q["options"]]
        ans = st.radio(f"Q{q['number']}. {q['question']}", opts, key=f"q_{i}")
        # Map selected option to index
        if ans is None:
            user_answers.append(None)
        else:
            user_answers.append(opts.index(ans))

    if st.button("Submit Test"):
        if len(user_answers) != len(questions):
            st.warning("Please answer all questions.")
        else:
            result = evaluate_test(user_answers, questions)
            save_test_result(subject, exam, result)
            total = result["total"]
            correct = result["correct"]
            percentage = result["percentage"]
            st.header("Test Result")
            st.write(f"Marks: {correct}/{total}")
            st.write(f"Percentage: {percentage:.1f}%")
            st.write(f"Accuracy: {result['accuracy']:.1f}%")
            st.write("Detailed solutions:")
            for d in result["details"]:
                status = "✓" if d["is_correct"] else "✗"
                ulabel = chr(ord("A")+d["user_choice_idx"]) if d["user_choice_idx"] is not None else "-"
                st.write(f"Q{d['q_num']}: {status} | You: {ulabel} | Correct: {d['correct_label']}")
                st.write(f"Sol: {d['solution']}")
            st.header("Analytics (Best/Worst/Subjects)")
            st.write(compute_analytics())

st.markdown("""
### How to use
1. Ask AI for MCQs in the required format.  
2. Paste them here, choose subject & exam, click **Load Quiz**.  
3. Answer all visible questions and click **Submit Test**.  
4. See marks, percentage, accuracy and full analytics.
""")
