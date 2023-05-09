import sqlite3
import os
import json
from .common_methods import *


class sql_ops:
    def __init__(self, db_name="sample.db"):
        self.__parent_dir = parent_dir
        self.__db_name = db_name
        self.__db_path = os.path.join(parent_dir, "FolderSync", db_name)

    def create_connection(self):
        try:
            conn = sqlite3.connect(self.__db_path)
            return conn
        except sqlite3.Error as e:
            print(e)
        return None

    def execute_query(self, conn, query, params=()):
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except sqlite3.Error as e:
            print(e)
        return None

    def execute_many(self, conn, query, list_of_params):
        try:
            cursor = conn.cursor()
            cursor.executemany(query, list_of_params)
            cursor.close()
        except sqlite3.Error as e:
            print(e)


class embeddings_table(sql_ops):

    def create_embeddings_table(self, table_name="embeddings", main_table="files"):
        conn = self.create_connection()
        query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                file_id INTEGER PRIMARY KEY,
                vectors TEXT,
                FOREIGN KEY (file_id) REFERENCES {main_table} (file_id)
                on delete cascade
            )
            '''
        self.execute_query(conn, query)
        conn.commit()
        conn.close()

    def delete_vector(self, file_id, table_name="embeddings"):
        conn = self.create_connection()
        # qf = "PRAGMA foreign_keys=ON"
        # self.execute_query(conn, qf)
        query = f"DELETE FROM {table_name} WHERE id = {file_id}"
        res = self.execute_query(conn, query)
        conn.commit()
        conn.close()
        return res

    def delete_multiple_vectors(self, file_ids, table_name="embeddings"):
        conn = self.create_connection()
        query = "DELETE FROM {} WHERE file_id IN ({})".format(
            table_name, ",".join(str(id) for id in file_ids)
        )
        self.execute_query(conn, query)
        conn.commit()
        conn.close()

    def add_vector(self, file_id, vector, table_name="embeddings"):
        conn = self.create_connection()
        query = "INSERT INTO ? (file_id, vectors) VALUES (?, ?)".format(
            table_name)
        self.execute_query(conn, query, (table_name, file_id, vector))
        conn.commit()
        conn.close()

    def add_multiple_vectors(self, data, table_name="embeddings"):
        # `data` should be a list of tuples in the format (file_id, vector)
        conn = self.create_connection()
        query = "INSERT INTO {} (file_id, vectors) VALUES (?, ?)".format(
            table_name)
        self.execute_many(conn, query, data)
        conn.commit()
        conn.close()

    def load_vector_normal_form(self, obj):
        return json.loads(obj)
    
    def fetch_single_id_and_vector(self,file_id, table_name="embeddings"):
        try:
            conn = self.create_connection()
            query = f"select file_id,vectors from {table_name} where file_id = {str(file_id)}"
            rows = self.execute_query(conn, query)
            if rows:
                row = rows[0]
                return (row[0], self.load_vector_normal_form(row[-1]))
            else:
                raise KeyError("file id not found in database table embeddings")

        except sqlite3.Error as e:
            print(e)
        return None

    def fetch_id_and_vector(self, table_name="embeddings"):
        try:
            conn = self.create_connection()
            query = f"select file_id,vectors from {table_name}"
            rows = self.execute_query(conn, query)
            # Convert the encoding column to numpy arrays
            print("are rows none ", rows == None)
            lis = []
            for row in rows:
                lis.append((row[0], self.load_vector_normal_form(row[-1])))

            return lis

        except sqlite3.Error as e:
            print(e)
        return None

    def dump_vector_in_json_form(self, vector):
        return json.dumps(vector.tolist())

    def get_id_vector_pairs_to_add_in_table(self, rows, encoding_func):
        """
        here take input of list of tuples each single tuple consistes of all filemetadata
        """
        for row in rows:
            content = make_file_content(row[1:])
            # here i am using only file name for vectorisation
            encoding = encoding_func(content)
            # id = row[0]
            yield (row[0], self.dump_vector_in_json_form(encoding))

    def get_file_metadata_for_vectorization(self, table_name="files"):
        conn = self.create_connection()
        query = f"select * from {table_name}"
        res = self.execute_query(conn, query)
        conn.commit()
        conn.close()
        return res

    def fetch_metadata_of_specific_ids(self, file_ids, table_name="files", column_name="id"):
        conn = self.create_connection()
        query = f"SELECT * FROM {table_name} WHERE {column_name} IN ({','.join('?'*len(file_ids))})"
        res = self.execute_query(conn, query, file_ids)
        conn.commit()
        conn.close()
        return res
    
    def fetch_metadata_of_ids(self, file_ids, table_name="files", column_name="id"):
        conn = self.create_connection()
        for id in file_ids:
            query = "SELECT * FROM {} WHERE {} = {};".format(table_name,column_name,str(id))
            res = self.execute_query(conn, query)
            # print(res)
            yield res
        conn.commit()
        conn.close()
        

    def keyword_search(self, query, table_name="files", column_name="file_name"):
        conn = self.create_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM {} WHERE {} LIKE ?".format(
            table_name, column_name)
        cursor.execute(sql, ('%{}%'.format(query),))
        res = cursor.fetchall()
        conn.commit()
        conn.close()
        return res


# this table is not used in main integration but still dont delete it
class metadata_table(sql_ops):
    def create_metadata_table(self):
        conn = self.create_connection()
        query = '''
        CREATE TABLE  if not exists metadata (
            file_id integer primary key autoincrement,
            file_name text,
            file_type text,
            file_size integer,
            creation_date text, 
            file_location text
            
        );
        '''
        self.execute_query(conn, query)
        print("success")
        conn.commit()
        conn.close()

    def insert_data(self, file_name, file_path, created_date, modified_date, size):
        conn = self.create_connection()
        query = "INSERT INTO metadata ( file_name,file_type,file_size,creation_date,file_location ) VALUES (?,?,?,?,?)"

        params = (file_name, file_path, created_date, modified_date, size)
        self.execute_query(conn, query, params)
        conn.commit()
        conn.close()

    def insert_many_data(self, list_of_data):
        conn = self.create_connection()
        query = "INSERT INTO metadata ( file_name,file_type,file_size,creation_date, file_location ) VALUES (?,?,?,?,?)"

        self.execute_many(conn, query, list_of_data)

        conn.commit()
        conn.close()

    # def fetch_metadata_of_specific_ids(self, file_ids, table_name="files"):
    #     conn = self.create_connection()
    #     query = "SELECT * FROM {table_name} WHERE file_id = ?"
    #     res = []
    #     for id in file_ids:
    #         cur = conn.cursor()
    #         cur.execute(query, (id,))
    #         res.append(cur.fetchone())
    #         cur.close()
    #     conn.commit()
    #     conn.close()
    #     return res

    def fetch_metadata_of_specific_ids(self, file_ids, table_name="files", column_name="file_id"):
        conn = self.create_connection()
        query = f"SELECT * FROM {table_name} WHERE {column_name} IN ({','.join('?'*len(file_ids))})"
        res = self.execute_query(conn, query, file_ids)
        conn.commit()
        conn.close()
        return iter(res)

    def keyword_search(self, query, table_name="files", column_name="file_name"):
        conn = self.create_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM {} WHERE {} LIKE ?".format(table_name, file_name)
        cursor.execute(sql, ('%{}%'.format(query),))
        res = cursor.fetchall()
        conn.commit()
        conn.close()
        return res
