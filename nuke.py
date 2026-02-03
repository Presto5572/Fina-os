import os
import time

DB_PATH = "data/fina_os.db"

def nuke_it():
    print(f"☢️  INITIATING NUCLEAR RESET ON: {DB_PATH}")
    
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("✅ Database file successfully deleted.")
        except PermissionError:
            print("❌ ERROR: File is locked. Close any other Python terminals/DB browsers and try again.")
            return
    else:
        print("⚠️  File not found (It's already gone).")

    # Double check
    if not os.path.exists(DB_PATH):
        print("\n✨ CLEAN SLATE CONFIRMED.")
        print("You may now run 'python setup_server.py' to rebuild.")
    else:
        print("❌ GHOST DATA REMAINS. Manual deletion required.")

if __name__ == "__main__":
    nuke_it()