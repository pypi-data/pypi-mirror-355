import argparse
import os
import questionary
from .frontend import handle_frontend
from .backend import handle_backend

def init_project():
    project_name = questionary.text("Enter your project name:").ask()
    directory = questionary.text("Enter the directory where you want to create the project:").ask()
    full_path = os.path.join(directory, project_name)
    os.makedirs(full_path, exist_ok=True)
    os.chdir(full_path)

    project_type = questionary.select(
        "Select the project type:",
        choices=["Frontend", "Backend", "Full Stack"]
    ).ask()

    if project_type == "Frontend":
        handle_frontend()
    elif project_type == "Backend":
        handle_backend()
    elif project_type == "Full Stack":
        os.makedirs("frontend", exist_ok=True)
        os.makedirs("backend", exist_ok=True)

        # frontend
        os.chdir("frontend")
        handle_frontend()
        os.chdir("..")

        # backend
        os.chdir("backend")
        handle_backend()
        os.chdir("..")

    author = questionary.text("Enter author name:").ask()

    with open("README.md", "w") as f:
        f.write(f"# {project_name}\n\nAuthor: {author}\n")

    print(f"\n Project '{project_name}' created successfully at {full_path}!")

def main():
    parser = argparse.ArgumentParser(prog="iya")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Initialize a new project")

    args = parser.parse_args()

    if args.command == "init":
        init_project()
    else:
        parser.print_help()
