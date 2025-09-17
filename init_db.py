import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "itinerary_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432)
}

# Create table SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS poi (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    budget_level TEXT,
    travel_style TEXT,
    location TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
"""

# Sample POIs with lat/lon
SAMPLE_DATA = [
    ("Tasek Lama Recreational Park", "alam", "low", "relaxed", "Bandar Seri Begawan",
     "Nature hike and waterfall spot", 4.8990, 114.9515),
    ("Gadong Night Market", "kuliner", "low", "family-friendly", "Gadong",
     "Local street food experience", 4.9072, 114.9163),
    ("Brunei Museum", "sejarah", "medium", "relaxed", "Kota Batu",
     "Cultural and history exhibits", 4.8672, 114.9421),
    ("Jerudong Park Playground", "santai", "medium", "family-friendly", "Jerudong",
     "Relaxing park with leisure areas", 4.9442, 114.8256),
]

def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Drop old table if exists
        cur.execute("DROP TABLE IF EXISTS poi;")
        print("⚡ Dropped old 'poi' table if existed.")

        # Create new table
        cur.execute(CREATE_TABLE_SQL)
        print("✅ 'poi' table created.")

        # Insert sample data
        for poi in SAMPLE_DATA:
            cur.execute(
                "INSERT INTO poi (name, category, budget_level, travel_style, location, description, latitude, longitude) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                poi,
            )
        print("✅ Sample POIs inserted.")

        conn.commit()
        cur.close()
        conn.close()
        print("🎉 Database initialized successfully!")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
