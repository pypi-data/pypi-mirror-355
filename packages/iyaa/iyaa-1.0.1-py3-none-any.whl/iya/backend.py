import questionary
import subprocess
import os

def handle_backend():
    backend_choice = questionary.select(
        "Select Backend Technology:",
        choices=["FastAPI", "Django", "Express.js", "Nest.js"]
    ).ask()

    print("\nCreating backend...")

    if backend_choice == "FastAPI":
        subprocess.run(["python3", "-m", "venv", "venv"])
        subprocess.run(["venv/bin/pip", "install", "fastapi", "uvicorn"])
        with open("main.py", "w") as f:
            f.write("""from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")
    elif backend_choice == "Django":
        subprocess.run(["python3", "-m", "venv", "venv"])
        subprocess.run(["venv/bin/pip", "install", "django"])
        subprocess.run(["venv/bin/django-admin", "startproject", "mysite"])
    elif backend_choice == "Express.js":
        subprocess.run(["npm", "init", "-y"])
        subprocess.run(["npm", "install", "express"])
        with open("index.js", "w") as f:
            f.write("""const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => res.send('Hello World!'));
app.listen(port, () => console.log(`Example app listening on port ${port}!`));
""")
    elif backend_choice == "Nest.js":
        subprocess.run(["npm", "i", "-g", "@nestjs/cli"])
        subprocess.run(["nest", "new", "."])
