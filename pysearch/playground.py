
import numpy as np
from .work_with_model import transformer_ops as tr_ops


def jaccard_sim(x, y):
    """
    Calculate the Jaccard similarity between two NumPy arrays x and y.
    """
    x = np.array(x)
    y = np.array(y)
    intersection = np.sum(x * y)
    union = np.sum((x + y) > 0)
    return intersection / union


def cosine_sim(array1, array2):
    # calculate dot product
    dot_product = np.dot(array1, array2)

    # calculate magnitudes
    magnitude1 = np.linalg.norm(array1)
    magnitude2 = np.linalg.norm(array2)

    # calculate cosine similarity
    return dot_product / (magnitude1 * magnitude2)


class search_ops:

    def __init__(self, k=10):
        self.k = k
        self.doc_encoding_iter = None
        # self.encoding_func = encoding_func

    def convert_to_dict(self, rows):
        try:
            dic = {}
            for id, vec in rows:
                dic[id] = vec
            print("fetch_func result convert to dict successful")
            return dic
        except:
            raise KeyError(
                "failure : adding id,vector pairs as dictionary failed")

    def add_dict(self, id_vec_pair):
        try:
            id, vec = id_vec_pair
            self.doc_encoding_iter[id] = vec
            return "success"
        except:
            return False

    def delete_dict(self, id):
        try:
            del self.doc_encoding_iter[id]
            return "success"
        except:
            return False

    def similarity_score_cal(self, query, fetch_func, similarity_func, encoding_func):
        """
        A function that fetches the top k most similar items to a given input
        using a pre-trained model.
        """

        query_embedding = encoding_func(query)

        if self.doc_encoding_iter is None:
            self.doc_encoding_iter = self.convert_to_dict(fetch_func())

        for id in self.doc_encoding_iter:
            # file_id = id   # doc_embedding = self.doc_encoding_iter[id]
            similarity_score = similarity_func(
                query_embedding, self.doc_encoding_iter[id])
            yield (id, similarity_score)

    def get_top_k_docs(self, query, fetch_func, similarity_func, encoding_func, k=10):
        similarity_scores = self.similarity_score_cal(
            query, fetch_func=fetch_func, similarity_func=similarity_func, encoding_func=encoding_func)
        sorted_tuples = sorted(
            similarity_scores, key=lambda x: x[1], reverse=True)
        result_dict = {}
        for i in range(min(len(sorted_tuples), k)):
            id, score = sorted_tuples[i]
            result_dict[id] = score

        return result_dict


# if __name__ == "__main__":
#     modelobj = tr_ops("GPT_125M")
#     db_obj = sql_ops('filesearch.db')
#     search_obj = search_ops(k = 10 )


#     stop = 1
#     while bool(stop):
#         query = input("enter query: ")
#         print("query :" ,query)
#         obj =  search_obj.get_top_k_docs(query,db_obj=db_obj,model_obj=modelobj,k=10,similarity_func=jaccard_sim)
#         res = list(next(obj))
#         for file in db_obj.get_result_per_ids(res):
#             print(file)
#             print()
#         print("/*"*50,"\n")
#         stop = input("should i stop?press enter to stop/1 to continue")
