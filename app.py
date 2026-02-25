import streamlit as st
import sqlite3
import hashlib
import os

# ---------------- DATABASE ----------------
conn = sqlite3.connect("app.db", check_same_thread=False)
c = conn.cursor()

# Create Users Table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user',
    approved INTEGER DEFAULT 0
)
""")

# Create Properties Table
c.execute("""
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    image_path TEXT,
    owner TEXT
)
""")
conn.commit()

# ---------------- CREATE DEFAULT ADMIN ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

c.execute("SELECT * FROM users WHERE username=?", ("admin",))
admin_exists = c.fetchone()

if not admin_exists:
    c.execute(
        "INSERT INTO users (username, password, role, approved) VALUES (?, ?, ?, ?)",
        ("admin", hash_password("admin123"), "admin", 1)
    )
    conn.commit()

# ---------------- FUNCTIONS ----------------
def register_user(username, password):
    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()

def approve_user(user_id):
    c.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
    conn.commit()

def save_property(title, description, image, owner):
    if not os.path.exists("images"):
        os.makedirs("images")

    image_path = os.path.join("images", image.name)
    with open(image_path, "wb") as f:
        f.write(image.getbuffer())

    c.execute(
        "INSERT INTO properties (title, description, image_path, owner) VALUES (?, ?, ?, ?)",
        (title, description, image_path, owner)
    )
    conn.commit()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

st.title("🏠 Real Estate Listing App")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- REGISTER ----------------
if choice == "Register":
    st.subheader("Register")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        if new_user and new_pass:
            if register_user(new_user, new_pass):
                st.success("Registered successfully! Wait for admin approval.")
            else:
                st.error("Username already exists.")
        else:
            st.warning("Please fill all fields.")

# ---------------- LOGIN ----------------
if choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            if user[4] == 1:
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.warning("Your account is pending admin approval.")
        else:
            st.error("Invalid username or password.")

# ---------------- AFTER LOGIN ----------------
if st.session_state.user:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as: {user[1]}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # -------- ADMIN PANEL --------
    if user[3] == "admin":
        st.header("Admin Panel - Approve Users")

        c.execute("SELECT * FROM users WHERE approved=0")
        pending = c.fetchall()

        if pending:
            for u in pending:
                col1, col2 = st.columns([3,1])
                col1.write(f"User: {u[1]}")
                if col2.button("Approve", key=u[0]):
                    approve_user(u[0])
                    st.success(f"{u[1]} approved!")
                    st.rerun()
        else:
            st.info("No pending users.")

    # -------- ADD PROPERTY --------
    st.header("Add Property")
    title = st.text_input("Property Title")
    description = st.text_area("Property Description")
    image = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    if st.button("Add Property"):
        if title and description and image:
            save_property(title, description, image, user[1])
            st.success("Property added successfully!")
        else:
            st.warning("Please complete all fields.")

    # -------- VIEW PROPERTIES --------
    st.header("Property Listings")
    c.execute("SELECT * FROM properties")
    properties = c.fetchall()

    for prop in properties:
        st.subheader(prop[1])
        st.write(prop[2])
        if os.path.exists(prop[3]):
            st.image(prop[3], width=300)
        st.caption(f"Posted by: {prop[4]}")
        st.markdown("---")
