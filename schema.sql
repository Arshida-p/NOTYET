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
    willingness_to_pay TEXT DEFAULT NULL, -- Optional resident budget / price expectation
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

-- 4. Completed Success Stories Table (For Feature: Success Stories)
CREATE TABLE IF NOT EXISTS success_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    need_id INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    original_problem TEXT NOT NULL,
    solution_provided TEXT NOT NULL,
    impact_summary TEXT NOT NULL,
    business_or_initiator TEXT,
    completed_date DATE,
    status TEXT DEFAULT 'completed', -- 'completed', 'resolved'
    is_demo BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE SET NULL
);

-- Helpful indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_needs_neighborhood ON needs(neighborhood);
CREATE INDEX IF NOT EXISTS idx_needs_category ON needs(category);
CREATE INDEX IF NOT EXISTS idx_needs_status ON needs(status);
CREATE INDEX IF NOT EXISTS idx_stories_category ON success_stories(category);
CREATE INDEX IF NOT EXISTS idx_stories_neighborhood ON success_stories(neighborhood);
CREATE INDEX IF NOT EXISTS idx_stories_status ON success_stories(status);

