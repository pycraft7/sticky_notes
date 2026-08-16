# STICKY NOTES — Complete Deploy Guide

> Django 6.1 Sticky Notes app — local bata Render.com ma deploy garna ko step-by-step guide.
> Har ek step ma **kina** bhanne explanation pani cha — aru lai sikau na milne gari.

---

## 1. Project Structure

```
sticky_notes/
├── config/          # Main project (settings.py, urls.py, wsgi.py)
│   ├── settings.py  # Sabai configuration
│   └── urls.py      # Root URL routing
├── notes/           # Note app (CRUD)
│   ├── models.py    # Note model (user, title, content, timestamps)
│   ├── views.py     # home, add, edit, delete
│   └── urls.py      # /notes/ paths
├── accounts/        # Auth app
│   ├── models.py    # Profile model (full_name, photo)
│   ├── views.py     # register, login, logout, profile
│   └── urls.py      # /accounts/ paths
├── templates/       # HTML files (notes/ + accounts/)
├── static/          # CSS files
├── manage.py        # Django CLI
└── requirements.txt # Packages list
```

### URL structure (final)
| Page | URL | View |
|---|---|---|
| Login (landing) | `/` , `/accounts/` | `accounts.views.login_view` |
| Register | `/accounts/register/` | `register_view` |
| Logout | `/accounts/logout/` | `logout_view` |
| Profile | `/accounts/profile/` | `profile_view` |
| Home | `/notes/home/` | `notes.views.home_views` |
| Add note | `/notes/add/` | `add_note` |
| Edit note | `/notes/edit/<pk>/` | `edit_note` |
| Delete note | `/notes/delete/<pk>/` | `delete_note` |

---

## 2. Local Setup (pehla patak)

### 2.1 Virtual environment (venv)

Python project ma dependencies isolate rakhnu ko lagi venv chahinchha — global Python ma jasta taistai package install garema version conflict aunchha.

```bash
# Windows (PowerShell)
python -m venv .env
.env\Scripts\activate

# Linux/Mac
python3 -m venv .env
source .env/bin/activate
```

### 2.2 Packages install

```bash
pip install Django Pillow gunicorn whitenoise dj-database-url "psycopg[binary]"
```

| Package | Kina chahinchha |
|---|---|
| Django | Web framework nai |
| Pillow | Profile photo (`ImageField`) ko lagi — ImageField bina Pillow chaldaina |
| gunicorn | Production web server (runserver development ko lagi matra) |
| whitenoise | Static files (CSS) production ma serve garna |
| dj-database-url | `DATABASE_URL` env bata DB connect garna |
| psycopg[binary] | PostgreSQL ko Python driver |

### 2.3 Migrations + Run

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Khola: `http://127.0.0.1:8000/` → login page auncha.

---

## 3. Deploy Prep — Files

### 3.1 `requirements.txt` (project root)

```bash
pip freeze > requirements.txt
```

**Kina:** Render le yo file padhera sabai packages install garchha. `pip freeze` le exact versions (`Django==6.1`) rakhcha — reproducibility ko lagi ramro.

**Verify:**
```bash
type requirements.txt   # Windows
cat requirements.txt    # Linux
```

`gunicorn`, `whitenoise`, `dj-database-url`, `psycopg` **hunai parcha** — chaina bhane deploy fail hunchha.

### 3.2 `.gitignore` (project root)

```
.env/
db.sqlite3
media/
__pycache__/
*.pyc
staticfiles/
```

**Kina:**
- `.env/` — venv (hundreds of MB) GitHub ma chahindaina
- `db.sqlite3` — Render ma PostgreSQL use hunchha; SQLite pani environment-specific ho
- `media/` — uploaded photos (user data)
- `staticfiles/` — `collectstatic` ko output (build time ma bancha)

### 3.3 `config/settings.py` changes

#### a) Top ma import:

```python
import os
import dj_database_url
from pathlib import Path
```

`dj_database_url` import garnu parchha — package naam `dj-database-url` (PyPI ma dash) tara Python import ma dash chaldaina, so underscore (`dj_database_url`).

