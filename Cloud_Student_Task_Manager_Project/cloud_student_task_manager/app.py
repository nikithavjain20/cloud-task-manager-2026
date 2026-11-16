import streamlit as st
from supabase import create_client, Client
from datetime import date

st.set_page_config(page_title="Cloud Student Task Manager", page_icon="☁️", layout="wide")

st.markdown("""
<style>
.main {background-color:#f5f8ff;}
.block-container {padding-top:2rem;}
.hero {background:linear-gradient(120deg,#153e75,#2874c7);padding:25px;border-radius:16px;color:white;}
.hero h1 {color:white;margin:0;}
.hero p {color:#eaf2ff;margin-bottom:0;}
div[data-testid="stMetric"] {background:white;padding:15px;border-radius:12px;border:1px solid #e5eaf4;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>☁️ Cloud Student Task Manager</h1>
  <p>Organise assignments, track deadlines and manage your academic tasks from anywhere.</p>
</div>
""", unsafe_allow_html=True)

def connect_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase: Client = connect_supabase()

if not supabase:
    st.error("Cloud database is not configured yet. Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets. Follow README.md.")
    st.stop()

def get_tasks():
    response = supabase.table("tasks").select("*").order("created_at", desc=True).execute()
    return response.data or []

def show_error(err):
    st.error(f"Database operation failed: {err}")

# Sidebar: create a task
with st.sidebar:
    st.header("➕ Add a task")
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Task title", placeholder="e.g. Complete Cloud Computing report")
        subject = st.text_input("Subject / category", placeholder="e.g. Cloud Computing")
        due_date = st.date_input("Due date", value=date.today())
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submitted = st.form_submit_button("Add task", use_container_width=True)
        if submitted:
            if not title.strip():
                st.warning("Please enter a task title.")
            else:
                try:
                    supabase.table("tasks").insert({
                        "title": title.strip(),
                        "subject": subject.strip(),
                        "due_date": due_date.isoformat(),
                        "priority": priority,
                        "completed": False
                    }).execute()
                    st.success("Task added to the cloud database.")
                    st.rerun()
                except Exception as e:
                    show_error(e)

try:
    tasks = get_tasks()
except Exception as e:
    show_error(e)
    st.stop()

total = len(tasks)
completed = sum(1 for t in tasks if t.get("completed"))
pending = total - completed
overdue = sum(1 for t in tasks if not t.get("completed") and t.get("due_date") and t["due_date"] < date.today().isoformat())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total tasks", total)
m2.metric("Completed", completed)
m3.metric("Pending", pending)
m4.metric("Overdue", overdue)

st.subheader("📋 Your tasks")
search = st.text_input("Search by task or subject", placeholder="Type to filter tasks...")
filter_status = st.selectbox("Show", ["All tasks", "Pending only", "Completed only"])

filtered = tasks
if search:
    s = search.lower()
    filtered = [t for t in filtered if s in (t.get("title") or "").lower() or s in (t.get("subject") or "").lower()]
if filter_status == "Pending only":
    filtered = [t for t in filtered if not t.get("completed")]
elif filter_status == "Completed only":
    filtered = [t for t in filtered if t.get("completed")]

if not filtered:
    st.info("No tasks found. Add your first task using the form in the sidebar.")
else:
    for task in filtered:
        with st.container(border=True):
            left, middle, right = st.columns([5, 2, 2])
            with left:
                mark = "✅" if task.get("completed") else "🕒"
                st.markdown(f"**{mark} {task.get('title','Untitled')}**")
                st.caption(f"{task.get('subject') or 'General'}  •  Due: {task.get('due_date') or 'Not set'}  •  Priority: {task.get('priority') or 'Medium'}")
            with middle:
                new_state = st.checkbox("Completed", value=bool(task.get("completed")), key=f"done_{task['id']}")
                if new_state != bool(task.get("completed")):
                    try:
                        supabase.table("tasks").update({"completed": new_state}).eq("id", task["id"]).execute()
                        st.rerun()
                    except Exception as e:
                        show_error(e)
            with right:
                if st.button("🗑 Delete", key=f"del_{task['id']}", use_container_width=True):
                    try:
                        supabase.table("tasks").delete().eq("id", task["id"]).execute()
                        st.rerun()
                    except Exception as e:
                        show_error(e)

st.divider()
st.caption("Cloud Student Task Manager • Built with Python, Streamlit and Supabase • Access your tasks through a web browser.")
