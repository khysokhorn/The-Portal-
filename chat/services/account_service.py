import os
import shutil
import time
import json

ANTIGRAVITY_TOOLS_DIR = "/root/.antigravity_tools"
BACKUP_DIR = "/root/.antigravity_tools/backups"

class AccountService:
    @staticmethod
    def logout_current_account():
        """
        Logs out ONLY the currently active account in Antigravity.
        """
        accounts_json_path = os.path.join(ANTIGRAVITY_TOOLS_DIR, "accounts.json")
        if not os.path.exists(accounts_json_path):
            return False, "accounts.json not found."

        try:
            with open(accounts_json_path, 'r') as f:
                data = json.load(f)
            
            current_id = data.get("current_account_id")
            if not current_id:
                return False, "No current account identified."

            # 1. Backup and Remove Account File
            account_file = os.path.join(ANTIGRAVITY_TOOLS_DIR, "accounts", f"{current_id}.json")
            if os.path.exists(account_file):
                backup_dir = os.path.join(ANTIGRAVITY_TOOLS_DIR, "backups", f"single_logout_{int(time.time())}")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.move(account_file, os.path.join(backup_dir, f"{current_id}.json"))
            
            # 2. Update accounts.json
            initial_count = len(data.get("accounts", []))
            data["accounts"] = [acc for acc in data.get("accounts", []) if acc.get("id") != current_id]
            
            if data["accounts"]:
                data["current_account_id"] = data["accounts"][0]["id"]
            else:
                data["current_account_id"] = None
            
            with open(accounts_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, f"Logged out current account ({current_id}). {initial_count - len(data['accounts'])} account removed."
            
        except Exception as e:
            return False, f"Error during single logout: {str(e)}"

    @staticmethod
    def logout_all_accounts():
        """
        Performs the 'Logout' action by clearing account session files for both
        the Docker Manager and the Desktop App.
        """
        results = []
        
        # --- 1. Reset Docker Manager ---
        if os.path.exists(ANTIGRAVITY_TOOLS_DIR):
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)
            
            timestamp = int(time.time())
            backup_path = os.path.join(BACKUP_DIR, f"logout_{timestamp}")
            os.makedirs(backup_path)

            files_to_reset = ["accounts.json", "user_tokens.db"]
            dirs_to_reset = ["accounts"]
            
            reset_count = 0
            for d in dirs_to_reset:
                src = os.path.join(ANTIGRAVITY_TOOLS_DIR, d)
                if os.path.exists(src):
                    shutil.move(src, os.path.join(backup_path, d))
                    reset_count += 1
            for f in files_to_reset:
                src = os.path.join(ANTIGRAVITY_TOOLS_DIR, f)
                if os.path.exists(src):
                    shutil.move(src, os.path.join(backup_path, f))
                    reset_count += 1
            results.append(f"Docker Manager: Reset {reset_count} components. Backup at {backup_path}")
        else:
            results.append("Docker Manager: Directory not found (skipping).")

        # --- 2. Reset Desktop App ---
        desktop_support_dir = "/root/DesktopAppSupport/Antigravity"
        if os.path.exists(desktop_support_dir):
            # As per user's solution: clear auth-tokens and standard session data
            desktop_items_to_clear = ["auth-tokens", "Cookies", "Local Storage", "Session Storage"]
            cleared_desktop = 0
            for item in desktop_items_to_clear:
                path = os.path.join(desktop_support_dir, item)
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    cleared_desktop += 1
            results.append(f"Desktop App: Cleared {cleared_desktop} cache items.")
        else:
            results.append("Desktop App: Directory not found (skipping).")
            
        return True, " | ".join(results)
