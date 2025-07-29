import os
import subprocess


def build_check_release(args, env_name="release-env"):
    print("📦 Starting isolated build and check process...")
    print(f"🧪 Creating a new environment: {env_name}")

    command = f"""
    mamba create -n {env_name} python=3.13 \\
        --file requirements/test.txt \\
        --file requirements/conda.txt \\
        --file requirements/docs.txt -y && \\
    source $(conda info --base)/etc/profile.d/conda.sh && \\
    conda activate {env_name} && \\
    pip install build twine && \\
    pip install . --no-deps && \\
    python -m build && twine check dist/*
    """

    try:
        subprocess.run(command, shell=True, executable="/bin/bash", check=True)
        print(
            "✅ Build and check completed successfully in environment:",
            env_name,
        )
    except subprocess.CalledProcessError as e:
        print("❌ Build or check failed:")
        print(e)


def build_pytest(args):
    """In a Python subprocess, you start with a blank shell so there is no
    e.g., .bashrc available. The environment name is derived from the current
    working directory.

    - Create a new Python environment with mamba with Python 3.13
    - Install all requirements
    - Install the package
    - Run pytest and pre-commit
    - Run whether it is possible to release to PyPI
    """
    package_name = os.path.basename(os.getcwd())
    env_name = f"{package_name}-env"

    print(f"🧪 Testing package: {package_name}")
    print(f"📦 Creating and using env: {env_name}")

    command = f"""
    mamba create -n {env_name} python=3.13 \\
        --file requirements/test.txt \\
        --file requirements/conda.txt \\
        --file requirements/docs.txt -y && \\
    source $(conda info --base)/etc/profile.d/conda.sh && \\
    conda activate {env_name} && \\
    pip install --no-deps -e . && \\
    pip install pre-commit && \\
    pytest && pre-commit run --all-files
    """

    try:
        subprocess.run(command, shell=True, check=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        print("Error - Test pipeline failed.")
        print(e)
    else:
        print("Good! All tests and checks passed.")
