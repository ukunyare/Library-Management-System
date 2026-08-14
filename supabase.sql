-- ============================================================
--  BookWise - Library Management System - Supabase Schema
--  Run this in: Supabase Dashboard -> SQL Editor -> New query
-- ============================================================

-- ---------- ADMINS ----------
CREATE TABLE IF NOT EXISTS admins (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    created_at    TIMESTAMP    DEFAULT now()
);

-- ---------- BOOKS ----------
CREATE TABLE IF NOT EXISTS books (
    id               SERIAL PRIMARY KEY,
    book_id          VARCHAR(50)  NOT NULL UNIQUE,
    title            VARCHAR(200) NOT NULL,
    author           VARCHAR(120) NOT NULL,
    category         VARCHAR(80),
    publisher        VARCHAR(120),
    published_year   INTEGER,
    total_copies     INTEGER      NOT NULL DEFAULT 1,
    available_copies INTEGER      NOT NULL DEFAULT 1,
    description      TEXT,
    created_at       TIMESTAMP    DEFAULT now()
);

-- ---------- MEMBERS ----------
CREATE TABLE IF NOT EXISTS members (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    email       VARCHAR(120) UNIQUE,
    phone       VARCHAR(20),
    address     VARCHAR(255),
    joined_date DATE         DEFAULT CURRENT_DATE,
    created_at  TIMESTAMP    DEFAULT now()
);

-- ---------- TRANSACTIONS ----------
CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    book_id     INTEGER     NOT NULL REFERENCES books(id)    ON DELETE CASCADE,
    member_id   INTEGER     NOT NULL REFERENCES members(id)  ON DELETE CASCADE,
    issue_date  DATE        NOT NULL DEFAULT CURRENT_DATE,
    due_date    DATE        NOT NULL,
    returned_at DATE,
    fine        FLOAT       DEFAULT 0,
    status      VARCHAR(20) NOT NULL DEFAULT 'issued'
);

-- ---------- INDEXES ----------
CREATE INDEX IF NOT EXISTS idx_books_book_id  ON books (book_id);
CREATE INDEX IF NOT EXISTS idx_books_title    ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author   ON books (author);
CREATE INDEX IF NOT EXISTS idx_members_name   ON members (name);
CREATE INDEX IF NOT EXISTS idx_members_email  ON members (email);
CREATE INDEX IF NOT EXISTS idx_tx_book_id     ON transactions (book_id);
CREATE INDEX IF NOT EXISTS idx_tx_member_id   ON transactions (member_id);
CREATE INDEX IF NOT EXISTS idx_tx_status      ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_tx_due_date    ON transactions (due_date);

-- ---------- DEFAULT ADMIN (username: admin / password: admin123) ----------
-- Login works only if you run this once. Change the password after login.
INSERT INTO admins (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$U3rN0l7yni6PamAb$0ec947de2bbbf8db8e73d4882400aed1f35f014d394d352e6b10614622c84b5b8ba24ac9771fc674260fa695d7abeae7c5a9689f7e501395c49f43e622650aa7')
ON CONFLICT (username) DO NOTHING;

-- ============================================================
--  OPTIONAL SAMPLE DATA (delete these two blocks if not needed)
-- ============================================================

-- Sample books
INSERT INTO books (book_id, title, author, category, publisher, published_year, total_copies, available_copies, description) VALUES
    ('505-303', 'The Great Gatsby',    'F. Scott Fitzgerald', 'Fiction',     'Scribner', 1925, 3, 3, 'Classic novel about the Jazz Age.'),
    ('505-304', '1984',                'George Orwell',       'Fiction',     'Secker & Warburg', 1949, 2, 2, 'Dystopian social science fiction.'),
    ('505-305', 'Atomic Habits',       'James Clear',         'Self-Help',   'Avery', 2018, 4, 4, 'How to build good habits and break bad ones.')
ON CONFLICT (book_id) DO NOTHING;

-- Sample members
INSERT INTO members (name, email, phone, address) VALUES
    ('Jane Doe',  'jane@example.com',  '555-0101', '1 Main Street'),
    ('John Roe',  'john@example.com',  '555-0102', '2 Second Avenue')
ON CONFLICT (email) DO NOTHING;

-- ============================================================
--  DONE - now start the Flask app and it will use this database
-- ============================================================