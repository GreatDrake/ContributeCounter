import sqlite3 

conn = sqlite3.connect('contributers.db') 
cur = conn.cursor()

def create_table():
    cur.execute("CREATE TABLE IF NOT EXISTS countries (country TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(country));")

    
def clear_table():
    cur.execute("DELETE FROM countries WHERE country IS NOT NULL;")
    conn.commit()
    


if __name__ == '__main__':
    create_table()
    cur.close()
    conn.close()