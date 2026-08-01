import os
import sqlite3
import time
import tempfile

def setup_large_db(db_path, num_rows=50000):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        DROP TABLE IF EXISTS roasts
    ''')
    cursor.execute('''
        DROP TABLE IF EXISTS users
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip_address TEXT NOT NULL,
            user_input TEXT NOT NULL,
            roast_result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()

    # Insert some users
    cursor.execute("INSERT OR IGNORE INTO users (id, email, password) VALUES (1, 'user1@example.com', 'pwd')")
    cursor.execute("INSERT OR IGNORE INTO users (id, email, password) VALUES (2, 'user2@example.com', 'pwd')")
    cursor.execute("INSERT OR IGNORE INTO users (id, email, password) VALUES (3, 'user3@example.com', 'pwd')") # User with few roasts

    print(f"Populating database with {num_rows} historical records...")

    roast_batch = []
    for i in range(num_rows):
        if i % 3 == 0:
            user_id = 1
            ip = '192.168.1.1'
        elif i % 3 == 1:
            user_id = 2
            ip = '192.168.1.2'
        else:
            user_id = None
            ip = f'192.168.1.{10 + (i % 100)}'

        # Give user_id = 3 exactly 10 roasts scattered in the DB
        if i > 1000 and i <= 1010:
            user_id = 3

        if i < 5:
            user_id = 1
            created_at = '2026-08-01 10:00:00'
        elif i >= 5 and i < 10:
            user_id = None
            ip = '192.168.1.15'
            created_at = '2026-08-01 11:00:00'
        else:
            created_at = '2026-07-15 08:30:00'

        roast_batch.append((user_id, ip, 'Startup idea pitch text...', '{}', created_at))

    cursor.executemany('''
        INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', roast_batch)
    conn.commit()
    conn.close()

def run_benchmarks(db_path, run_optimized=False):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if run_optimized:
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_roasts_user_created
            ON roasts (user_id, created_at DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_roasts_ip_user_created
            ON roasts (ip_address, user_id, created_at DESC)
        ''')
        conn.commit()
    else:
        # Drop indexes to ensure accurate comparison
        cursor.execute('DROP INDEX IF EXISTS idx_roasts_user_created')
        cursor.execute('DROP INDEX IF EXISTS idx_roasts_ip_user_created')
        conn.commit()

    # Query 1: Loading history for user_id = 3 (sorted) who only has 10 rows
    q1_sql = '''
        SELECT id, user_input, roast_result, created_at
        FROM roasts
        WHERE user_id = ?
        ORDER BY created_at DESC
    '''

    # Query 2: Daily limit check for user_id = 1
    q2_unopt = '''
        SELECT COUNT(*) FROM roasts
        WHERE user_id = ? AND date(created_at) = date('now')
    '''
    q2_opt = '''
        SELECT COUNT(*) FROM roasts
        WHERE user_id = ? AND created_at >= date('now')
    '''

    # Query 3: Daily limit check for anonymous IP '192.168.1.15'
    q3_unopt = '''
        SELECT COUNT(*) FROM roasts
        WHERE ip_address = ? AND user_id IS NULL AND date(created_at) = date('now')
    '''
    q3_opt = '''
        SELECT COUNT(*) FROM roasts
        WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
    '''

    # Run Query 1 Benchmark
    iterations = 50
    start = time.perf_counter()
    for _ in range(iterations):
        cursor.execute(q1_sql, (3,))
        cursor.fetchall()
    q1_time = (time.perf_counter() - start) / iterations * 1000.0

    # Run Query 2 Benchmark
    q2_sql = q2_opt if run_optimized else q2_unopt
    start = time.perf_counter()
    for _ in range(iterations):
        cursor.execute(q2_sql, (1,))
        cursor.fetchone()
    q2_time = (time.perf_counter() - start) / iterations * 1000.0

    # Run Query 3 Benchmark
    q3_sql = q3_opt if run_optimized else q3_unopt
    start = time.perf_counter()
    for _ in range(iterations):
        cursor.execute(q3_sql, ('192.168.1.15',))
        cursor.fetchone()
    q3_time = (time.perf_counter() - start) / iterations * 1000.0

    conn.close()
    return q1_time, q2_time, q3_time

if __name__ == '__main__':
    db_path = os.path.join(tempfile.gettempdir(), 'roastlab_bench.db')
    setup_large_db(db_path)

    print("\n--- Running BEFORE Optimization Benchmarks ---")
    q1_b, q2_b, q3_b = run_benchmarks(db_path, run_optimized=False)
    print(f"Query 1 (User History Load): {q1_b:.3f} ms")
    print(f"Query 2 (User Limit Check):  {q2_b:.3f} ms")
    print(f"Query 3 (IP Limit Check):    {q3_b:.3f} ms")

    print("\n--- Running AFTER Optimization Benchmarks ---")
    q1_a, q2_a, q3_a = run_benchmarks(db_path, run_optimized=True)
    print(f"Query 1 (User History Load): {q1_a:.3f} ms")
    print(f"Query 2 (User Limit Check):  {q2_a:.3f} ms")
    print(f"Query 3 (IP Limit Check):    {q3_a:.3f} ms")

    print("\n=== SPEEDUP MULTIPLIERS ===")
    print(f"Query 1: {q1_b / q1_a:.1f}x faster")
    print(f"Query 2: {q2_b / q2_a:.1f}x faster")
    print(f"Query 3: {q3_b / q3_a:.1f}x faster")

    with open('bench_after.txt', 'w') as f:
        f.write(f"Before:\nQ1={q1_b:.3f}ms, Q2={q2_b:.3f}ms, Q3={q3_b:.3f}ms\n")
        f.write(f"After:\nQ1={q1_a:.3f}ms, Q2={q2_a:.3f}ms, Q3={q3_a:.3f}ms\n")
        f.write(f"Multipliers:\nQ1={q1_b / q1_a:.1f}x, Q2={q2_b / q2_a:.1f}x, Q3={q3_b / q3_a:.1f}x\n")
