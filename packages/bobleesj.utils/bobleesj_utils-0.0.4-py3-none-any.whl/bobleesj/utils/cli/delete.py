import subprocess


def all_local_branches(args):
    command = """git branch | grep -v "main" | xargs git branch -D"""
    subprocess.run(command, shell=True, executable="/bin/bash", check=True)
    print("Deleted all local branches except 'main'.")
