from __future__ import print_function, division

#general operations
import time
import os
import copy
import pathlib

#for openning images via an URL
from PIL import Image
import requests

#data processing
import pandas as pd
import numpy as np

#data visualisation
import matplotlib.pyplot as plt

#ML tools
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torch.utils.data.dataset import Dataset
import torchvision
from torchvision import models, transforms

class EmpImageData:
    def __init__(self, csv_dir):
        self.data=pd.read_csv(csv_dir)
        self.forward_mapping = None
        self.reverse_mapping = None
        self.classes_num = None
        self.full_dataset = None
        self.data_dict=None

    def create_dataset(self, label_col, file_col, folder_dir, min_n=100, train_val_ratio=0.8, pure_random=True):

        df=self.data[[label_col,file_col]]
        df_sum = df.groupby(label_col).count().sort_values(file_col, ascending=False)
        keepindex=df_sum[df_sum['PRODUCT_ID']>=min_n].index
        #print(keepindex)
        df = df[df[label_col].apply(lambda x: True if x in keepindex else False)]
        df.columns=['labels','image_path']
        df['image_path']=df['image_path'].apply(lambda p_id: str(p_id) + '.jpg')
        df['image_path']=df['image_path'].apply(lambda file_name: os.path.join(folder_dir, file_name))
        mapping = enumerate(df['labels'].unique())
        self.reverse_mapping=dict(mapping)
        self.forward_mapping={value: key for key,value in self.reverse_mapping.items()}

        df['labels']=df['labels'].map(self.forward_mapping)
        
        
        def missing_data(file_dir):
            item=pathlib.Path(file_dir)
            return not item.exists()
        
        # check how many images are not downloaded
        print('There are in total {} missing data.'.format(sum(df['image_path'].apply(missing_data))))
        
        self.full_dataset = df
        self.classes_num=len(df['labels'].unique())
        
        if pure_random:
            trainsize=int(df.shape[0]*train_val_ratio)
            train=df.iloc[:trainsize]
            val=df.iloc[trainsize:]

        else:
            train=pd.DataFrame(columns=df.columns)
            val=train.copy()
            for label in df['labels'].unique():
                df_by_label=df[df['labels']==label]
                ratio=int(df_by_label.shape[0] * 0.8)
                train=train.append(df_by_label.iloc[:ratio,:])
                val=val.append(df_by_label.iloc[ratio:,:])
            
        self.data_dict={
            'train': train,
            'val':val
        }
            
        return self.data_dict
    
    def display_photos(self, label, n=12, num_row=4):
        print('Label: {}'.format(self.reverse_mapping[label]))
        img_list=list(self.full_dataset[self.full_dataset['labels']==label].sample(n)['image_path'])
        figs, axes = plt.subplots(nrows=n//num_row , ncols=num_row ,figsize=(50,50))
        i=0
        for y in range(n//num_row):
            for x in range(num_row):
                img = Image.open(img_list[i])
                axes[y, x].imshow(img)
                axes[y, x].xaxis.set_visible(False)
                axes[y, x].yaxis.set_visible(False)
                i+=1 
        for x in range(n%num_row):
            img = Image.open(img_list[i])
            axes[n//num_row, x].imshow(img)
            axes[n//num_row, x].xaxis.set_visible(False)
            axes[n//num_row, x].yaxis.set_visible(False)
            i+=1       

    def mktorchdataloaders(self, transformations=None, batch_size=4):
        keys=['train','val']
        product_datasets = {key: ImageData(self.data_dict[key], transforms=transformations) for key in keys}

        datasets_loader = {key: torch.utils.data.DataLoader(dataset=product_datasets[key],
                                                        batch_size=batch_size,
                                                        num_workers=8,
                                                        shuffle=False) for key in keys}

        dataset_sizes = {key: len(product_datasets[key].labels_arr) for key in keys}

        return datasets_loader, dataset_sizes

class ImageData(Dataset):
    def __init__(self, raw_data, transforms=None):
        self.raw_data = raw_data
        self.transforms = transforms
        self.labels_arr = self.raw_data.iloc[:,0]
        self.image_arr = self.raw_data.iloc[:,1]
        self.data_len = len(self.raw_data.index)


    def __getitem__(self, index):
        one_img = Image.open(self.image_arr.iloc[index]).convert('RGB')

        if self.transforms is not None:
            transformed_img = self.transforms(one_img)
        else:
            transformations = transforms.Compose([transforms.ToTensor()])
            transformed_img = transformations(one_img)

        # Get the image Label
        single_image_label = self.labels_arr.iloc[index]

        return (transformed_img, single_image_label)

    def __len__(self):
        return self.data_len