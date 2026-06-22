# Class Rank with Authentication and Database

This project is now a backend-backed school course review site.

## Install dependencies

From the project root folder:

```powershell
python -m pip install -r requirements.txt
```

## Run locally

```powershell
.\serve.ps1
```

Then open:

```text
http://localhost:5500
```

## Push to GitHub

1. Initialize git and commit the project:

```powershell
git init
git add .
git commit -m "Initial Class Rank app"
```

2. Create a GitHub repository on github.com.
3. Add the remote and push:

```powershell
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

4. If you already have an existing repo, use its HTTPS or SSH URL instead.

## Deploy to Render

This project includes `render.yaml` so Render can detect and deploy the app automatically.

1. Go to https://render.com and sign in.
2. Create a new Web Service.
3. Connect your GitHub account and choose the repository you pushed.
4. For the service, use:
   - Environment: `Python`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT server:app`
4. Add environment variables in Render:
   - `FLASK_SECRET_KEY` with a secure secret value
   - `DATABASE_URL` optionally if you use a hosted database
   - `SESSION_COOKIE_SECURE` optionally set to `true` for HTTPS-only cookies
5. Deploy the service.

Render gives you an HTTPS URL like `https://<your-app>.onrender.com` automatically.

> This repo also includes `.env.example` for local development. Copy it to `.env` and set your own `FLASK_SECRET_KEY` before running locally.
>
> Render does not use `.env` files directly, so set these values in the Render dashboard instead.

## Login & registration

- A default admin account is created automatically:
  - username: `admin`
  - password: `admin123`
- Students and staff can register from the login page using a Davis School District email.
- Only a valid `@davis.k12.ut.us` address can be used to register and post reviews.
- Users can log in with either their username or their school email.
- Registered users can post reviews after logging in.
- Admin users can delete reviews from the course detail page.

## What changed

- `server.py` now uses SQLite for users and reviews.
- `/api/login`, `/api/register`, `/api/logout`, and `/api/me` support authentication.
- Reviews are saved in `data/app.db` instead of browser-only storage.
- The frontend now has login/register UI and requires login to post reviews.

## What else you would add for a full school deployment

1. Enable HTTPS / real hosting
2. Use a stronger secret key with `FLASK_SECRET_KEY`
3. Replace the demo admin password
4. Add input validation and stronger security checks
5. Add student/teacher accounts and user roles
6. Add moderation pages and review deletion controls
7. Deploy to a cloud host such as Heroku, Render, or Azure

## Deployment & Production notes

Quick checklist for production:

- Set a persistent `FLASK_SECRET_KEY` in your environment (do NOT use the dev key). Example (PowerShell):

```powershell
$env:FLASK_SECRET_KEY = "$(python -c \"import secrets; print(secrets.token_urlsafe(48))\")"
```

- Use a production WSGI server (Gunicorn) and a reverse proxy (NGINX) when deploying to a VM/container. Example (Linux):

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 server:app
```

- For zero-ops hosting, Render or Heroku can run the app. Example Render `start` command:

```
python server.py
```

- Secure the site with HTTPS (TLS) and restrict CORS if integrating with other domains.

- Rotate the admin/demo password and create real accounts for staff.

## Deploying with HTTPS on Render

This app is ready for Render, which provides free HTTPS automatically for public services.

1. Push your repository to GitHub.
2. Sign in to https://render.com and create a new Web Service.
3. Connect your GitHub repo and select the branch to deploy.
4. Use the following settings:
   - Environment: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT server:app`
   - Environment variables:
     - `FLASK_SECRET_KEY` set to a strong secret
     - `DATABASE_URL` optionally set for hosted database support
5. Deploy and open the generated Render URL. It will be served over HTTPS.

### Optional Render Docker deployment

If you prefer Docker, Render can also use the existing `Dockerfile`:

- Select "Docker" as the environment.
- Use the default Dockerfile at the repo root.
- The service URL will still be HTTPS-managed by Render.

## Notes on HTTPS

Once deployed to Render, the service URL will be `https://<your-app>.onrender.com` or a custom domain if you configure one. Render handles TLS certificates for you, so the site is HTTPS by default.

## Seeding and tests

Set production env values in `.env` or environment variables. To seed/set the admin password locally:

```powershell
setx FLASK_ADMIN_PW "your-strong-admin-pw"
python seed_db.py
```

Run tests:

```powershell
python -m pytest -q
```

Database migrations

This project includes a lightweight SQL-based migrations runner. To apply migrations locally:

```powershell
python migrate.py
```

Migration files live in `migrations/versions` and are applied in filename order. New migrations should be added as `.sql` files.
