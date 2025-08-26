Career Optimizer — Developer Guide (clean, accurate, step-by-step)
Purpose

This document explains how to get the project running locally, where the important files live, and how the core parts work. It is intended for the developer who will pick up coding and maintenance. All descriptions reflect the current code in the repository you supplied.

Table of contents

Quick start (fastest)

Full setup (step-by-step)

Repository map (exact files & folders)

Key configuration to check (settings.py)

Database (where it lives, how it works, how to inspect)

Models (concise, file-by-file)

Views, URLs, Templates — data flow (step-by-step example)

Match scoring — exact behaviour (from code)

Styling & static files (how CSS is applied)

Admin, shell & common commands

Troubleshooting (common problems & fixes)

Handover checklist & recommended first tasks

1 — Quick start (fastest; assumes you provide db.sqlite3)

If you give the incoming developer the repository with requirements.txt and db.sqlite3, these commands are sufficient to run the site locally (Windows):

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver


mac / linux:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver


Open the app:

http://127.0.0.1:8000
http://127.0.0.1:8000/admin


If db.sqlite3 is not provided, run migrations before runserver:

python manage.py migrate


To create an admin user:

python manage.py createsuperuser

2 — Full setup (step-by-step)

If the new developer needs the full onboarding (create venv, install, migrations), use this:

Clone repo and change directory:

git clone <repo-url>
cd career-optimizer--project


Create and activate virtual environment (Windows PowerShell):

python -m venv venv
& .\venv\Scripts\Activate.ps1


mac / linux:

python -m venv venv
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Confirm settings in careerpath/settings.py (see section 4). If a project-level static/ folder exists, consider adding:

STATICFILES_DIRS = [ BASE_DIR / "static" ]


Apply migrations (if you did not include db.sqlite3):

python manage.py makemigrations
python manage.py migrate


Create superuser (optional):

python manage.py createsuperuser


Run server:

python manage.py runserver

3 — Repository map (exact top-level items)

These are the items actually present in the zip you provided (top-level):

.venv
.vscode
accounts
careerpath
positions
templates
venv
.gitignore
db.sqlite3
db.sqlite3.bak
index.html
manage.py
README.md
requirements.txt
structure.txt


Notes:

.venv and venv are present in the zip — do not commit virtual environment dirs into Git. They should be in .gitignore.

db.sqlite3 and db.sqlite3.bak are present here. If you share the repository with others, decide whether to include db.sqlite3 or provide fixtures instead.

templates/ includes base.html, base_auth.html, and landing.html.

4 — Key configuration to check (careerpath/settings.py)

Open careerpath/settings.py and confirm the following values (these are present in your project):

Custom user model:

AUTH_USER_MODEL = 'accounts.User'


Database (development; file-based SQLite):

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


Static URL:

STATIC_URL = 'static/'


Debug mode (currently True in the repo): DEBUG = True
For production you must set DEBUG = False and configure ALLOWED_HOSTS.

Important notes:

Do not change AUTH_USER_MODEL after migrations have been created/applied. Doing so will cause migration conflicts and requires careful migration planning.

If you want a central static/ folder, add STATICFILES_DIRS as needed (see Full setup step 4).

5 — Database: where it lives and how it behaves

Development DB: db.sqlite3 (file-based SQLite). Path: project root.

The SQLite configuration is set in careerpath/settings.py (see above).

SQLite is a real SQL engine stored in a single file and is suitable for development and testing. It is not a server; for production prefer PostgreSQL or equivalent.

Inspecting data

Use Django shell:

python manage.py shell


then e.g.:

from positions.models import Position
Position.objects.all()[:5]


Or use the sqlite CLI:

sqlite3 db.sqlite3
.tables


Or use the VS Code SQLite extension to open db.sqlite3 visually.

Changing data vs changing schema

To change rows (data): use Django admin or the Django ORM (manage.py shell) — preferred.

To change schema (models): edit models.py, then run:

