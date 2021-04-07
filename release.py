SITE="pypi.org"
USER="shinmera"

def password(site):
    process = subprocess.run(["pass", SITE], capture_output=True, encoding="utf-8")
    return process.stdout.split('\n')[0]

subprocess.run(["python3", "-m", "build"])
subprocess.run(["python3", "-m", "twine", "upload",
                "--username", USER,
                "--password", password(SITE),
                "--repository", "pypi",
                "dist/*"])
