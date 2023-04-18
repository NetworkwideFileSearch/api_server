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


import faiss

class FaissIndex:
    def __init__(self, dim, index_type='Flat', metric_type='L2'):
        self.dim = dim
        self.index_type = index_type
        self.metric_type = metric_type
        self.index = self._create_index()
        
    def add_vectors(self, vectors):
        if self.index is None:
            self.index = self._create_index()
        else:
            # Reconstruct the index to free memory before adding new vectors
            self.index.reset()
        self.index.add(vectors)
        
    def reconstruct_index(self):
        if self.index is not None:
            self.index.reset()
            self.index = None
        
    def search(self, query_vectors, k):
        if self.index is None:
            raise ValueError("Index has not been created yet.")
        distances, indices = self.index.search(query_vectors, k)
        return distances, indices
        
    def _create_index(self):
        if self.index_type == 'Flat':
            index = faiss.IndexFlat(self.dim, self.metric_type)
        elif self.index_type == 'IVF':
            index =  faiss.IndexFlat(self.dim, self.metric_type)
              
        elif self.index_type == 'PCA':
            pca_matrix = faiss.PCAMatrix(self.dim, 10)
            index = faiss.IndexPreTransform(pca_matrix, self._create_index())
        elif self.index_type == 'LSH':
            index = faiss.IndexLSH(self.dim, 8)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        return index
