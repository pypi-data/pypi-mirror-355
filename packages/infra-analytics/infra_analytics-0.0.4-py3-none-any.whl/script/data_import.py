import os
import spark_sdk as ss
ss.__version__
import os
ss.PySpark(yarn=False, num_executors=60, driver_memory='60g', executor_memory='24g',
            add_on_config1=('spark.port.maxRetries', '1000'))
spark = ss.PySpark().spark

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
import pyspark.pandas as ps
from pyspark.sql.functions import to_date,col
spark.sql("SET spark.sql.sources.partitionOverwriteMode = dynamic")
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import glob, re

import sh
import requests
import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine

def extract_date(file_path):
    # Split tên file để lấy phần ngày tháng
    file_name = file_path.split('/')[-1]  # Lấy phần cuối cùng sau dấu '/'
    date_str = file_name.split('_')[-1]   # Lấy phần sau dấu '_' chứa ngày tháng
    date_str = date_str.replace('.xlsx','')
    # Chuyển đổi từ string sang datetime
    return datetime.strptime(date_str, '%Y%m%d')
def process_hodannam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/ho_dan'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df.columns = ['Mã tỉnh', 'Tỉnh', 'Mã quận', 'Quận', 'Mã phường', 'Phường', 'Tổng hộ',
               'Thành thị', 'Nông thôn', 'Năm']
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/ho_dan.parquet/")\
        .save()

def process_dansonam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/dan_so'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df.columns = ['Mã tỉnh', 'Tỉnh', 'Mã quận', 'Quận', 'Mã phường', 'Phường', 'Tổng số dân',
           'Dân số Nông thôn', 'Dân số Thành thị', 'Năm']
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/dan_so.parquet/")\
        .save()
def process_thanhphandansonam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/thanh_phan_dan_so'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df.columns = ['Mã tỉnh', 'Tỉnh', 'Mã quận', 'Quận', 'Mã phường', 'Phường',
           'Dưới tiểu học', 'Tiểu học', 'Trung học', 'Cao đẳng', 'Đại học',
           'Thạc sỹ', 'Tiến sỹ', 'Năm']
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/thanh_phan_dan_so.parquet/")\
        .save()

def process_nganhangnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/ngan_hang'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/ngan_hang.parquet/")\
        .save()
        
def process_chitieunam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/chi_tieu'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/chi_tieu.parquet/")\
        .save()

def process_benhviennam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/benh_vien'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/benh_vien.parquet/")\
        .save()

def process_trung_tam_y_tenam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/trung_tam_y_te'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/trung_tam_y_te.parquet/")\
        .save()
def process_truong_tieu_hocnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/truong_tieu_hoc'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/truong_tieu_hoc.parquet/")\
        .save()
def process_truong_trung_hoc_co_sonam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/truong_trung_hoc_co_so'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/truong_trung_hoc_co_so.parquet/")\
        .save()
def process_truong_trung_hoc_pho_thongnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/truong_trung_hoc_pho_thong'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/truong_trung_hoc_pho_thong.parquet/")\
        .save()

def process_truong_dai_hocnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/truong_dai_hoc'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/truong_dai_hoc.parquet/")\
        .save()
def process_truong_cao_dangnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/truong_cao_dang'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/truong_cao_dang.parquet/")\
        .save()
def process_chonam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/cho'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/cho.parquet/")\
        .save()
def process_sieu_thinam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/sieu_thi'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/sieu_thi.parquet/")\
        .save()

def process_trung_tam_thuong_mainam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/trung_tam_thuong_mai'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/trung_tam_thuong_mai.parquet/")\
        .save()
def process_doanh_nghiepnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep.parquet/")\
        .save()
def process_doanh_nghiep_vua_va_nhonam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_vua_va_nho'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_vua_va_nho.parquet/")\
        .save()

def process_doanh_nghiep_tu_nhannam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_tu_nhan'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_tu_nhan.parquet/")\
        .save()
def process_khach_sannam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/khach_san'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/khach_san.parquet/")\
        .save()
def process_khach_san_tu_nhannam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/khach_san_tu_nhan'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/khach_san_tu_nhan.parquet/")\
        .save()
def process_doanh_nghiep_co_von_nuoc_ngoainam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_co_von_nuoc_ngoai'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_co_von_nuoc_ngoai.parquet/")\
        .save()
def process_doanh_nghiep_co_hoat_dong_xuat_nhap_khaunam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_co_hoat_dong_xuat_nhap_khau'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_co_hoat_dong_xuat_nhap_khau.parquet/")\
        .save()
def process_doanh_nghiep_cong_nghe_thong_tinnam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_cong_nghe_thong_tin'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_cong_nghe_thong_tin.parquet/")\
        .save()