python manage.py makemigrations
python manage.py migrate


Never edit db.sqlite3 schema by hand — always use migrations.

Export / import data
python manage.py dumpdata > dump.json
python manage.py loaddata dump.json

6 — Models (concise, accurate, file-by-file)

I inspected accounts/models.py and positions/models.py. Below is a short, precise summary of the actual models present and what they represent.

accounts/models.py (key classes found)

User — custom user model (inherits AbstractUser). Has is_admin boolean.

StudentProfile — user profile data; linked one-to-one to User.

StudentSkill — links a StudentProfile to a Skill and stores proficiency (string codes like 'low', 'medium', 'high' in some places).

SavedPosition — a student saved a Position. It includes a match_score method (see section 8).

StudentCV — stores a student CV (one-to-one with StudentProfile), fields include full_name, email, phone, address, objective, created_at, updated_at.

Language (and other CV-related models) — languages, etc., related to StudentCV.

Read accounts/models.py directly for full fields — these are the main structures you will read and edit.

positions/models.py (key classes found)

Skill — canonical skill with name and category.

Position — job posting, fields include title, company, description, tags, status, created_at, updated_at.

PositionSkillRequirement — join table: links a Position to a Skill. Fields found:

level_pct (named in code; help text: "Required proficiency % (0–100)")

importance (PositiveSmallIntegerField default=1, help_text "Relative importance (1–5)")

PROFICIENCY_CHOICES (choices like 'low', 'medium', 'high') are defined.

unique_together = ('position','skill')

The PositionSkillRequirement model uses both a numeric level_pct and a coded proficiency level; code uses these fields (see match scoring logic).

7 — Views, URLs, Templates — how a page is produced (step-by-step)

When you need to find where a page is implemented, follow this pattern:

Find the URL: open careerpath/urls.py, then follow the include('accounts.urls') or include('positions.urls') to the app-level urls.py.

Open the view: open the view function/class referenced by the route (in accounts/views.py or positions/views.py).

Check model queries: the view will use the ORM (e.g., StudentSkill.objects.filter(student=request.user)).

Find template: view calls render(request, "path/to/template.html", context). Open that template under templates/.

Map data: in the template, find {{ }} or {% for %} elements and map them back to the context variable names in the view.

Concrete example: “My Skills” page (how it works)

accounts/urls.py includes a route for skills/ (look there).

accounts/views.py implements student_skills (example name). The view:

queries StudentSkill for request.user's profile,

returns render(request, "accounts/skills.html", {"skills": skills}).

templates/accounts/skills.html uses the skills context in a loop:

{% for s in skills %}
  {{ s.skill.name }} - {{ s.proficiency }}
{% endfor %}


If interactivity (AJAX) exists, locate JS under static/ or inline scripts in the template and match endpoints in views.py.

8 — Match scoring — exact behaviour (taken from code)

The repository contains a SavedPosition.match_score method in accounts/models.py. I inspected the method and describe its behaviour exactly:

It builds a prof_map of the student's skills:

prof_map = { ss.skill_id: ss.proficiency for ss in self.profile.student_skills.all() }


where ss.proficiency is the stored code for the student skill (codes like 'low', 'medium', 'high' are used elsewhere).

It gets the position requirements:

reqs = self.position.requirements.all()


It sums importance for all requirements and returns 0.0 if total importance (total weight) is zero.

It defines a numeric ordering for proficiency codes:

LEVEL_ORDER = {"low": 1, "medium": 2, "high": 3}


For each requirement r, it finds:

the student's level code student_lvl = prof_map.get(r.skill_id)

the required level req_lvl = r.required_proficiency_code if hasattr(r, 'required_proficiency_code') else r.level_pct

(Implementation note: the code checks for required_proficiency_code field; otherwise it falls back to level_pct. Because the repository contains both representations, the method is tolerant.)

It increases matched by r.importance when the student's level code is greater than or equal to the required level code using LEVEL_ORDER:

