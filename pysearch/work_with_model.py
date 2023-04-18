import numpy as np
import pickle
import os
import torch
import transformers
from functools import lru_cache
from .common_methods import parent_dir,load_pickle_obj,save_pickle_obj





class transformer_ops:

    def __init__(self,name):
        self.__parent_dir       = parent_dir
        self.__is_model_present = False
        self.__model_name       = name
        self.__model_path       = None
        self.__tokenizer_path   = None
        self.__loaded_model     = None
        self.__loaded_tokenizer = None
        self.setter()

    def access_model_for_testing(self):
        if not self.__loaded_model or not self.__loaded_tokenizer:
            self.load_model_pickle()
        return (self.__loaded_tokenizer,self.__loaded_model)
    
    def set_models_rare_case(self,tokenizer,model):
        self.__loaded_model = model
        self.__loaded_tokenizer= tokenizer

    def get_data_for_testing_purpose(self):
        print(self.__is_model_present)
        print(self.__model_name)
        print(self.__model_path)
        print(self.__tokenizer_path)


    
    def setter(self):
        self.__model_path     =  os.path.join(self.__parent_dir,"models")
        self.__tokenizer_path =  os.path.join(self.__parent_dir,"models")
        
        self.__model_name = self.__model_name.replace("/","@")
            
        model_folder = os.path.join(self.__model_path,self.__model_name)

        if not os.path.exists(model_folder):
            os.makedirs(model_folder)
        else:
            if not os.path.exists(os.path.join(model_folder,"model.pkl")):
                print("Directory already exists but model not downloaded")
            else:
                print("Directory already exists and model also downloaded")
                self.__is_model_present = True

        self.__model_path     =  os.path.join(model_folder,"model.pkl")
        self.__tokenizer_path =  os.path.join(model_folder,"tokenizer.pkl")
        



    #Mean Pooling - Take average of all tokens
    def mean_pooling(self,model_output, attention_mask):
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    #Encode text
    def encode_from_official_doc_by_HF(self,texts,do_normalize = False):
       
        # Tokenize sentences
        encoded_input = self.__loaded_tokenizer(texts, padding=True, truncation=True, return_tensors='pt')

        # Compute token embeddings
        with torch.no_grad():
            model_output = self.__loaded_model(**encoded_input, return_dict=True)

        # Perform pooling
        embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Normalize embeddings
        if do_normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings[0]
    
    def download_and_save_model_pickle(self, model_name: str, tokenizer_class: str, model_class: str) -> None:
        """
        Downloads a pre-trained model and tokenizer from Hugging Face's Transformers library and saves them as pickle files.

        Args:
            model_name (str): Name of the pre-trained model to download.
            tokenizer_class (str): Name of the tokenizer class to use for the pre-trained model.
            model_class (str): Name of the model class to use for the pre-trained model.

        Returns:
            None: The function does not return anything, it just saves the pre-trained model and tokenizer as pickle files.

        Raises:
            None: The function does not raise any exceptions.

        Example:
            download_and_save_model_pickle('bert-base-uncased', 'BertTokenizer', 'BertModel')

        Note:
            This function assumes that the pre-trained model and tokenizer do not exist in the specified file paths, and will download and save them if they are not present. If they already exist, the function will print a message indicating that the model has already been downloaded and will not download it again.
        """

        if self.__is_model_present:
            print(f"{model_name} already exists no need to download again ...")
        else:
            tokenizer =   getattr(transformers, tokenizer_class).from_pretrained(model_name) 
            model     =   getattr(transformers,model_class).from_pretrained(model_name)
            # print(__model_path)
            save_pickle_obj(obj = tokenizer,path= self.__tokenizer_path)
            save_pickle_obj(obj = model,path= self.__model_path)





    def load_model_pickle(self) -> None:
        """
        Loads a pre-trained model and tokenizer from pickle files and stores them as instance variables.

        Args:
            None: This function does not take any arguments.

        Returns:
            None: This function does not return anything, it just loads the pre-trained model and tokenizer from pickle files.

        Raises:
            None: This function does not raise any exceptions.

        Example:
            load_model_pickle()

        Note:
            This function assumes that the pre-trained model and tokenizer exist in the specified file paths, and will load them into instance variables if they are not already loaded. If they are already loaded, the function will not load them again.
        """
        if self.__loaded_model is None:
            self.__loaded_model = load_pickle_obj(self.__model_path)
        if self.__loaded_tokenizer is None:
            self.__loaded_tokenizer = load_pickle_obj(self.__tokenizer_path)
        


    def encode_single_doc(self, text: str) -> np.ndarray:
        """
        Encodes a single document by generating a vector representation using a pre-trained model and tokenizer.

        Args:
            text (str): The text to be encoded.

        Returns:
            np.ndarray: A numpy array representing the vector embedding of the input text.

        Raises:
            None: This function does not raise any exceptions.

        Example:
            encode_single_doc("This is an example sentence to be encoded.")

        Note:
            This function assumes that the pre-trained model and tokenizer have been loaded using the `load_model_pickle` method. If they have not been loaded, this method will load them automatically. 
        """

        self.load_model_pickle()
        # Tokenize the text and convert to input format for the model
        input_ids = self.__loaded_tokenizer(text, return_tensors='pt').input_ids
        
        # Generate the vector representation using the model
        with torch.no_grad():
            outputs = self.__loaded_model(input_ids)
            embeddings = outputs.pooler_output
            
        # Return the vector representation as a numpy array
        # print(len(embeddings.numpy()[0]))
        return embeddings.numpy()[0]


 
    def quantize_model(tokenizer, model ,module_types, dtype: torch.dtype):
        # define a dummy input sequence
        input_ids = tokenizer.encode("Hello, how are you?")[:128]
        dummy_input = torch.tensor([input_ids])

        # quantize the model and tokenizer
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            set(module_types),
            dtype=dtype
        )
        quantized_tokenizer = torch.quantization.quantize_dynamic(
            tokenizer,
            dtype=dtype
        )

        # return the quantized tokenizer and model
        return quantized_tokenizer, quantized_model