#### b) SECRET_KEY / DEBUG / ALLOWED_HOSTS — environment bata:

```python
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-<local-fallback>")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
```

**Kina env bata?**
- SECRET_KEY production ma GitHub ma leak garna hudaina → Render dashboard ko env var ma rakhe
- DEBUG `True` ma error page le code leak garchha → production ma `False`
- ALLOWED_HOSTS = domain ko whitelist → env bata set garne

**Note:** `ALLOWED_HOSTS` default `[""]` rakhema local `runserver` ma **400 Bad Request** aunchha — `127.0.0.1,localhost,testserver` default rakha.

#### c) Whitenoise middleware (MIDDLEWARE ko FIRST position):

```python
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    ...
]
```

**Kina:** Production ma Django aafai static serve gardaina — whitenoise le CSS serve garchha.

#### d) Static files (STATIC_URL ko pachadi):

```python
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

`STATIC_ROOT` = `collectstatic` ko output thau. Manifest storage = hashed filenames (`style.f999df8ae7ef.css`) + caching.

#### e) Database — SQLite local, PostgreSQL production:

```python
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3")
    )
}
```

**Kina:** `DATABASE_URL` env chaina → SQLite (local). `DATABASE_URL` cha (Render ma) → PostgreSQL. Eutai code, duita environment.

#### f) Security settings (production):

```python
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False") == "True"
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

**Kina env bata?** `runserver` (http) ma cookie secure garema login bigranchha — lokal ma False, Render ma True.

**`SECURE_PROXY_SSL_HEADER` jaruri cha** — Render HTTPS bata proxy forward garchha, chaina bhane redirect loop aunchha.

#### g) LOGIN_URL:

```python
LOGIN_URL = "/accounts/"
```

**Kina:** `@login_required` view ma anonymous user janchas → `LOGIN_URL` ma redirect hunchha. Login `/accounts/` ma cha (accounts/urls.py ma `path("", views.login_view)`), so `LOGIN_URL` tyahi hunu parcha. Galti URL rakhema **404** aunchha.

