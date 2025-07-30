#!/usr/bin/env python3

import os
import json
import hashlib
import getpass
import datetime
import argparse
from argparse import RawTextHelpFormatter
import sys

# Constants
BASE_DIR = os.path.expanduser("~/.termux_remember")
USER_FILE = os.path.join(BASE_DIR, "user.json")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

# Ensure base folder exists
os.makedirs(BASE_DIR, exist_ok=True)

version = "1.1.0"  # Updated version
author = "Mallik Mohammad Musaddiq"
email = "mallikmusaddiq1@gmail.com"
github = "https://github.com/mallikmusaddiq1/termux-remember"

# Utils
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Auth
class AuthManager:
    def __init__(self):
        self.user_data = load_json(USER_FILE)

    def signup(self):
        email = input("Enter your email: ").strip()
        password = getpass.getpass("Create password: ")
        password_hash = hash_password(password)
        self.user_data = {
            "email": email,
            "password_hash": password_hash,
            "session_active": False
        }
        save_json(USER_FILE, self.user_data)
        print("✅ Signup complete. Now login to start using termux-remember.")

    def login(self):
        if not self.user_data:
            print("❌ No account found. Run --signup first.")
            return False
        password = getpass.getpass("Enter password: ")
        if hash_password(password) == self.user_data.get("password_hash"):
            self.user_data["session_active"] = True
            save_json(USER_FILE, self.user_data)
            print("✅ Logged in successfully.")
            return True
        else:
            print("❌ Incorrect password.")
            return False

    def logout(self):
        self.user_data["session_active"] = False
        save_json(USER_FILE, self.user_data)
        print("👋 Logged out.")

    def is_logged_in(self):
        return self.user_data.get("session_active", False)

    def verify_password(self):
        password = getpass.getpass("Confirm password: ")
        return hash_password(password) == self.user_data.get("password_hash")

