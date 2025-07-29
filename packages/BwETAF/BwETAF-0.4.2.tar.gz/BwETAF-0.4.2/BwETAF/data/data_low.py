import json
import numpy as np
from huggingface_hub import hf_hub_download, upload_file

def save_ds_np(array,path="ds.npy"):
    np.save(path,array)

def load_ds_np(path):
    return np.load(path)

class Load_dataset():
    def load_txt(path,encode='utf-8'):
        with open(path, encoding=encode,mode='r') as file:
            return file.read()
    
    def load_json(path):
        with open(path,'r') as file:
            data = json.load(file)
        if isinstance(data,list):
            return data
        if isinstance(data,dict):
            return list(json.load(file).Values())
    
    def load_hf_formated(name,file):
        from datasets import load_dataset
        dataset = load_dataset(name, data_files=file)
        train_data_dict = dataset['train'].to_dict()["answer"]
        return train_data_dict

def Load(name,file,start=0,end=None):
    data = Load_dataset.load_hf_formated(name,file)
    if end is not None:
        return data[start:end]
    else:
        return data[start:]


def get_data(repo_id="WICKED4950/Raw-GPT-traindata", file="saved_ds.npy"):
    print("Plesae note that this is not a correctly working function")
    print(hf_hub_download(repo_id=repo_id, filename=file,local_dir="ds"))

def put_data(repo_id="WICKED4950/Raw-GPT-traindata", file="saved_ds.npy"):
    upload_file(
        path_or_fileobj=file,
        path_in_repo=file,  # Save with the same filename
        repo_id=repo_id,
        repo_type="dataset",
    )