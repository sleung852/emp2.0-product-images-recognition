import time
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import pandas as pd


class StatusReport:
    def __init__(self,
                 scope=None,
                 credentials=None,
                 data=None,
                 time_obtained=None
                 ):
    
        self.scope=scope
        self.credentials=credentials
        self.data=data
        self.time_obtained=time_obtained

    def connection(self):
        self.scope=['https://www.googleapis.com/auth/drive']
        self.credentials=ServiceAccountCredentials.from_json_keyfile_name('hktdc-pec-elec-garment-tag-72f0e1c9e005.json',
                                                                          self.scope)
        print('Connection initialised\n')
        
    def get_report(self):
        start = time.time()
        gc = gspread.authorize(self.credentials)
        df=pd.DataFrame()
        for productType in ['garment','elec']:
            wks = gc.open('emp_product_tag_{}'.format(productType)).worksheet("output")
            df_temp=pd.DataFrame(wks.get_all_values())
            df_temp.columns=df_temp.iloc[0]
            df_temp=df_temp.drop(df_temp.index[0])
            df_temp['PRODUCT_TYPE']=productType
            df=df.append(df_temp)
        self.data = df
        self.time_obtained=datetime.datetime.now()
        print('Obtained Data at {}\n'.format(self.time_obtained))

    def overview(self):
        #check whether the inputs are correct
        #if self.data==None:
        #       raise Exception('No report is available yet. \nPlease use get_report before using overview.')

        total=self.data.shape[0]
        notDone=self.data[self.data['completed_timestamp']=='not_ready'].shape[0]
        print('Overall Completion: {:.2f}%'.format(100*(1-(notDone/total))))
        print('with {} products left  to label'.format(notDone))
        print('--'*10)

        df_temp = self.data[self.data['PRODUCT_TYPE']=='garment']
        g_total=df_temp.shape[0]
        g_notDone=df_temp[df_temp['completed_timestamp']=='not_ready'].shape[0]

        print('Garment Completion: {:.2f}%'.format(100*(1-(g_notDone/g_total))))
        print('with {} products left to label'.format(g_notDone))
        print('--'*10)

        df_temp = self.data[self.data['PRODUCT_TYPE']=='elec']
        e_total=df_temp.shape[0]
        e_notDone=df_temp[df_temp['completed_timestamp']=='not_ready'].shape[0]

        print('Consumer Electronic Completion: {:.2f}%'.format(100*(1-(e_notDone/e_total))))
        print('with {} products left  to label'.format(e_notDone))
        print('--'*10)
        
        #print('Data was obtained at {}'.format(self.time_obtained))

obtainReport = StatusReport()
obtainReport.connection()
obtainReport.get_report()
obtainReport.overview()

input('Press Enter to terminate.');