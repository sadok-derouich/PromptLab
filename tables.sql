-- SYSTEM PROMPTS TABLE
CREATE TABLE IF NOT EXISTS system_prompts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content TEXT,
    creation_date TIMESTAMP,
    last_update TIMESTAMP,
    comment TEXT,
    UNIQUE(name, version)
);

-- USER PROMPTS TABLE
CREATE TABLE IF NOT EXISTS user_prompts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    content TEXT,
    creation_date TIMESTAMP,
    comment TEXT,
    UNIQUE(name, version)
);

-- OUTPUTS TABLE (joins prompts with metadata and rankings)
CREATE TABLE IF NOT EXISTS outputs (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES system_prompts(id),
    user_id INTEGER REFERENCES user_prompts(id),
    api TEXT,
    model TEXT,
    temperature REAL,
    response_time REAL,
    response TEXT,
    ranking INTEGER,
    comment TEXT, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
