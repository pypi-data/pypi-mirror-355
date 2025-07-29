import questionary
import subprocess
import os

def handle_frontend():
    frontend_choice = questionary.select(
        "Select Frontend Technology:",
        choices=["React", "Angular", "Vue", "Svelte", "Next.js", "Nuxt.js", "SolidJS", "Qwik", "Astro"]
    ).ask()

    frontend_lang = None
    if frontend_choice == "React":
        frontend_lang = questionary.select(
            "Choose language for React:",
            choices=["JavaScript", "TypeScript"]
        ).ask()

    print("\nCreating frontend...")

    if frontend_choice == "React":
        if frontend_lang == "JavaScript":
            subprocess.run(["npx", "create-react-app", ".", "--template", "cra-template"])
        else:
            subprocess.run(["npx", "create-react-app", ".", "--template", "typescript"])
    elif frontend_choice == "Next.js":
        next_lang = questionary.select(
            "Choose language for Next.js:",
            choices=["JavaScript", "TypeScript"]
        ).ask()

        if next_lang == "TypeScript":
            subprocess.run(["npx", "create-next-app", ".", "--typescript"])
        else:
            subprocess.run(["npx", "create-next-app", "."])
    elif frontend_choice == "Vue":
        subprocess.run(["npm", "init", "vue@latest"])
    elif frontend_choice == "Angular":
        subprocess.run(["npx", "@angular/cli", "new", os.getcwd()])
    elif frontend_choice == "Svelte":
        subprocess.run(["npm", "create", "vite@latest", ".", "--", "--template", "svelte"])
    elif frontend_choice == "Nuxt.js":
        subprocess.run(["npx", "nuxi", "init", "."])
    elif frontend_choice == "SolidJS":
        subprocess.run(["npm", "create", "solid@latest"])
    elif frontend_choice == "Qwik":
        subprocess.run(["npm", "create", "qwik@latest"])
    elif frontend_choice == "Astro":
        subprocess.run(["npm", "create", "astro@latest"])