def process_doanh_nghiep_co_trang_thong_tin_dien_tunam(year):
    hdfsdir = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/'
    filelist = [ line.rsplit(None,1)[-1] for line in sh.hdfs('dfs','-ls',hdfsdir).split('\n') if len(line.rsplit(None,1))][1:]
    keyword = '/data/fpt/ftel/infra/dwh/import_data_phattrienhatang/doanh_nghiep_co_trang_thong_tin_dien_tu'
    # Initialize an empty list to store matching file paths
    matching_files = []
    
    # Iterate through the file list
    for file_path in filelist:
        # Check if the keyword is present in the file path
        if keyword in file_path:
            # If yes, append the file path to the matching_files list
            matching_files.append(file_path)
    # Lấy ra file có ngày tạo gần đây nhất
    recent_file = max(matching_files, key=extract_date)
    print(recent_file)
    df= ps.read_excel(recent_file)
    df['Năm'] = year
    df_ = spark.createDataFrame(df.to_pandas())
    df_ = df_.withColumn('d', to_date(col('Năm')))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('d')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/doanh_nghiep_co_trang_thong_tin_dien_tu.parquet/")\
        .save()
# Hàm để lấy dữ liệu từ một trang cụ thể
def fetch_data(page, limit):
    url = f'https://icdp.fpt.net/flask/cads/get_star_pop?page={page}&limit={limit}'
    headers = {
    'content-type': 'application/json',
    }
    proxies = {
    "http_proxy": "http://proxy.hcm.fpt.vn:80",
    "https_proxy": "http://proxy.hcm.fpt.vn:80",
    "no_proxy": "icdp.fpt.net"
    }
    response = requests.get(url,
                  headers=headers, 
                  proxies=proxies)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Hàm để lấy toàn bộ dữ liệu từ API
def fetch_all_data(base_url, limit=10000):
    all_data = []
    page = 1
    while True:
        print(page)
        data = fetch_data(page, limit)
        if (len(data['data']['data'])==0):  # Nếu không còn dữ liệu mới, dừng lại
            break
        all_data.extend(data['data']['data'])
        page += 1
    return all_data
def process_get_star_pop(month):
    # Sử dụng hàm để lấy toàn bộ dữ liệu
    base_url = 'https://icdp.fpt.net/flask/cads/get_star_pop'
    all_data = fetch_all_data(base_url)
    lst_data_single = pd.DataFrame(all_data)
    lst_data_single.columns=['month','avg_operation_pop','avg_quality_pop','pop','province']
    lst_data_single['month'] = pd.to_datetime(lst_data_single['month'])
    
    conn = pg.connect("postgresql://dwh_noc:fNSdAnGVEA23NjTTPvRv@172.27.11.177:6543/dwh_noc")
    cur = conn.cursor()
    sql = """DELETE FROM public.tbl_quality_pop WHERE month = '""" + month + """';"""
    cur.execute(sql)
    conn.commit()
    engine = create_engine('postgresql://dwh_noc:fNSdAnGVEA23NjTTPvRv@172.27.11.177:6543/dwh_noc')
    lst_data_single[lst_data_single.month==month].to_sql('tbl_quality_pop', engine, if_exists='append', index=False, schema='public')

def process_dataimport(date):
    if (int(date[5:7])>=3)&(int(date[5:7])<9):
        kydautu = '2H'+str(int(date[:4]))
    else:
        if (int(date[5:7])>=1)&(int(date[5:7])<3):
            kydautu= '1H'+str(int(date[:4]))
        else:
            kydautu= '1H'+str(int(date[:4])+1)
    year=kydautu[2:]+'-01-01'
    process_get_star_pop(date)
    process_dansonam(year)
    process_hodannam(year)
    process_thanhphandansonam(year)
    process_nganhangnam(year)
    process_chitieunam(year)
    process_benhviennam(year)
    process_trung_tam_y_tenam(year)
    process_truong_tieu_hocnam(year)
    process_truong_trung_hoc_co_sonam(year)
    process_truong_trung_hoc_pho_thongnam(year)
    process_truong_dai_hocnam(year)
    process_truong_cao_dangnam(year)
    process_chonam(year)
    process_sieu_thinam(year)
    process_trung_tam_thuong_mainam(year)
    process_doanh_nghiepnam(year)
    process_doanh_nghiep_vua_va_nhonam(year)
    process_doanh_nghiep_tu_nhannam(year)
    process_khach_sannam(year)
    process_khach_san_tu_nhannam(year)
    process_doanh_nghiep_co_von_nuoc_ngoainam(year)
    process_doanh_nghiep_co_hoat_dong_xuat_nhap_khaunam(year)
    process_doanh_nghiep_cong_nghe_thong_tinnam(year)
    process_doanh_nghiep_co_trang_thong_tin_dien_tunam(year)