### 3.4 `config/urls.py` — media serving:

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", accounts_views.login_view, name="landing"),
    path("notes/", include("notes.urls")),
    path("accounts/", include("accounts.urls")),
]
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT}
    ),
]
```

**Kina `static()` use nagareko?** Django ko `static()` helper le **`DEBUG=False` ma khali list return garchha** — production ma photo 404 dincha. Explicit `serve` URL pattern `DEBUG` ko condition bina kaam garchha.

**Note:** `static()` bhanne import (`from django.conf.urls.static import static`) aaba chahindaina — matlab `config/urls.py` ko top ma na rakhne.

---

## 4. Git + GitHub

```bash
# Project folder ma
git init
git config user.name "Timro Naam"
git config user.email "timro@email.com"
git add .
git commit -m "Ready for deploy"
```

### GitHub repo banaune:

1. github.com → `+` → New repository
2. Name: `sticky_notes`, Public
3. **"Add a README file" TICK NAGARA** (conflict aunchha)
4. Create → repo page ko commands:

```bash
git remote add origin https://github.com/<USERNAME>/sticky_notes.git
git branch -M main
git push -u origin main
```

### Commit message rules:
- Short + clear: `"Add requirements and security"`, `"Fix login redirect"`, `"Add profile photo feature"`
- Ek commit = ek kaam
- **`.env/` ra `db.sqlite3` GitHub ma gayeko chaina check gara** — `git ls-files` ma dekhinuhudaina

---

## 5. Render.com Deploy

### 5.1 Web Service banaune

1. **render.com** → Sign up with GitHub
2. Dashboard → **New +** → **Web Service** → GitHub repo connect (`sticky_notes`)
3. Form:
   - **Name:** `sticky-notes`
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:**
     ```
     gunicorn config.wsgi
     ```
   - **Instance:** Free

### 5.2 Environment Variables (Advanced → Add Environment Variable — **Key/Value pair**, .env file upload HOINA)

| Key | Value | Kina |
|---|---|---|
| `SECRET_KEY` | Random 50+ chars (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) | Encryption |
| `DEBUG` | `False` | Security |
| `ALLOWED_HOSTS` | `*` | Domain whitelist (ya exact domain) |
| `SECURE_SSL_REDIRECT` | `True` | HTTPS force |
| `SESSION_COOKIE_SECURE` | `True` | Session cookie HTTPS matra |
| `CSRF_COOKIE_SECURE` | `True` | CSRF cookie HTTPS matra |
| `SECURE_HSTS_SECONDS` | `31536000` | HSTS |

### 5.3 PostgreSQL

1. **New +** → **PostgreSQL** → Create
2. Web Service → **Environment** tab → **Link Postgres** → DB select
3. `DATABASE_URL` auto-add hunchha (link huna parcha — build ma DB error aayo bhane check gara)

**Kina PostgreSQL, SQLite hoina?** Render free tier ko filesystem **ephemeral** cha — redeploy garepachi sabai file wipe. PostgreSQL aru server ma bascha, data safe rahancha.

### 5.4 Deploy + Test

- **Deploy** press → 5-10 min
- Logs ma `Build succeeded` + `Your service is live`
- Test checklist:
  - [ ] `/` → login page
  - [ ] Register → home ma puginchha
  - [ ] Logout → login page
  - [ ] Login → home
  - [ ] Note add / edit / delete
  - [ ] Profile photo upload → sidebar ma photo
  - [ ] Photo refresh pachi pani dekhincha (media serve)

---

## 6. Feri Deploy Garna (update — 3 command)

```bash
git add .
git commit -m "K ke change gareko"
git push origin main
```

Render auto-redeploy hunchha (1-2 min). **DB migrate** build command le afai garchha (naya model change bhaye `makemigrations` local ma garera migrations file pani commit garna naparcha... actually garera nai commit gara!).

---

## 7. Common Errors + Solutions

| Error | Cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'Profile'` | `notes/views.py` ma `from .models import Note, Profile` tara Profile `accounts/models.py` ma cha | `from accounts.models import Profile` |
| `400 Bad Request` | `ALLOWED_HOSTS = [""]` (env na huda) | Default `127.0.0.1,localhost,testserver` |
| `404` login redirect pachi | `LOGIN_URL` galti URL | Login ko actual URL rakha (`/accounts/`) |
| Photo `/media/` 404 on Render | `static()` helper `DEBUG=False` ma kaam gardaina | Explicit `serve` URL pattern |
| `ModuleNotFoundError` | requirements.txt ma package chaina | `pip freeze > requirements.txt` |
| `Invalid .env file` (Render UI) | `.env` file upload gareko | **Key/Value pair** ek ek garera add gara |
| `403 Forbidden` POST | CSRF (Origin header missing — test tool ko problem) | Browser ma normal hunchha; curl/pwsh le `Origin` header pathau |
| `Missing staticfiles manifest entry` | Local ma collectstatic gareko chaina (DEBUG=False test ma) | `python manage.py collectstatic --noinput` |
| Free tier `502` after idle | App suspend bhayeko | Reload gare 1-2 min lagcha — normal |

---

## 8. Git Commit History (yo project ko)

```
81ad625 Serve media files with explicit URL pattern
790493f Fix LOGIN_URL to match accounts login route
7193402 Serve media files in production
014c074 Profile improvements and host fix
5f8b568 Add requirements and security
9d2b312 Ready for deploy
```

---

## 9. Important Notes

- **Render free tier disk ephemeral** — profile photos redeploy ma harainchan. Permanent photo chahiyo bhane Cloudinary/S3 jasto storage chahinchha
- **Free tier 15 min idle pachi suspend** — first load dhilo, normal ho
- **Local command chalaunda** venv activate gara: `.env\Scripts\activate`
- **SECRET_KEY chat/email ma share nagara** — aaba compromised bhayo bhane feri generate gara
- `db.sqlite3` local data GitHub/Render ma jadaina — production data PostgreSQL ma matra