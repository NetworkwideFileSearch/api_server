
import numpy as np
from  .work_with_model import transformer_ops as tr_ops



def jaccard_sim(x, y):
    """
    Calculate the Jaccard similarity between two NumPy arrays x and y.
    """
    x = np.array(x)
    y = np.array(y)
    intersection = np.sum(x * y)
    union = np.sum((x + y) > 0)
    return intersection / union


def cosine_sim(array1,array2):
    # calculate dot product
    dot_product = np.dot(array1, array2)

    # calculate magnitudes
    magnitude1 = np.linalg.norm(array1)
    magnitude2 = np.linalg.norm(array2)

    # calculate cosine similarity
    return dot_product / (magnitude1 * magnitude2)



class search_ops:

    def __init__(self,k= 10 ):
        self.k = k
        self.doc_encoding_iter = None
        # self.encoding_func = encoding_func



    def similarity_score_cal(self,query,fetch_func,similarity_func,encoding_func):
        """
        A function that fetches the top k most similar items to a given input
        using a pre-trained model.
        """
        
        
        query_embedding = encoding_func(query)

        if self.doc_encoding_iter is None:
            self.doc_encoding_iter = fetch_func()
    
        for doc in self.doc_encoding_iter:
            file_id = doc[0]
            doc_embedding = doc[1]
            similarity_score =  similarity_func(query_embedding, doc_embedding)
            yield (file_id,similarity_score)


    def get_top_k_docs(self,query,fetch_func,similarity_func,encoding_func,k = 10 ):
        similarity_scores = self.similarity_score_cal(query,fetch_func=fetch_func,similarity_func=similarity_func,encoding_func= encoding_func)
        sorted_tuples = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        for i in range(0,len(sorted_tuples),k):
            yield [row[0] for row in sorted_tuples[i:i+k]]


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
        
    




    


    