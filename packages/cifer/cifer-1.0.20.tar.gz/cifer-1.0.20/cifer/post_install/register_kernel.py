# cifer/post_install/register_kernel.py
import os
import sys
import subprocess

def register_kernel():
    kernel_name = "cifer-kernel"
    display_name = "🧠 Cifer Kernel"
    kernel_dir = os.path.expanduser(f"~/.local/share/jupyter/kernels/{kernel_name}")

    if os.path.exists(kernel_dir):
        print(f"✅ Kernel already exists: {display_name}")
        return

    print(f"🚀 Registering Jupyter kernel: {display_name}")
    try:
        subprocess.run([
            sys.executable, "-m", "ipykernel", "install",
            "--user", "--name", kernel_name,
            "--display-name", display_name
        ], check=True)
        print(f"✅ Kernel registered as: {display_name}")
    except Exception as e:
        print(f"❌ Failed to register kernel: {e}")
