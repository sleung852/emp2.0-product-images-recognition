from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
from io import BytesIO
import requests
import time
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np

##Simple Function##

def get_time_now():
    
    start = time.time()
    
    localtime = time.localtime(time.time())
    j=''
    for i in localtime[:2]:
        j+=str(i)+'-'
    j+=str(localtime[2])+' '
    for i in localtime[3:5]:
        j+=str(i)+':'
    j+=str(localtime[5])
    
    end = time.time()
    print('get_time_now.function.time: {}s'.format(end-start))
    
    return j


##Task Object##

class LabelTask:
    def __init__(self,user_id,
                 product_type,
                 product_id=None,
                 labels=None,
                 labels_chi=None,
                 response_vector=None,
                 g_output_vector=None,
                 t_output_vector=None,
                 scope=None,
                 credentials=None
                 ):
    
        self.product_id=product_id
        self.labels=labels
        self.labels_chi=labels_chi
        self.response_vector=response_vector
        self.g_output_vector=g_output_vector #for tags generated from Google
        self.t_output_vector=t_output_vector #for tags generated internally
        self.scope=scope
        self.credentials=credentials
        self.user_id=user_id
        self.product_type=product_type
            
    def set_response_vector_zeros(self, n):
        self.response_vector=np.zeros(n)
    def set_g_output_vector_zeros(self, n):
        self.g_output_vector=np.zeros(n)
    def set_t_output_vector_zeros(self, n):
        self.t_output_vector=np.zeros(n)
        
    def updated_response_vector_to_one(self, ind):
        self.response_vector[ind]=1
    def updated_g_output_vector_to_one(self, ind):
        self.g_output_vector[ind]=1
    def updated_t_output_vector_to_one(self, ind):
        self.t_output_vector[ind]=1
        
    def updated_response_vector_to_zero(self, ind):
        self.response_vector[ind]=0
    def updated_g_output_vector_to_zero(self, ind):
        self.g_output_vector[ind]=0
    def updated_t_output_vector_to_zero(self, ind):
        self.t_output_vector[ind]=0
        
    def check_record(self):
    
        start = time.time()

        gc = gspread.authorize(self.credentials)

        wks = gc.open('emp_product_tag_{}'.format(self.product_type)).worksheet("input")
        cells = wks.findall("idle")
        cell=cells[-1]
        #update the STATUS column
        #wks.update_cell(cell.row, cell.col, 'work_in_progress')
        #obtain the row in list format
        tags_list = wks.row_values(cell.row)

        end = time.time()
        print('check_record.function.time: {}s'.format(end-start))
        
        self.product_id = tags_list[0]

        if tags_list[10]=='':
            self.labels = tags_list[1:tags_list.index('')]
            self.labels_chi = (tags_list[42:])[:len(tags_list[1:tags_list.index('')])]
        else:
            self.labels = tags_list[1:11]
            self.labels_chi = (tags_list[42:])[:len(tags_list[1:11])]
                
    def submit_to_gsheet(self):
        start = time.time()
        gc = gspread.authorize(self.credentials)

        wks = gc.open('emp_product_tag_{}'.format(self.product_type)).worksheet("output")

        #find the matching 
        cell = wks.find(self.product_id)
        wks.update_cell(cell.row, cell.col+1, get_time_now())
        wks.update_cell(cell.row, cell.col+2, str(self.g_output_vector))
        #for i in range(len(self.g_output_vector)):
            #wks.update_cell(cell.row, cell.col+2+i, self.g_output_vector[i])
        wks.update_cell(cell.row, cell.col+3, str(self.t_output_vector))
        wks.update_cell(cell.row, cell.col+4,self.user_id)
        print('Data Recorded')

        end = time.time()
        print('record_data.function.time: {}s'.format(end-start))
        
    def local_backup(self):
        with open("local_backup.txt","a") as backup:
            backup.write('\n{},{},{}'.format(self.product_id,
                                             self.g_output_vector,
                                             self.t_output_vector))
            
    def initialise(self):
        self.scope=['https://www.googleapis.com/auth/drive']
        self.credentials=ServiceAccountCredentials.from_json_keyfile_name('hktdc-pec-elec-garment-tag-72f0e1c9e005.json',
                                                                          self.scope)
        self.check_record()
        self.response_vector=np.zeros(len(self.labels))
        self.g_output_vector=np.zeros(len(self.labels))
        
        if os.path.isfile('local_backup.txt'):
            print('local_backup.txt checked')
        else:
            print('local_backup.txt is not here')
            f=open("local_backup.txt","w+")
            f.write("Local Backup File - Please do not delete")
            f.close()
            print('local_backup.txt is created')
        
    def close_proto(self):
        start = time.time()
        gc = gspread.authorize(self.credentials)
        wks = gc.open('emp_product_tag_{}'.format(self.product_type)).worksheet("input")
        #find the matching 
        cell = wks.find(self.product_id)
        wks.update_cell(cell.row, 42, 'idle')
        print('close proto done')


    def check_record_test(self):

        self.scope=['https://www.googleapis.com/auth/drive']
        self.credentials=ServiceAccountCredentials.from_json_keyfile_name('hktdc-pec-elec-garment-tag-72f0e1c9e005.json',
                                                                          self.scope)
        start = time.time()

        gc = gspread.authorize(self.credentials)

        wks = gc.open('emp_product_tag_{}'.format(self.product_type)).worksheet("input")
        cell = wks.find("idle")
        #cell=cells[-1]
        #update the STATUS column
        #wks.update_cell(cell.row, cell.col, 'work_in_progress')
        #obtain the row in list format

        #print(cells[-1])
        #cell=cells[-1]
        print(cell.row)
        end = time.time()
        print('check_record.function.time: {}s'.format(end-start))
        
task=LabelTask(user_id=9, product_type='garment')
task.check_record_test()