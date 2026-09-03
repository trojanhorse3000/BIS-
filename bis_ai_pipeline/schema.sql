CREATE TABLE IF NOT EXISTS standards (
    is_number TEXT PRIMARY KEY,
    title TEXT,
    part_or_section TEXT,
    edition_year TEXT,
    ics_code TEXT,
    technical_committee TEXT,
    standard_type TEXT,
    status TEXT,
    publication_or_revision_date TEXT,
    bis_page_url TEXT,
    pdf_url TEXT,
    access_type TEXT,
    retrieved_at TEXT
);

CREATE TABLE IF NOT EXISTS crosswalk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    product_category TEXT,
    scheme TEXT,
    is_number TEXT,
    is_title TEXT,
    qco_number TEXT,
    ministry TEXT,
    notification_date TEXT,
    effective_date TEXT,
    amendment TEXT,
    source_url TEXT,
    retrieved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_crosswalk_category ON crosswalk(product_category);
CREATE INDEX IF NOT EXISTS idx_crosswalk_is_number ON crosswalk(is_number);

CREATE TABLE IF NOT EXISTS ahc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ahc_name TEXT, address TEXT, state TEXT, district TEXT, contact TEXT,
    recognition_status TEXT, scope TEXT, source_url TEXT, retrieved_at TEXT
);

CREATE TABLE IF NOT EXISTS labs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_name TEXT, state TEXT, status TEXT, osl_code TEXT, scope TEXT,
    source_url TEXT, retrieved_at TEXT
);

CREATE TABLE IF NOT EXISTS huid_reference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gold_fineness_grade TEXT, caratage TEXT, huid_length INTEGER,
    mark_components TEXT, verification_method TEXT, source_url TEXT
);
