import sqlite3

class DB:
    def __init__(self, db_path: str = "./data/data.db"):
        
        self.db_path = db_path

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS githash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashstr TEXT NOT NULL,
            project TEXT NOT NULL,
            author TEXT NOT NULL,

            filehashmap JSON DEFAULT '{}',       
            projectfile JSON DEFAULT '{}',    

            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS filehash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashstr TEXT UNIQUE NOT NULL,
            fileref JSON DEFAULT '[]'
        )
        """)

        conn.commit()
        conn.close()
    

    def find_matching_filehash(input_list):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 创建参数占位符（?,?,?...）
        placeholders = ','.join(['?' for _ in input_list])
        
        # 执行查询：查找表中存在的所有匹配项
        query = f"SELECT DISTINCT hashstr FROM filehash WHERE hashstr IN ({placeholders})"
        cursor.execute(query, input_list)
        
        # 获取查询结果
        results = [row[0] for row in cursor.fetchall()]

        conn.close()

        return results

