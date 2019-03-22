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
        cell = wks.find("idle")
        #update the STATUS column
        wks.update_cell(cell.row, cell.col, 'work_in_progress')
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


#call an object from Tk
window = Tk()
window.title('HKTDC Image Labelling App')
#set window size
window.geometry('1400x1400')



#setup for freakin checkboxes
lines=[]
with open("elec_csv.csv","r") as ref:
    for line in ref:
        lines.append(line)

tickbox_set=[]
for line in lines:
    temp_list=[]
    for string in line.split(','):
        if string=='':
            break
        elif string[-1]==' ':
            temp_list.append(string[:-1])
        elif string[-2:]==r'\n':
            temp_list.append(string[:-2])
        else:
            temp_list.append(string)
    tickbox_set.append(temp_list)

#new task
task = LabelTask(user_id=8,product_type='elec')

##first data call
task.initialise()
url=r'http://i03.hktdc-img.com/rsc?profile=productimage&subprofile=enlarge&pid={}&file=image_1.jpg'.format(task.product_id)
print(task.product_id)
#print(attributes)
#print(attributes_chi)



#setup variables  

##first time defining url and attributes
#url, attributes = get_gsheet()
#url, attributes = get_test_inputs()

##define activebutton
active_buttons=len(task.labels)
total_buttons=10

##define label and button dictionaries
label_d={}
for i in range(len(task.labels)):
    label_d['label{}'.format(i)]=Label()
button_d={}

##action variables
yes_dict={}
no_dict={}

checkbutton_dict={}
tick_count=0
##output formats
#response_vector=np.zeros(len(attributes))
#output_vector=np.zeros(len(attributes))

####################################################################
#set a bunch of functions
####################################################################

##setup yes no functions

def yes_function(i):
    key='label{}'.format(i)    
    def y_func():
        #update colour of the attribute
        label_d['label{}'.format(i)].configure(bg='green')
        #update response vector
        task.updated_response_vector_to_one(i)
        #update output vector
        task.updated_g_output_vector_to_one(i)
        
        print(task.response_vector)
    return y_func

def no_function(i):
    key='label{}'.format(i)
    def n_func():
        #update colour of the attribute
        label_d['label{}'.format(i)].configure(bg='red')
        #update response vector
        task.updated_response_vector_to_one(i)
        #update output vector
        task.updated_g_output_vector_to_zero(i)
        
        print(task.response_vector)
    return n_func

def checked_box_function(i):
    key='label{}'.format(i)
    def no_func():
        #update response vector
        task.updated_response_vector_to_one(i)
        #update output vector
        task.updated_g_output_vector_to_zero(i)
        print(task.response_vector)
    return 

for i in range(len(task.labels)):
    yes_dict['label{}'.format(i)]=yes_function(i)
    no_dict['label{}'.format(i)]=no_function(i)
    label_d['label{}'.format(i)]=Label(window, text=task.labels[i] + ' ' + task.labels_chi[i])
    (label_d['label{}'.format(i)]).grid(column=0,row=i+3)
    
if total_buttons>len(task.labels):
    for i in range(len(task.labels),total_buttons):
        yes_dict['label{}'.format(i)]=yes_function(i)
        no_dict['label{}'.format(i)]=no_function(i)
        label_d['label{}'.format(i)]=Label(window, text='Unavailable',bg='grey')
        (label_d['label{}'.format(i)]).grid(column=0,row=i+3)

def next_function():
    
    start = time.time()
    
    #check whether the response vector is all ones
    if (task.response_vector != np.ones(active_buttons)).any():
        messagebox.showwarning('Warning',
                              'Please ensure you have clicked Yes or No for all attributes')
    else:
        checkbox_submission=[]
        for i in range(tick_count):
            checkbox_submission.append(checkbutton_dict['check_{}'.format(i)].get())
        task.t_output_vector=checkbox_submission
        task.local_backup()
        print('Local backup successful')
        task.submit_to_gsheet()
        print('Online submission successful')
        next_image()
    end = time.time()
    print('next_function.function.time: {}s'.format(end-start))
    
####################################################################

