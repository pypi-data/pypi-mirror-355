import os
import subprocess

def main():
    script_path = os.path.join(os.path.dirname(__file__), "install_silo.sh")
    os.chmod(script_path, 0o755)  # Ensure script is executable
    subprocess.run([script_path])

if __name__ == "__main__":
    main()
