# Shortner URL service
This is a project from the [roadmap.sh](https://roadmap.sh) website, project details can be found here from [roadmap.sh](https://roadmap.sh/projects/url-shortening-service), it was implemented as an API with Python.

# Python Technologies Used:
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL

# How to run
- create environment using something like `conda` or `venv`
    - I used: `python -m venv .venv`
    - Activate `./.venv/Scripts/Activate` (on Windows)
- install dependencies using `pip install -r requirements.txt`
- make sure to add your env variables for PostgreSQL database (see `.env.example`)

# Run with Uvicorn
`uvicorn app.main:app --reload`

# Run with FastAPI CLI
`fastapi dev app/main.py`