def next_image():
    
    start = time.time()
    
    #call get_gsheet function to obtain url and attributes
    #url, attributes = get_gsheet()

    #new image
    task.check_record()
    url=r'http://i03.hktdc-img.com/rsc?profile=productimage&subprofile=enlarge&pid={}&file=image_1.jpg'.format(task.product_id)
    print(task.labels)
    print(task.labels_chi)
    _response = requests.get(url)
    img=Image.open(BytesIO(_response.content))
    img=img.resize((250, 250), Image.ANTIALIAS)
    img=ImageTk.PhotoImage(img)
    panel.configure(image=img)
    panel.image=img
    
    global active_buttons
    
    #adjust layout if neccessary
    if active_buttons>len(task.labels):
        for i in range(len(task.labels)):
            label_d['label{}'.format(i)].configure(text=task.labels[i] + ' ' + task.labels_chi[i],bg='white')
        for i in range(len(task.labels),total_buttons):
            label_d['label{}'.format(i)].configure(text='Unavailable',bg='grey')
            button_d['button_y{}'.format(i)].configure(bg='grey',fg='black',command=lambda:None)
            button_d['button_n{}'.format(i)].configure(bg='grey',fg='black',command=lambda:None)
    elif active_buttons<len(task.labels):
        for i in range(len(task.labels)):
            label_d['label{}'.format(i)].configure(text=task.labels[i] + ' ' + task.labels_chi[i],bg='white')
            button_d['button_y{}'.format(i)].configure(bg='white', fg='green',command=yes_dict['label{}'.format(i)])
            button_d['button_n{}'.format(i)].configure(bg='white',fg='red',command=no_dict['label{}'.format(i)])
    else: # or active_buttons==len(attributes)
        for i in range(len(task.labels)):
            label_d['label{}'.format(i)].configure(text=task.labels[i],bg='white')
    
    #reset output formats
    active_buttons=len(task.labels)
    print(active_buttons)
    task.set_g_output_vector_zeros(len(task.labels))
    print(task.g_output_vector)
    task.set_response_vector_zeros(len(task.labels))
    print(task.response_vector)

    for i in range(tick_count):
        checkbutton_dict['check_{}'.format(i)].set(0)
    
    end = time.time()
    print('next_image.function.time: {}s'.format(end-start))

    
    


#setup content
####################################################################
##image part
####################################################################

title_font=('Helvetica', '20')

#layoutplan
Label(window, text='Product Image', font=title_font).grid(column=0,row=0)
#display image
Label(window, text='Google Generated Tags', font=title_font).grid(column=0,row=2)
#display ten rows of Google tags [3,4,5,6,7,8,9,10,11,12]
Label(window, text='TDC Tags', font=title_font).grid(column=4,row=2)

tick_count=0
current_row=3
current_column=4
for row in range(len(tickbox_set)):
    for column in range(len(tickbox_set[row])):
        key='check_{}'.format(tick_count)
        checkbutton_dict[key]=IntVar()
        temp_check = Checkbutton(window, text=tickbox_set[row][column], variable=checkbutton_dict[key], anchor = "w")
        if (column%7==0) & (column!=0):
            current_row+=1
        temp_check.grid(row=current_row+row, column=current_column+(column%7))
        tick_count+=1
    #Label(window, text='-------').grid(column=current_column,row=current_row+row+1)
    #current_row += 1
##garment

#test
response=requests.get(url)
img=Image.open(BytesIO(response.content))
img=img.resize((250, 250), Image.ANTIALIAS)
img=ImageTk.PhotoImage(img)
panel=Label(window, image = img)



#set location
panel.grid(column=0,row=1)

####################################################################
##setup display objects in the app
####################################################################
###attributes yes or no buttons

for i in range(active_buttons):
    button_d['button_y{}'.format(i)]=Button(window, text="Yes", bg='white', fg='green', command=yes_dict['label{}'.format(i)])
    (button_d['button_y{}'.format(i)]).grid(column=1, row=i+3)
    button_d['button_n{}'.format(i)]=Button(window, text="No", bg='white', fg='red', command=no_dict['label{}'.format(i)])
    (button_d['button_n{}'.format(i)]).grid(column=2, row=i+3)

if total_buttons>active_buttons:
    for i in range(active_buttons,total_buttons):
        button_d['button_y{}'.format(i)]=Button(window, text="Yes", bg='grey',fg='black', command=lambda:None)
        (button_d['button_y{}'.format(i)]).grid(column=1, row=i+3)
        button_d['button_n{}'.format(i)]=Button(window, text="No", bg='grey',fg='black', command=lambda:None)
        (button_d['button_n{}'.format(i)]).grid(column=2, row=i+3)

btn_next = Button(window, text="Next", bg='orange', fg='black', command=next_function)
btn_next.grid(column=0, row=20)

print(label_d)
print(button_d)

def on_closing():
    print(checkbutton_dict['check_0'].get())
    if messagebox.askokcancel("Quit", "You sure you want to quit?"):
        task.close_proto()
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
    

        