# Memory
class MemoryManager:
    def __init__(self):
        self.memory_data = load_json(MEMORY_FILE)
        self.auth = AuthManager()

    def add_memory(self, text=None, tag=None, password_protected=False):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        if text is None:  # Interactive note input
            print("""Enter your note:

For single-line notes, type your note and press Enter.

For multi-line notes, type each line and end with 'EOF' on a new line.

Use \\n with single-line input for newlines (e.g., 'Line1\\nLine2').
""")
            lines = []
            first_line = input("Note: ").strip()
            if not first_line:  # Handle empty first line
                print("❌ Note cannot be empty.")
                return
            if first_line == "EOF":  # Handle immediate EOF
                print("❌ Note cannot be empty.")
                return
            if "\\n" in first_line:  # Handle \n in single-line input
                text = first_line.replace("\\n", "\n")
            else:
                lines.append(first_line)
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                text = "\n".join(lines).strip()
        if not text:
            print("❌ Note cannot be empty.")
            return
        note_id = str(len(self.memory_data) + 1)
        entry = {
            "id": note_id,
            "text": text,
            "tag": tag,
            "timestamp": str(datetime.datetime.now()),
            "password_protected": password_protected
        }
        self.memory_data[note_id] = entry
        save_json(MEMORY_FILE, self.memory_data)
        print(f"✅ Note saved with ID {note_id}. 📁 Path: {MEMORY_FILE}")

    def list_notes(self):
        if not self.auth.is_logged_in():
            print("🔐 Please login first.")
            return
        for note_id, entry in self.memory_data.items():
            locked = "🔐" if entry.get("password_protected") else ""
            preview = entry['text'].split('\n')[0][:50]
            if len(entry['text'].split('\n')[0]) > 50:
                preview += "..."
            display_text = "******" if entry.get("password_protected") else preview
            print(f"[{note_id}] {entry['tag'] or ''} {display_text} {locked}")

    def find_notes(self, keyword):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        for note_id, entry in self.memory_data.items():
            count = entry['text'].lower().count(keyword.lower())
            preview = entry['text'].split('\n')[0][:50]
            if len(entry['text'].split('\n')[0]) > 50:
                preview += "..."
            if entry.get("password_protected"):
                print(f"[{note_id}] ****** (keyword \"{keyword}\" repeats {count} times)")
            else:
                print(f"[{note_id}] {preview} (keyword \"{keyword}\" repeats {count} times)")

    def view_note(self, note_id):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        note = self.memory_data.get(note_id)
        if not note:
            print("❌ Note not found.")
            return
        if note.get("password_protected") and not self.auth.verify_password():
            print("❌ Incorrect password.")
            return
        print(f"📄 [{note_id}] {note['text']} (Tag: {note.get('tag')})")

    def show_notes_by_tag(self, tag):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        found = False
        for note_id, entry in self.memory_data.items():
            if entry.get("tag") == tag:
                locked = "🔐" if entry.get("password_protected") else ""
                preview = entry['text'].split('\n')[0][:50]
                if len(entry['text'].split('\n')[0]) > 50:
                    preview += "..."
                print(f"[{note_id}] {preview} {locked}")
                found = True
        if not found:
            print(f"🔎 No notes found with tag '{tag}'.")

    def retag_note(self, note_id, new_tag):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        note = self.memory_data.get(note_id)
        if not note:
            print("❌ Note not found.")
            return
        note["tag"] = new_tag
        save_json(MEMORY_FILE, self.memory_data)
        print(f"🏷️ Note {note_id} updated with new tag '{new_tag}'.")

    def delete_note(self, note_id):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        if not self.auth.verify_password():
            print("❌ Password verification failed.")
            return
        if note_id in self.memory_data:
            del self.memory_data[note_id]
            save_json(MEMORY_FILE, self.memory_data)
            print(f"🗑️ Note {note_id} deleted.")
        else:
            print("❌ Note ID not found.")

    def delete_all_notes(self):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        confirm = input("Are you sure you want to delete all notes? (yes/no): ")
        if confirm.lower() == 'yes' and self.auth.verify_password():
            self.memory_data = {}
            save_json(MEMORY_FILE, self.memory_data)
            print("🔥 All notes deleted.")
        else:
            print("❎ Deletion cancelled or wrong password.")

    def delete_all_tags(self):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        confirm = input("Are you sure you want to remove all tags from all notes? (yes/no): ")
        if confirm.lower() == 'yes' and self.auth.verify_password():
            for note_id, entry in self.memory_data.items():
                entry["tag"] = None
            save_json(MEMORY_FILE, self.memory_data)
            print("🏷️ All tags removed from all notes.")
        else:
            print("❎ Tag deletion cancelled or wrong password.")

    def delete_specific_tag(self, tag):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        confirm = input(f"Are you sure you want to remove the tag '{tag}' from all notes? (yes/no): ")
        if confirm.lower() == 'yes' and self.auth.verify_password():
            found = False
            for note_id, entry in self.memory_data.items():
                if entry.get("tag") == tag:
                    entry["tag"] = None
                    found = True
            save_json(MEMORY_FILE, self.memory_data)
            if found:
                print(f"🏷️ Tag '{tag}' removed from all notes.")
            else:
                print(f"🔎 No notes found with tag '{tag}'.")
        else:
            print("❎ Tag deletion cancelled or wrong password.")

    def remove_note_tag(self, note_id):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        note = self.memory_data.get(note_id)
        if not note:
            print("❌ Note not found.")
            return
        if not self.auth.verify_password():
            print("❌ Password verification failed.")
            return
        if note.get("tag") is None:
            print(f"❎ Note {note_id} has no tag to remove.")
            return
        note["tag"] = None
        save_json(MEMORY_FILE, self.memory_data)
        print(f"🏷️ Tag removed from note {note_id}.")

    def list_tags(self):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        tags = set(entry.get("tag") for entry in self.memory_data.values() if entry.get("tag"))
        if not tags:
            print("🔎 No tags found.")
            return
        print("🏷️ Available tags:")
        for tag in sorted(tags):
            print(f"- {tag}")

    def edit_note(self, note_id, new_text=None):
        if not self.auth.is_logged_in():
            print("🔒 Please login first.")
            return
        note = self.memory_data.get(note_id)
        if not note:
            print("❌ Note not found.")
            return
        if note.get("password_protected") and not self.auth.verify_password():
            print("❌ Incorrect password.")
            return
        if new_text is None:  # Interactive edit
            print(f"Current note content:\n{note['text']}\n")
            print("""Enter new note content:

For single-line notes, type your note and press Enter.

For multi-line notes, type each line and end with 'EOF' on a new line.

Use \\n in single-line input for newlines (e.g., 'Line1\\nLine2').
""")
            lines = []
            first_line = input("New note: ").strip()
            if not first_line:  # Handle empty first line
                print("❌ Note cannot be empty.")
                return
            if first_line == "EOF":  # Handle immediate EOF
                print("❌ Note cannot be empty.")
                return
            if "\\n" in first_line:  # Handle \n in single-line input
                new_text = first_line.replace("\\n", "\n")
            else:
                lines.append(first_line)
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                new_text = "\n".join(lines).strip()
        if not new_text:
            print("❌ Note cannot be empty.")
            return
        note["text"] = new_text
        note["timestamp"] = str(datetime.datetime.now())  # Update timestamp
        save_json(MEMORY_FILE, self.memory_data)
        print(f"✅ Note {note_id} updated.")

