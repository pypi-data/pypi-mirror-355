import os
import shutil
import subprocess
import time
from dotenv import load_dotenv
from .jenkins import get_crumb

def install_hooks(repo_path):
    hooks_dir = os.path.join(os.path.dirname(__file__), 'hooks')
    git_hooks_dir = os.path.join(repo_path, '.git', 'hooks')
    root_env_path = os.path.join(repo_path, '.env')
    template_env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')

    if not os.path.isdir(git_hooks_dir):
        print("❌ Error: Target directory is not a valid Git repository.")
        return

    print("🔧 Installing Git hooks...")

    # Copy all hooks
    for filename in os.listdir(hooks_dir):
        source = os.path.join(hooks_dir, filename)
        target = os.path.join(git_hooks_dir, filename)

        try:
            shutil.copyfile(source, target)
            os.chmod(target, 0o775)
            print(f"✅ Hook installed: {filename}")
        except Exception as e:
            print(f"❌ Failed to install {filename}: {e}")

    # Copy .env if missing
    if not os.path.exists(root_env_path):
        try:
            shutil.copyfile(template_env_path, root_env_path)
            print("✅ .env file created from template.")
            print("📌 Please enter your Jira and Jenkins credentials in the file.")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return
    else:
        print("⚠️  .env file already exists. No changes made.")

    # Open .env in Notepad
    try:
        subprocess.run(["notepad.exe", root_env_path], check=True)
        print("⏳ Reading updated .env...")

        time.sleep(1)
        load_dotenv(dotenv_path=root_env_path)

        # Validate Jenkins credentials by fetching crumb
        try:
            crumb = get_crumb()
            if crumb:
                print("✅ Jenkins crumb fetched successfully. Jenkins credentials appear valid.")
        except Exception as e:
            print(f"❌ Failed to fetch Jenkins crumb. Please check your JENKINS_URL / credentials.\nDetails: {e}")

    except Exception as e:
        print(f"⚠️ Could not open .env in Notepad or read it: {e}")

    print("🎉 Installation complete. You're ready to commit!")
