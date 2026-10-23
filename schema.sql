-- NOTYET: Neighbourhood Needs & Business Opportunity Platform
-- Safe Database Initialization (Idempotent: Never drops or overwrites existing data)

-- 1. Core Needs Table
CREATE TABLE IF NOT EXISTS needs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    zip_code TEXT,
    validation_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'open', -- 'open', 'in_discussion', 'met'
    reporter_name TEXT DEFAULT 'Anonymous Resident',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Community Validations Table (For Feature 3: Community Validation)
CREATE TABLE IF NOT EXISTS validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    need_id INTEGER NOT NULL,
    supporter_name TEXT DEFAULT 'Neighbour',
    support_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE CASCADE
);

-- 3. Business Leads / Interest Table (For Feature 4: Business Opportunities)
CREATE TABLE IF NOT EXISTS business_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    need_id INTEGER NOT NULL,
    business_name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    proposal_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE CASCADE
);

-- Helpful index for fast lookups by neighborhood and category
CREATE INDEX IF NOT EXISTS idx_needs_neighborhood ON needs(neighborhood);
CREATE INDEX IF NOT EXISTS idx_needs_category ON needs(category);
CREATE INDEX IF NOT EXISTS idx_needs_status ON needs(status);