if student_lvl and LEVEL_ORDER.get(student_lvl,0) >= LEVEL_ORDER.get(req_lvl, 0):
    matched += r.importance


Final score returned:

return 100.0 * matched / total_weight


Summary (behavioural):

The algorithm counts how many requirement importances the student meets at or above the required level (using 'low' < 'medium' < 'high' ordering), sums importance of satisfied requirements, and computes a percentage of the total importance. Missing student skill => not matched (student_lvl is None => not counted).

What to confirm when changing scoring:

Which field is canonical: required_proficiency_code (string codes) or level_pct (percentage)? The code supports both; choose one representation and make the logic consistent.

Decide how to treat numeric level_pct (if you switch to percent-based matching, you'll likely change the algorithm to compare numeric values instead of codes).

Decide treatment of missing student skills (current code treats missing as not meeting requirement).

9 — Styling and static assets (how CSS is applied right now)

templates/base.html loads Bootstrap 5 from a CDN:

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">


The repository does not include a static/css/style.css by default in the files I inspected. If you add project-specific CSS, place it in static/css/style.css and add this to the base template after the Bootstrap link:

<link rel="stylesheet" href="{% static 'css/style.css' %}">


To make sure Django will serve project-level static assets during development, set (if not present):

STATICFILES_DIRS = [ BASE_DIR / "static" ]


in careerpath/settings.py.

The project uses CSS classes for proficiency (search for .prof-high, .prof-medium, etc. in templates or a CSS file). If you implement the color coding, put these definitions in static/css/style.css.

10 — Admin, shell & commonly used commands

Useful commands you will use often:

Create and activate venv:

python -m venv venv


Activate (Windows PowerShell):

& .\venv\Scripts\Activate.ps1


Activate (mac / linux):

source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Migrations:

python manage.py makemigrations
python manage.py migrate


Create superuser:

python manage.py createsuperuser


Run server:

python manage.py runserver


Open Django shell:

python manage.py shell


Run tests:

python manage.py test


Dump / load data:

python manage.py dumpdata > dump.json
python manage.py loaddata dump.json

11 — Troubleshooting: common problems & fixes (concise)

PowerShell blocks activation

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


requirements.txt missing / pip install fails
Install core packages manually:

pip install django django-crispy-forms widget-tweaks


Migration errors after changing AUTH_USER_MODEL
If AUTH_USER_MODEL was altered after migrations exist, do not attempt to fix lightly. If you can discard dev data, reset migrations and DB:

rm db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate


(Windows: remove with Explorer or del / rmdir as appropriate.)

Static files 404
Ensure STATICFILES_DIRS is set if you use a project-level static/ and that templates include {% load static %}.

AJAX 403 (CSRF)
Include CSRF token in headers for AJAX requests: send X-CSRFToken header with the token.

N+1 query / performance
Use select_related and prefetch_related in views fetching related objects (e.g., .select_related('skill')) to reduce DB queries.

12 — Handover checklist (what to give the next developer)

Provide the incoming developer:

GitHub URL & repository permissions.

requirements.txt (included).

db.sqlite3 (or dump.json fixture) so they can run the Quick Start without running migrations. Decide which to include.

Any environment variables or external service credentials securely (do not send passwords in chat).

A short list of current top-priority tasks and known issues (CV UI problems, match-score review, etc.).

Optional: a copy of .gitignore that excludes venv/.venv.

13 — Recommended first tasks (exact, numbered)

Clone repo and run Quick Start (above).

Log into Django admin or create a superuser if one is not provided.

Inspect accounts/models.py and positions/models.py in code and via admin to understand relationships.

Reproduce basic user flows in a browser:

Add a skill on “My Skills”.

Save a position and view saved positions.

Generate a CV PDF (if the endpoint exists).

Locate SavedPosition.match_score and confirm the behaviour against example student records; document any differences between expected product rules and code.

If desired, implement or move CSS into static/css/style.css and include it in templates/base.html.

Run tests:

python manage.py test
