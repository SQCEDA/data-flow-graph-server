import sqlite3
import json
from typing import List, Dict, Any

class DB:
    def __init__(self, db_path: str = "./data/data.db"):
        
        self.db_path = db_path

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS githash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashstr TEXT NOT NULL,
            projectname TEXT NOT NULL,
            owner TEXT NOT NULL,
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
            fileref JSON DEFAULT '[]',
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
    
    def query_filehash(self, input_list):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 创建参数占位符（?,?,?...）
        placeholders = ','.join(['?' for _ in input_list])
        
        # 执行查询：查找表中存在的所有匹配项
        query = f"SELECT * FROM filehash WHERE hashstr IN ({placeholders})"
        cursor.execute(query, input_list)
        
        # 获取查询结果
        results = {row[1]:row[2] for row in cursor.fetchall()}

        conn.close()

        return results

    def find_matching_filehash(self, input_list)->List[str]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 创建参数占位符（?,?,?...）
        placeholders = ','.join(['?' for _ in input_list])
        
        # 执行查询：查找表中存在的所有匹配项
        query = f"SELECT hashstr FROM filehash WHERE hashstr IN ({placeholders})"
        cursor.execute(query, input_list)
        
        # 获取查询结果
        results = [row[0] for row in cursor.fetchall()]

        conn.close()
        return results

    def add_filehash(self, input_list):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        data = [(hash_val,) for hash_val in input_list]
    
        try:
            cursor.executemany(
                "INSERT OR IGNORE INTO filehash (hashstr) VALUES (?)",
                data
            )
            conn.commit()
        except sqlite3.Error as e:
            raise e
        finally:
            conn.close()
    
    def set_filehash(self, filehashmap: Dict[str, List[str]]):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        data = [(hash_val, json.dumps(fileref, ensure_ascii=False)) for hash_val, fileref in filehashmap.items()]
    
        try:
            cursor.executemany(
                "INSERT OR REPLACE INTO filehash (hashstr, fileref) VALUES (?, ?)",
                data
            )
            conn.commit()
        except sqlite3.Error as e:
            raise e
        finally:
            conn.close()


    def find_exact_match(
        self,
        hashstr: str,
        projectname: str,
        owner: str
    ) -> List[Dict[str, Any]]:
        """
        查询 hashstr, projectname, owner 三个字段都完全匹配的条目
        返回匹配的条目数组
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT * FROM githash 
        WHERE hashstr = ? 
        AND projectname = ? 
        AND owner = ?
        ORDER BY id
        """
        
        cursor.execute(query, (hashstr, projectname, owner))
        
        # 获取结果并转换为字典列表
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            # 解析 JSON 字段
            if 'filehashmap' in row_dict and row_dict['filehashmap']:
                row_dict['filehashmap'] = json.loads(row_dict['filehashmap'])
            if 'projectfile' in row_dict and row_dict['projectfile']:
                row_dict['projectfile'] = json.loads(row_dict['projectfile'])
            results.append(row_dict)

        conn.close()
        
        return results

    def insert_githash_full(
        self,
        hashstr: str,
        projectname: str,
        owner: str,
        author: str,
        filehashmap: dict,
        projectfile: dict,
        time: str
    ):
        """
        插入完整条目，所有字段都不能为空
        
        Args:
            hashstr: 哈希字符串
            projectname: 项目名称
            owner: 所有者
            author: 作者
            filehashmap: 文件哈希映射字典
            projectfile: 项目文件字典
            time: 时间戳字符串 (格式: 'YYYY-MM-DD HH:MM:SS')

        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 将字典转换为JSON字符串
        filehashmap_json = json.dumps(filehashmap, ensure_ascii=False)
        projectfile_json = json.dumps(projectfile, ensure_ascii=False)
        
        try:
            cursor.execute("""
                INSERT INTO githash 
                (hashstr, projectname, owner, author, filehashmap, projectfile, time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (hashstr, projectname, owner, author, 
                filehashmap_json, projectfile_json, time))
            
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


    def delete_by_ids(self, id_list: List[int]) -> int:
        """
        根据ID列表批量删除记录
        
        Args:
            id_list: ID列表，如[1, 4, 5]
        
        Returns:
            删除的行数
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if not id_list:
            return 0  # 空列表不执行任何操作
        
        cursor = conn.cursor()
        
        # 创建参数占位符
        placeholders = ','.join(['?' for _ in id_list])
        
        # 构建删除语句
        query = f"DELETE FROM githash WHERE id IN ({placeholders})"
        
        try:
            cursor.execute(query, id_list)
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_release(self,
        hashstr: str,
        projectname: str,
        owner: str) -> int:
        """
        查询 hashstr, projectname, owner 三个字段都完全匹配的条目
        删除条目以及在filehash中删除对应的记录
        """

        # 查询匹配的条目
        rows = self.find_exact_match(
            hashstr=hashstr,
            projectname=projectname,
            owner=owner
        )

        if not rows:
            return 0

        try:
           
            # 删除对应的 filehash 记录
            filehashes_to_delete = []
            for row in rows:
                filehashmap = row['filehashmap']
                filehashes_to_delete.extend(filehashmap.items())

            if filehashes_to_delete:
                records = self.query_filehash([item[1] for item in filehashes_to_delete])
                for item in filehashes_to_delete:
                    hashstr = item[1]
                    if hashstr in records:
                        fileref = item[0]
                        if fileref in records[hashstr]:
                            records[hashstr].remove(fileref)
                self.set_filehash(records)

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # 删除 githash 记录
            ids_to_delete = [row['id'] for row in rows]
            placeholders = ','.join(['?' for _ in ids_to_delete])
            cursor.execute(f"DELETE FROM githash WHERE id IN ({placeholders})", ids_to_delete)

            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def submit_release(
        self,
        hashstr: str,
        projectname: str,
        owner: str,
        author: str,
        filehashmap: dict,
        projectfile: dict,
        time: str
    )->(int, List[str]):
        """
        提交发布，先检查filehashmap中的hash是否都存在于filehash表中，如果有不存在的hash，则返回错误和缺失的hash列表；如果都存在，则删除原有的release（如果有的话），并插入新的release
        """
        hashes=filehashmap.values()
        had=self.find_matching_filehash(hashes)
        missing_hashes = set(hashes) - set(had)
        if missing_hashes:
            return 0, list(missing_hashes)
        count=self.delete_release(hashstr, projectname, owner)

        records = self.query_filehash(list(filehashmap.values()))
        for fileref,hashstr in filehashmap.items():
            if fileref not in records[hashstr]:
                records[hashstr].append(fileref)
        self.set_filehash(records)

        self.insert_githash_full(
            hashstr=hashstr,
            projectname=projectname,
            owner=owner,
            author=author,
            filehashmap=filehashmap,
            projectfile=projectfile,
            time=time
        )
        return count, []


if __name__ == "__main__":
    db = DB()
    db.init_db()
    import sys
    if '-t1' in sys.argv:
        db.insert_githash_full(
            hashstr="testhash",
            projectname="testproject",
            owner="testowner",
            author="testauthor1",
            filehashmap={"file1": "hash1", "file2": "hash2"},
            projectfile={"file1": "path/to/file1", "file2": "path/to/file2"},
            time="2024-06-01 12:00:00"
        )
        print(db.find_exact_match("testhash", "testproject", "testowner"))
    if '-t2' in sys.argv:
        db.add_filehash(["hash1", "hash2", "hash3"])
        print(db.query_filehash(["hash1", "hash3", "hash1", "hash4"]))
        print(db.find_matching_filehash(["hash3", "hash2", "hash3", "hash4"]))
    if '-c' in sys.argv:
        # clear db
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM githash")
        cursor.execute("DELETE FROM filehash")
        conn.commit()
        conn.close()