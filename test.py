
from fastapi import FastAPI
from pysearch.new_sql import embeddings_table
from pysearch.work_with_model import transformer_ops
from pysearch.playground import search_ops, jaccard_sim, cosine_sim
from pysearch.common_methods import *
from dataclasses import dataclass
import uvicorn










@dataclass
class ObjClass:
    """
    A class to store essential objects used for search operations.

    Attributes:
    -----------
    model_obj: object
        An object of the transformer_ops class.
    db_obj: object
        An object of the dbclient class.
    search_obj: object
        An object of the search_ops class.
    """
    model_obj: object = None
    db_obj: object = None
    search_obj: object = None


essentials = ObjClass()


app = FastAPI()


# /search - search query for the file name
# /rediscover - again check for devices in the network


def vectorize_whole_table():
    essentials.db_obj.create_embeddings_table()
    rows = essentials.db_obj.get_file_metadata_for_vectorization()
    # print(rows[0])
    data = [i for i in essentials.db_obj.get_id_vector_pairs_to_add_in_table(
        rows=rows, encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)]
    # print(data[0])
    essentials.db_obj.add_multiple_vectors(data=data, table_name="embeddings")
    return {"message": "entire table is vectorized and stored in table"}


@app.on_event("startup")
async def startup_event():
    """
    Load essential objects when the application starts.

    Returns:
    --------
    str
        A message indicating whether the objects were loaded successfully or not.
    """
    try:
        essentials.model_obj = transformer_ops(
            "sentence-transformers@multi-qa-MiniLM-L6-cos-v1")
        essentials.model_obj.load_model_pickle()
        essentials.db_obj = embeddings_table("sample.db")
        essentials.search_obj = search_ops(k=5)
        # vectorize_whole_table()
        print("loaded success")
        return "Objects loaded successfully."
    except:
        return "Failed to load objects."




@app.get("/search/{query}")
async def search_func(query: str):
    """
    Perform a search operation based on the given query.

    Parameters:
    -----------
    query: str
        The query string to search for.

    Returns:
    --------
    list
        A list of file ids in decreasing order of relevance
    """
    res = essentials.search_obj.get_top_k_docs(query,
                                               fetch_func=essentials.db_obj.fetch_id_and_vector,
                                               k=10,
                                               similarity_func=cosine_sim,
                                               encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)
    lis = list(next(res))
    # res = essentials.db_obj.keyword_search(
    #     query, table_name="files", column_name="filename")
    # files = db.query(File).filter(File.id.in_(lis)).all()
    # files.sort(key=lambda row: lis.index(row.id))
    return lis


@app.get("/delete/{file_ids}")
def delete_row(file_ids: str):
    # op = essentials.db_obj.delete_vector(
    #     file_id=int(file_id), table_name="files")
    file_ids = [int(i) for i in file_ids.split("_")]
    op = essentials.search_obj.delete_dict(*file_ids)
    if op:
        return {'message': f"file data with file_id : {file_ids} deleted successfully"}
    else:
        return {"message": f"file data  deletion unsuccessful"}


@app.get("/add_vector/{id_list}")
async def add_vector(id_list: str):
    file_ids = [int(i) for i in file_ids.split("_")]
    rows = essentials.db_obj.fetch_metadata_of_specific_ids(
        file_ids=[id_list], table_name="files")

    data = essentials.db_obj.get_id_vector_pairs_to_add_in_table(
        rows=rows, encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)

    essentials.db_obj.add_multiple_vectors(data=data, table_name="embeddings")

    op = essentials.search_obj.add_dict(*id_list)
    if op:
        return {'message': f"file data and vectors with file_ids : {id_list} added successfully"}
    else:
        return {"message": f"file data and vector addition unsuccessful"}
    
    

@app.get("/")
async def welcome():
    return "welcome to nfs"

# if __name__ == "__main__":cir
