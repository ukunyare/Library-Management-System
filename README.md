# BookWise — Library Management System

A simple, clean, and modern Library Management System built with **Flask (Python)** and **Tailwind CSS**.

## Features

- Admin login/logout with hashed passwords (Flask-Login)
- Dashboard with live stats: total books, copies, members, issued, returned, overdue
- Book CRUD: add, edit, delete, view, search (by Book ID, title, author, category), pagination
- User-managed **Book ID** (e.g. `505-303`): unique, set when adding a book, shown in Books, Transactions, and everywhere else
- Member CRUD: add, edit, delete, view, search, pagination
- Issue and return books with due-date tracking
- Automatic overdue detection and per-day fine calculation
- Overdue list with projected fines and one-click "Return & Charge"
- Flash messages for success / error / warning
- Responsive sidebar layout with mobile drawer
- SQLite by default (MySQL-ready via `DATABASE_URL`)

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** and sign in with the default admin:

| Username | Password  |
|----------|-----------|
| `admin`  | `admin123` |

The default admin is created automatically on first run. Change the password after login (or via the database) for production use.

## Configuration

Set environment variables to override defaults (see `config.py`):

```bash
# Use MySQL instead of SQLite
set DATABASE_URL=mysql+pymysql://user:pass@localhost/library

# Session secret
set SECRET_KEY=change-me

# Loan period in days (default 14) and fine per overdue day (default $1.00)
set ISSUE_DAYS=21
set FINE_PER_DAY=2.0
```

## Project Structure

```
Library Management System/
├── app.py              # App factory, blueprints, error handlers
├── config.py           # Configuration (SQLite/MySQL, loan rules)
├── extensions.py       # db & login_manager singletons
├── models.py           # Admin, Book, Member, Transaction
├── routes/
│   ├── auth.py         # login / logout
│   ├── dashboard.py    # stats and quick lists
│   ├── books.py        # book CRUD + search
│   ├── members.py      # member CRUD + search
│   └── transactions.py # issue / return / overdue
├── templates/
│   ├── base.html       # layout: sidebar, topbar, flash
│   ├── login.html
│   ├── dashboard.html
│   ├── books/  members/  transactions/  errors/
│   └── partials/       # flash, pagination, badges
├── static/
│   ├── css/style.css
│   └── js/main.js      # sidebar, flash, confirm dialogs
├── requirements.txt
└── README.md
```

## Notes

- Tailwind CSS is **pre-compiled** to a static file (`static/css/tailwind.css`) — no CDN, no runtime JS, works fully offline.
- After editing templates or `tailwind.config.js`, rebuild the stylesheet:

  ```bash
  npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify
  ```

- The DB file `library.db` is created automatically on first run.
- Books cannot be deleted while copies are issued; members cannot be deleted while they hold books.
- Returned books accrue a fine of `FINE_PER_DAY` for each day past the due date.