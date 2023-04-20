"""Faiss supports several index types and metric types. Here are some of the most commonly used ones:

Index Types:

Flat: A simple brute-force index that stores all vectors in a single flat list.
IVF: An inverted file index that partitions the vectors into clusters using k-means clustering.
PCA: A Principal Component Analysis index that projects the vectors into a lower-dimensional space.
LSH: A Locality-Sensitive Hashing index that hashes vectors to buckets based on their similarity.
Metric Types:

L2: Euclidean distance metric, which is commonly used for continuous vector spaces.
IP: Inner product metric, which is commonly used for high-dimensional sparse data.
Cosine: Cosine similarity metric, which is commonly used for text and image data.

Note that there are many more index and metric types available in Faiss, and the choice of index and metric can have 
a significant impact on the performance of your search. It's important to choose the right index and metric based on 
the characteristics of your data and the requirements of your application.
"""


import numpy as np
import faiss

class faiss_index:
    def __init__(self,index_name,dim = 384):
        self.dim  = dim
        self.index = self.create_index()
        self.index_name = index_name

    def create_index(self):
        return  faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
    
    def normalize(self,vec):
        return vec/np.linalg.norm(vec)

    def load_index(self):
        self.index = faiss.read_index(self.index_name)

    def write_index(self):
        faiss.write_index(self.index,self.index_name)

    def add_multiple_vector(self,vectors,id_list,do_normalize = 1):
        if do_normalize:
            vectors= [self.normalize(vec) for vec in vectors]
         
        vectors = np.array(vectors)
        id_list = np.array(id_list)
        self.index.add_with_ids(vectors,id_list)

    def add_single_vector(self,vector,id,do_normalize = 1):
        if do_normalize:
            vector= self.normalize(vector)
         
        vector = np.array(vector).reshape(1,self.dim)
        id_list = np.array([id])
        self.index.add_with_ids(vector,id_list)


    def remove_data(self,id_list):
        id_list = np.array(id_list)
        self.index.remove_ids(id_list)

    def search_top_k(self,query_vector,k = 5,do_normalize = 1):
        if do_normalize:
            query_vector = self.normalize(query_vector)
        query_vector = query_vector.reshape(1,self.dim)
        distance,ids = self.index.search(query_vector ,k = k)
        return list(distance[0]),list(ids[0])
    
    def convert_to_dict(self,distances,ids):
        dic = {}
        for i in range(len(ids)):
            dic[ids[i]] = distances[i]
        return dic
        