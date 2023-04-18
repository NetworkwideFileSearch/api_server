
from file_metadata import get_all_metadata
from new_sql import dbclient
from work_with_model import transformer_ops
from playground import search_ops, jaccard_sim, cosine_sim
from common_methods import load_field_from_json


# tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
# model = AutoModel.from_pretrained("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")


# model_obj = transformer_ops("sentence-transformers@multi-qa-MiniLM-L6-cos-v1")
# model_obj.set_models_rare_case(tokenizer=tokenizer,model=model)

model_obj = transformer_ops("sentence-transformers@multi-qa-MiniLM-L6-cos-v1")
model_obj.load_model_pickle()
db_obj = dbclient("test.db")
search_obj = search_ops(k=5)


def index(path=r"C:\Users\shree\Downloads"):
    print(path)
    lis = get_all_metadata(folder_path=path)
    db_obj.create_metadata_table()
    db_obj.insert_many_data(lis)


def semantic_search():

    # while bool(stop):
    query = input("enter query: ")
    print("query :", query)
    obj = search_obj.get_top_k_docs(query,
                                    fetch_func=db_obj.fetch_id_and_vector,
                                    k=10,
                                    similarity_func=jaccard_sim,
                                    encoding_func=model_obj.encode_from_official_doc_by_HF)
    # res = list(obj)
    # for file in db_obj.get_result_per_ids(res[0]):
    #     print(file)
    #     print()
    # print("/*"*50,"\n")
    lis = list(next(obj))
    res = db_obj.fetch_metadata_of_specific_ids_in_single_sql_query(
        lis, table_name="files")

    for file in res:
        print(file[1])
    # stop = input("should i stop?press enter to stop/1 to continue")


def keyword_search():
    query = input("enter query: ")
    print("query :", query)
    res = db_obj.keyword_search(query)
    for i in res:
        print(i[1])


def compulsory_process():
    paths = load_field_from_json(
        path=r"D:\be_project_2.0\venv1\filesearch2\global_info.json", field="paths_to_index")
    print(paths)
    for path in paths:
        index(path)
        print("\n", "ok", "\n")

    db_obj.create_embeddings_table()
    rows = db_obj.get_file_metadata_for_vectorization()
    print(rows[0])
    data = [i for i in db_obj.get_id_vector_pairs_to_add_in_table(
        rows=rows, encoding_func=model_obj.encode_from_official_doc_by_HF)]
    db_obj.add_multiple_vectors(data=data)


def menu_driven_test_purpose():
    stop = 1
    while bool(stop):
        inp = input(
            "enter your choice\n1.index\n2.keyword search\n3.semantic search\n")
        if inp == "1":
            # path = input("please proveide folder path you want to index: \n")
            # index(path=path)
            compulsory_process()
        if inp == "2":
            keyword_search()
        elif inp == "3":
            semantic_search()
        else:
            print("please enter correct choice")
        stop = input("should i stop?press enter to stop/1 to continue")


if __name__ == "__main__":
    menu_driven_test_purpose()
