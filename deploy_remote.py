import os
import pty
import time
import subprocess
import shutil

# CONFIG
HOST = "147.47.239.135"
USER = "hyeokjun"
PASS = "1234"
REMOTE_DIR = f"/home/{USER}/autowein_deploy"
LOCAL_ARCHIVE = "autowein_pack.tar.gz"

def run_interactive(cmd_list, password, desc="Command"):
    """
    Runs a command that might ask for a password using a pseudo-terminal.
    """
    print(f"[{desc}] Running: {' '.join(cmd_list)}")
    
    pid, fd = pty.fork()
    if pid == 0:
        # Child process
        os.execvp(cmd_list[0], cmd_list)
    else:
        # Parent process
        output = b""
        try:
            while True:
                try:
                    chunk = os.read(fd, 1024)
                    if not chunk: break
                    output += chunk
                    
                    # Check for password prompt
                    if b"password:" in chunk.lower():
                        os.write(fd, (password + "\n").encode())
                        
                    # Also print to stdout for debugging
                    # sys.stdout.write(chunk.decode(errors='ignore'))
                    
                except OSError:
                    break
        except Exception as e:
            print(f"Error communicating: {e}")
        
        _, status = os.waitpid(pid, 0)
        return status == 0, output.decode(errors='ignore')

def main():
    print("=== Autowein Remote Deployer ===")
    
    # 1. Archive
    print("1. Creating Archive...")
    # Exclude output file to prevent infinite recursion/errors
    cmd = ["tar", "-czf", LOCAL_ARCHIVE, "--exclude=.git", "--exclude=__pycache__", f"--exclude={LOCAL_ARCHIVE}", "."]
    
    # Tar returns 1 often if files change (e.g. logs), ignore strict check
    subprocess.run(cmd, check=False)
    
    if not os.path.exists(LOCAL_ARCHIVE):
        print("Archive creation failed!")
        return
    
    print(f"Archive {LOCAL_ARCHIVE} created.")
    
    # 2. SCP Upload
    print("2. Uploading to Server...")
    # Clean remote directory first (optional, via SSH)
    
    # Simple SCP
    success, log = run_interactive(
        ["scp", "-o", "StrictHostKeyChecking=no", LOCAL_ARCHIVE, f"{USER}@{HOST}:{REMOTE_DIR}.tar.gz"], 
        PASS, 
        desc="SCP Upload"
    )
    if not success:
        print("Upload Failed!")
        print(log)
        return
    print("Upload Success.")

    # 3. Remote Execution Stub
    # We will send a large chained command to SSH to handle everything
    setup_cmds = [
        f"mkdir -p {REMOTE_DIR}",
        f"tar -xzf {REMOTE_DIR}.tar.gz -C {REMOTE_DIR}",
        f"cd {REMOTE_DIR}",
        "echo 'Building Docker Image...'",
        "docker build -t autowein-trainer .",
        "echo 'Running Training Container...'",
        # Use GPUs 1 and 2 (indices 1,2)
        # Note: --gpus '"device=1,2"' syntax or NV_GPU env var depending on docker version.
        # Safest is usually --gpus '"device=1,2"'
        "docker run --rm --gpus '\"device=1,2\"' -v $(pwd)/models:/app/models autowein-trainer"
    ]
    
    remote_cmd_str = " && ".join(setup_cmds)
    
    print("3. Executing Remote Training...")
    success, log = run_interactive(
        ["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{HOST}", remote_cmd_str],
        PASS,
        desc="SSH Execute"
    )
    
    print("=== Remote Log Output ===")
    print(log)
    
    if "Model saved to" in log:
        print("\n[SUCCESS] Remote Training Completed Successfully!")
    else:
        print("\n[WARNING] Training might have failed. Check log above.")

    # Cleanup local
    if os.path.exists(LOCAL_ARCHIVE):
        os.remove(LOCAL_ARCHIVE)

if __name__ == "__main__":
    main()