# CLI Entrypoint
def main():
    parser = argparse.ArgumentParser(
        description=f"""
🧠 Termux Remember - A Secure CLI Note Keeper for Termux Users
──────────────────────────────────────────────────────────────
An interactive terminal-based memory assistant to securely store
your personal notes, ideas, and tasks. supports tagging, password-protection, multi-line entries, and keyword-based search.

📁 STORAGE DIRECTORY:
User credentials: ~/.termux_remember/user.json
Saved notes     : ~/.termux_remember/memory.json

🔐 USER AUTHENTICATION:
--signup           Register with your email and password
--login            Login to your account
--logout           Logout from the current session

📝 NOTE ADDITION & EDITING:
--add TEXT         Add a note (use TEXT for single-line, or leave empty for interactive)
--edit-note ID     Edit a specific note by its ID (Interactive)
--tag TAG          Add a tag to your note (e.g., --tag "personal")
--password         Protect your note using your login password

📥 INTERACTIVE INPUT MODES:
Use --add "your note" for single-line note.
Use just --add (no quotes) for interactive input:
→ Type each line of the note, and finish with a line containing only: EOF
→ Example:
$ remember --add
> Today was great
> I am very happy
> EOF
You can also use "\\n" to insert newlines with a single-line input
→ Example: --add "Line1\\nLine2"

🏷️ TAGGING & MANAGEMENT:
--retag ID TAG     Update the tag of a note (e.g., --retag 3 "journal")
--list-tag         List all unique tags
--delete-all-tags  Remove all tags from all notes
--delete-specific-tag TAG  Remove a specific tag from all notes
--rm-note-tag ID   Remove tag from a specific note

📋 LIST & SEARCH:
--list             View all your saved notes (🔒 indicates password protected)
--find KEY         Search notes by a keyword
--view-note ID     View a specific note by its ID
--show-tag TAG     View all notes that have a specific tag

🗑️ NOTE DELETION:
--forget ID        Delete a specific note (will ask for password if protected)
--forget-all       Delete ALL notes after confirmation and password

🔐 SECURITY DETAILS:
All passwords are stored securely using SHA-256 hashing.
Notes marked with --password are hidden unless verified.
Viewing or deleting protected notes will require password confirmation.

🧪 EXAMPLES:
remember --signup
remember --login
remember --add "Remember to call mom" --tag "family"
remember --add --tag "diary" --password
remember --edit-note 2
remember --find "milk"
remember --view-note 2
remember --retag 2 "tasks"
remember --list-tag
remember --delete-all-tags
remember --delete-specific-tag "family"
remember --rm-note-tag 2
remember --forget 2
remember --forget-all

🔑 FORGOT PASSWORD?
Just create a new account using --signup

📦 VERSION & META:
--version          Show current version and author details

👨‍💻 AUTHOR INFO:
Author    : {author}
Email     : {email}
GitHub    : {github}

🌐 GITHUB REPOSITORY:
{github}

Made with ❤️ for Termux users who don't want to forget little things.
""",
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument("--signup", action="store_true", help="Create a new user account")
    parser.add_argument("--login", action="store_true", help="Login to your account")
    parser.add_argument("--logout", action="store_true", help="Logout from your session")
    parser.add_argument("--add", nargs='?', default=None, type=str, help="Add a new note (single-line with TEXT, or interactive if no TEXT)")
    parser.add_argument("--edit-note", metavar='ID', type=str, help="Edit a specific note by its ID (interactive)")
    parser.add_argument("--tag", metavar='TAG', type=str, help="Optional tag for your note")
    parser.add_argument("--password", action="store_true", help="Protect the note with your login password")
    parser.add_argument("--list", action="store_true", help="List all saved notes")
    parser.add_argument("--find", metavar='KEY', type=str, help="Search notes by keyword")
    parser.add_argument("--view-note", metavar='ID', type=str, help="View a specific note by its ID")
    parser.add_argument("--show-tag", metavar='TAG', type=str, help="Show notes with a specific tag")
    parser.add_argument("--retag", nargs=2, metavar=('ID', 'TAG'), help="Change the tag of a specific note")
    parser.add_argument("--list-tag", action="store_true", help="List all unique tags")
    parser.add_argument("--delete-all-tags", action="store_true", help="Remove all tags from all notes")
    parser.add_argument("--delete-specific-tag", metavar='TAG', type=str, help="Remove a specific tag from all notes")
    parser.add_argument("--rm-note-tag", metavar='ID', type=str, help="Remove tag from a specific note")
    parser.add_argument("--forget", metavar='ID', type=str, help="Delete a specific note by its ID")
    parser.add_argument("--forget-all", action="store_true", help="Delete all notes (require confirmation & password)")
    parser.add_argument("--version", action="store_true", help="Show current version of the app")

    args = parser.parse_args()

    if args.version:
        print(f"""
📦 termux-remember v{version}
🧑‍💻 Author : {author}
🔗 GitHub  : {github}
✉️ Email   : {email}
""")
        return

    auth = AuthManager()
    memory = MemoryManager()

    if args.signup:
        auth.signup()
    elif args.login:
        auth.login()
    elif args.logout:
        auth.logout()
    elif '--add' in sys.argv or args.tag or args.password:
        note_text = args.add
        if note_text is None:
            memory.add_memory(
                text=None,
                tag=args.tag,
                password_protected=args.password
            )
        elif note_text.strip() == "":
            print("❌ Empty note text. For multi-line or interactive input, use just --add without quotes.")
        else:
            memory.add_memory(
                text=note_text,
                tag=args.tag,
                password_protected=args.password
            )
    elif args.edit_note:
        memory.edit_note(args.edit_note)
    elif args.list:
        memory.list_notes()
    elif args.find:
        memory.find_notes(args.find)
    elif args.view_note:
        memory.view_note(args.view_note)
    elif args.show_tag:
        memory.show_notes_by_tag(args.show_tag)
    elif args.retag:
        memory.retag_note(args.retag[0], args.retag[1])
    elif args.list_tag:
        memory.list_tags()
    elif args.delete_all_tags:
        memory.delete_all_tags()
    elif args.delete_specific_tag:
        memory.delete_specific_tag(args.delete_specific_tag)
    elif args.rm_note_tag:
        memory.remove_note_tag(args.rm_note_tag)
    elif args.forget:
        memory.delete_note(args.forget)
    elif args.forget_all:
        memory.delete_all_notes()
    else:
        parser.print_help()


# Run main if executed directly
if __name__ == "__main__":
    main()