# ////////////////*****************************************************************************************/////////////////////////

# def download_and_save_model_bin(model_name):
#     # Define the model name and path
   
#     save_path = "models/{}".format(model_name)

#     # Create the directory to store the tokenizer and model
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)
#         os.makedirs("{}/model".format(save_path))
#         os.makedirs("{}/tokenizer".format(save_path))

#     # Download the tokenizer and model
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForSequenceClassification.from_pretrained(model_name)

#     # Save the tokenizer and model to their respective directories
#     tokenizer.save_pretrained("{}/tokenizer".format(save_path))
#     model.save_pretrained("{}/model".format(save_path))


# @lru_cache
# def load_model_bin(model_name = "sentence-transformers/paraphrase-MiniLM-L3-v2"):
#     load_path = "models/{}".format(model_name)

#     # Load the tokenizer and model
#     loaded_tokenizer = AutoTokenizer.from_pretrained("{}/tokenizer".format(load_path))
#     loaded_model = AutoModelForSequenceClassification.from_pretrained("{}/model".format(load_path))
#     print(loaded_model is None)
#     return (loaded_model,loaded_tokenizer)



# def encode_model_bin(text):
#     # Tokenize the text and convert to input format for the model
#     __loaded_model,__loaded_tokenizer = load_model_bin()
#     input_ids = __loaded_tokenizer(text, return_tensors='pt').input_ids
    
#     # Generate the vector representation using the model
#     with torch.no_grad():
#         outputs = __loaded_model(input_ids)
#         embeddings = outputs.pooler_output
        
#     # Return the vector representation as a numpy array
#     # print(len(embeddings.numpy()[0]))
#     return embeddings.numpy()[0]

# //////////////////*****************//////////////////////////////////////****************************************************












if __name__ == "__main__":
    print("ok")
    # vec = encode_single_doc("the cat is strong")
    # print(len(vec))
