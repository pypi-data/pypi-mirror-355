import psycopg2 as pg
from sqlalchemy import create_engine
import unidecode
import pickle
import os
import numpy as np
import pandas as pd
from datetime import datetime,timedelta
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
from numpy import std,loadtxt,sort
from sklearn.datasets import make_classification
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.feature_selection import SelectFromModel
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn import tree
import datetime as dt
import pytz
import glob
from dateutil.relativedelta import relativedelta
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import SelectKBest, f_classif
from sksurv.ensemble import ExtraSurvivalTrees
from operator import add
from sksurv.nonparametric import kaplan_meier_estimator
from sksurv.ensemble import RandomSurvivalForest
from sksurv.ensemble import GradientBoostingSurvivalAnalysis
from sksurv.tree import SurvivalTree
from sksurv.ensemble import GradientBoostingSurvivalAnalysis
from sksurv.ensemble import ComponentwiseGradientBoostingSurvivalAnalysis
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sklearn import set_config
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
set_config(print_changed_only=False)
from sklearn.metrics import classification_report
from sklearn.impute import KNNImputer
import os.path

# import pyspark
# #  bắt đầu từ đây 
# os.environ['SPARK_HOME']="/opt/spark/spark-3.0.2-bin-hadoop2.7/"
# os.environ['JAVA_HOME']="/usr/jdk64/jdk1.8.0_112/"
# os.environ['PYSPARK_DRIVER_PYTHON']="python"
# # Do not set in cluster modes
# os.environ['HADOOP_OPTS']="-Dhdp.version=3.1.0.0-78"

# conf = SparkConf()

# # config location for spark finding metadata from hive metadata server
# conf.set("hive.metastore.uris", "thrift://master01-dc9c14u40.bigdata.local:9083,thrift://master02-dc9c14u41.bigdata.local:9083")
# conf.set("spark.sql.hive.metastore.jars", "/opt/spark/spark-3.0.2-bin-hadoop2.7/*")

# # config directory to use for "scratch" space in Spark, including map output files and RDDs that get stored on disk
# # conf.set('spark.local.dir', '/tmp/user')
# # config in-memory columnar data format that is used in Spark to efficiently transfer data between JVM and Python processes
# conf.set("spark.kryoserializer.buffer.max", "2000")
# conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
# conf.set("spark.sql.execution.arrow.enabled", "true")
# conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "false")
# conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "50000")


# # config spark driver memory
# conf.set("spark.driver.memory", '60g')
# conf.set('spark.driver.maxResultSize', '5G')
# conf.set('spark.default.parallelism', '8')

# #set metastore.client.capability.check to false
# conf.set("hive.metastore.client.capability.check", "false")

# conf.set("spark.ui.port", "7070")
# conf.set("spark.driver.extraJavaOptions", "-Dhdp.version=3.1.0.0-78")
# conf.set("spark.yarn.am.extraJavaOptions", "-Dhdp.version=3.1.0.0-78")

# spark = SparkSession.builder.config(conf=conf).master("local[40]")\
# .config("spark.jars", "/mnt/projects-data/infra_report/jars/postgresql-42.2.20.jar")\
# .enableHiveSupport().getOrCreate()
##  config pyspark 
import spark_sdk as ss
ss.__version__
import os
ss.PySpark(yarn=False, num_executors=60, driver_memory='60g', executor_memory='24g',
            add_on_config1=('spark.port.maxRetries', '1000'),
          add_on_config2=('spark.jars', '/mnt/projects-data/infra_report/jars/postgresql-42.2.20.jar'))
spark = ss.PySpark().spark
spark.sql("SET spark.sql.sources.partitionOverwriteMode = dynamic")
from pyspark import SparkConf
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.sql.functions import monotonically_increasing_id 
from pyspark.sql.types import StringType
from pyspark.sql import Window
from pyspark import SparkConf
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.sql.types import StringType
from pyspark.sql.functions import *
from pyspark.sql.functions import countDistinct
import pyspark.sql.functions as f
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType
from requests.packages import urllib3
urllib3.disable_warnings()
import subprocess

def hdfs_file_exists(path):
    result = subprocess.run(['hdfs', 'dfs', '-test', '-e', path])
    return result.returncode == 0

def process_GYTN(date):

    # if (int(date[5:7])>=3)&(int(date[5:7])<9):
    #     kydautu = '2H'+str(int(date[:4]))
    #     date=str(int(date[:4]))+'-03-01'
    # else:
    #     if (int(date[5:7])>=1)&(int(date[5:7])<3):
    #         kydautu= '1H'+str(int(date[:4]))
    #         date=str(int(date[:4])-1)+'-09-01'
    #     else:
    #         kydautu= '1H'+str(int(date[:4])+1)
    #         date=str(int(date[:4]))+'-09-01'
    # prev_month = (datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6))
    # path_out_ds = '/mnt/projects-data/phat_trien_ha_tang/model/goiytiemnang/model_{}.pkl'.format(kydautu)
    # if (os.path.isfile(path_out_ds)==False):
    #     spark.sql('refresh table ftel_dwh_infra.ds_feature_ptht')
    #     sql_str = """select * from ftel_dwh_infra.ds_feature_ptht 
    #                 where create_date<='{}'""".format(date)
    #     df_feature_= spark.sql(sql_str)
    #     df_feature_ = df_feature_.toPandas()
    if (int(date[5:7])>=3)&(int(date[5:7])<9):
        kydautu = '2H'+str(int(date[:4]))
        date=str(int(date[:4]))+'-03-01'
    else:
        if (int(date[5:7])>=1)&(int(date[5:7])<3):
            kydautu= '1H'+str(int(date[:4]))
            date=str(int(date[:4])-1)+'-09-01'
        else:
            kydautu= '1H'+str(int(date[:4])+1)
            date=str(int(date[:4]))+'-09-01'
    prev_month = (datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6))
    path_out_ds = '/mnt/projects-data/phat_trien_ha_tang/model/goiytiemnang/model_{}.pkl'.format(kydautu)
    if (os.path.isfile(path_out_ds)==False):
        spark.sql('refresh table ftel_dwh_infra.ds_feature_ptht')
        sql_str = """select * from ftel_dwh_infra.ds_feature_ptht 
                    where create_date<='{}'""".format(date)
        df_feature_= spark.sql(sql_str)
        df_feature_ = df_feature_.toPandas()
        df_feature_.drop({'tong_port_sau_6t_hien_tai','port_dung_sau_6t_hien_tai'},axis=1,inplace=True)
        df_label = spark.sql("""select * from ftel_dwh_infra.ds_label_phattrienhatang 
                    where create_date<='{}'""".format(date)).toPandas()
        
        df_feature_full = df_feature_.merge(df_label,on=['quan', 'phuong', 'tinh', 'vung', 
                                      'ky_dau_tu', 'chi_nhanh','create_date'],how='left')
        df_feature_full['hqkt_6t_hieu_tai'] = np.where(df_feature_full['tong_port_sau_6t_hien_tai']>0,
                   df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai'],0)
        
        df_feature_full['danh_gia_hieu_qua']=np.where((df_feature_full['tong_port_sau_6t_hien_tai']>0)&(df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai']>=df_feature_full['nguong_tb']),
                                                       'Hiệu quả',np.where((df_feature_full['tong_port_sau_6t_hien_tai']>0)&(df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai']<df_feature_full['nguong_tb']),
                                                         'Không hiệu quả','Chưa xác định'))
        df_feature_full.replace([np.inf, -np.inf], 0, inplace=True)
        df_feature_full['create_date'] = pd.to_datetime(df_feature_full['create_date'])
        data = df_feature_full.drop(['hqkt_6t_hieu_tai', 'nguong_tb',
                    'tl_khai_thac_sau_3t',  'tl_khai_thac_sau_9t',
                    'tl_khai_thac_sau_12t', 'tl_portfree_sau_3t',
                    'tl_portfree_sau_6t', 'tl_portfree_sau_9t', 'tl_portfree_sau_12t',
                     'dl_kh', 'port', 'portuse', 'portfree', 'portdie',
                    'portmaintain', 'avg_operation_pop',
                    'khg_rm', 'number_nocuoc', 'number_khg','area', 'tong_dan', 'tong_so_ho', 'dai_ly_canh_to'
                    ], axis=1)
        
        train = data[(data['create_date']<=prev_month)&(data.danh_gia_hieu_qua.isin(['Hiệu quả','Không hiệu quả']))]\
                            .drop(['quan', 'phuong', 'tinh', 'vung', 'chi_nhanh','tong_port_sau_6t_hien_tai'
                                   , 'port_dung_sau_6t_hien_tai','create_date','ky_dau_tu'], axis=1)
        train = train.set_index('danh_gia_hieu_qua').reset_index()
        train.replace({'danh_gia_hieu_qua':{'Hiệu quả':1,'Không hiệu quả':0,'Chưa xác định':2}}, regex=True, inplace=True)
        train.fillna(0,inplace=True)
        
        validate = data[(data['create_date']==datetime.strptime(date, '%Y-%m-%d'))]
        test = validate.drop(['quan', 'phuong', 'tinh', 'vung', 'chi_nhanh',
            'tong_port_sau_6t_hien_tai', 'port_dung_sau_6t_hien_tai','create_date','ky_dau_tu'], axis=1)
        test = test.set_index('danh_gia_hieu_qua').reset_index()
        test.replace({'danh_gia_hieu_qua':{'Hiệu quả':1,'Không hiệu quả':0,'Chưa xác định':2}}, regex=True, inplace=True)
        test.fillna(0,inplace=True)
        
        X_train = train.iloc[:, 1:]
        y_train = train.iloc[:, 0]
        X_test = test.iloc[:, 1:]
        y_test = test.iloc[:, 0]
        sel = SelectFromModel(ExtraTreesClassifier(n_estimators=10, random_state=444), 
                              threshold='mean')
        clf = RandomForestClassifier(n_estimators=5000, random_state=444)
        
        model_1 = Pipeline([('norm', StandardScaler()), ('pca', PCA()),('sel', sel), ('clf', clf)])
        params = {'clf__max_features': ['auto', 'sqrt', 'log2']}
        
        gs_1 = GridSearchCV(model_1, params)
        gs_1.fit(X_train, y_train)
        print('Training set score: ' + str(gs_1.score(X_train, y_train)))
        path_output = '/mnt/projects-data/phat_trien_ha_tang/model/goiytiemnang/model_{}.pkl'.format(kydautu)
        with open(path_output,'wb') as f:
            pickle.dump(gs_1,f)
        validate_w = validate[['phuong','quan','tinh', 'vung', 'chi_nhanh','ky_dau_tu','danh_gia_hieu_qua'
                          ,'tong_port_sau_6t_hien_tai', 'port_dung_sau_6t_hien_tai']]
        validate_w['score'] = gs_1.predict_proba(X_test)[:,1]*100
        validate_w = validate_w.sort_values('score',ascending=False)
        validate_w['de_xuat'] = np.where(validate_w.score>=validate_w.score.quantile(0.7),"Đề xuất","Không đề xuất")
        df_ = spark.createDataFrame(validate_w)
        df_ = df_.withColumn('kydautu', col('ky_dau_tu'))
        df_.coalesce(1)\
            .write.mode("overwrite")\
            .partitionBy('kydautu')\
            .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/danh_sach_goi_y_tiem_nang.parquet/")\
            .save()

def get_ds_feature_ptht(date, col_to_use):
    # t3: 2H2023
    # t9: 1H2024
    # date = '2023-03-01' #2H2023
    # if (int(date[5:7])>=3)&(int(date[5:7])<9):
    #     kydautu = '2H'+str(int(date[:4]))
    #     date=str(int(date[:4]))+'-03-01'
    # else:
    #     if (int(date[5:7])>=1)&(int(date[5:7])<3):
    #         kydautu= '1H'+str(int(date[:4]))
    #         date=str(int(date[:4])-1)+'-09-01'
    #     else:
    #         kydautu= '1H'+str(int(date[:4])+1)
    #         date=str(int(date[:4]))+'-09-01'
    # prev_month = (datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6))
    
    # print('Get data for ', kydautu)
        
    # spark.sql('REFRESH TABLE ftel_dwh_infra.ds_feature_ptht')
    # sql_str = """select * from ftel_dwh_infra.ds_feature_ptht 
    #             where create_date<='{}'""".format(date)
    
    # df_feature_= spark.sql(sql_str)
    # df_feature_ = df_feature_.toPandas()
    # df_feature_.replace([np.inf, -np.inf], 0, inplace=True)
    # df_feature_['create_date'] = pd.to_datetime(df_feature_['create_date'])
    if (int(date[5:7])>=3)&(int(date[5:7])<9):
        kydautu = '2H'+str(int(date[:4]))
        date=str(int(date[:4]))+'-03-01'
    else:
        if (int(date[5:7])>=1)&(int(date[5:7])<3):
            kydautu= '1H'+str(int(date[:4]))
            date=str(int(date[:4])-1)+'-09-01'
        else:
            kydautu= '1H'+str(int(date[:4])+1)
            date=str(int(date[:4]))+'-09-01'
    prev_month = (datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6))
    
    print('Get data for ', kydautu)
        
    spark.sql('REFRESH TABLE ftel_dwh_infra.ds_feature_ptht')
    sql_str = """select * from ftel_dwh_infra.ds_feature_ptht 
                where create_date<='{}'""".format(date)
    
    df_feature_= spark.sql(sql_str)
    df_feature_ = df_feature_.toPandas()
    df_feature_= spark.sql(sql_str)
    df_feature_ = df_feature_.toPandas()
    df_feature_.drop({'tong_port_sau_6t_hien_tai','port_dung_sau_6t_hien_tai'},axis=1,inplace=True)
    df_label = spark.sql("""select * from ftel_dwh_infra.ds_label_phattrienhatang 
                where create_date<='{}'""".format(date)).toPandas()
    
    df_feature_full = df_feature_.merge(df_label,on=['quan', 'phuong', 'tinh', 'vung', 
                                  'ky_dau_tu', 'chi_nhanh','create_date'],how='left')
    df_feature_full['hqkt_6t_hieu_tai'] = np.where(df_feature_full['tong_port_sau_6t_hien_tai']>0,
               df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai'],0)
    
    df_feature_full['danh_gia_hieu_qua']=np.where((df_feature_full['tong_port_sau_6t_hien_tai']>0)&(df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai']>=df_feature_full['nguong_tb']),
                                                   'Hiệu quả',np.where((df_feature_full['tong_port_sau_6t_hien_tai']>0)&(df_feature_full['port_dung_sau_6t_hien_tai']/df_feature_full['tong_port_sau_6t_hien_tai']<df_feature_full['nguong_tb']),
                                                     'Không hiệu quả','Chưa xác định'))
    df_feature_full.replace([np.inf, -np.inf], 0, inplace=True)
    df_feature_full['create_date'] = pd.to_datetime(df_feature_full['create_date'])
    return kydautu, df_feature_full[col_to_use]

def get_KDT_info(KDT_test):
    start_year = 2021
    
    end_year = int(KDT_test[2:])
    
    KDT_fill_list = []
    for year_kdt in range(start_year, end_year+1):
        for H in [1, 2]:
            KDT_element = '{}H{}'.format(H, year_kdt)
            if KDT_element != KDT_test:
                KDT_fill_list.append(KDT_element)
            else:
                KDT_fill_list.append(KDT_element)
                break

    if KDT_test in ['1H2021', '2H2021']:
        KDT_train_list = ['2H2020']
    else:
        KDT_train_list = KDT_fill_list[:-2]
        
    
    return KDT_fill_list, KDT_train_list
    
def get_context(date):
    col_to_use = [
        'vung','chi_nhanh','tinh','quan','phuong','ky_dau_tu','hqkt_6t_hieu_tai','nguong_tb','danh_gia_hieu_qua',
        'tong_port_sau_6t_hien_tai','port_dung_sau_6t_hien_tai',
        'area','tong_dan', 'thanh_thi', 'nong_thon', 'tong_so_ho', 'duoi_tieu_hoc',
        'tieu_hoc', 'trung_hoc', 'cao_dang', 'dai_hoc', 'thac_sy', 'tien_sy',
        'density', 'mat_do_ho_dan', 'thu_nhap',
        'total_error_olt','ticketcode','timetotal','name_device','cus_qty',
        'ap_doi_thu', 'khg_rm', 'number_nocuoc', 'number_khg', 'rate_rm',
        'rate_nc', 'num_checlist', 'avg_operation_pop', 'avg_quality_pop',
        'tg_dau_tu_gan_nhat', 'num_khdt_truoc', 'dl_trien_khai',
        'tl_khai_thac_sau_3t', 'tl_khai_thac_sau_6t', 'tl_khai_thac_sau_9t',
        'tl_khai_thac_sau_12t', 'perport', 'tl_portfree_sau_3t',
        'tl_portfree_sau_6t', 'tl_portfree_sau_9t', 'tl_portfree_sau_12t', 'ibb',
        'dai_ly_canh_to', 'so_hd_với_khg', 'doanh_thu', 't1', 't2', 't3', 't4',
        't5', 'tuoi', 'port', 'portuse', 'portfree', 'portdie', 'portmaintain', 'num_device',
        # -------------------------------------------------
        'so_benh_vien','so_co_so_y_te','so_truong_tieu_hoc', 'so_truong_trung_hoc', 'so_truong_pho_thong',
        'so_truong_cao_dang', 'so_truong_dai_hoc', 'so_doanh_nghiep',
        'so_doanh_nghiep_von_nuoc_ngoai', 'so_doanh_nghiep_xuat_nhap_khau',
        'so_kinh_doanh_ca_the', 'so_doanh_nghiep_khach_san',
        'so_ca_the_khach_san', 'so_doanh_nghiep_vua_nho',
        'so_doanh_nghiep_cntt', 'so_doanh_nghiep_ttdt', 'so_cho', 'so_sieu_thi',
        'so_trung_tam_thuong_mai', 'so_san_bay', 'so_cang', 'so_duongga',
        'so_caotoc', 'so_ngan_hang', 'so_vp', 'so_shop'
        ]
    
    KDT_test, df_feature = get_ds_feature_ptht(date, col_to_use)
    KDT_fill_list, KDT_train_list = get_KDT_info(KDT_test)

    df_DL_range_ref = (pd.read_csv('/mnt/projects-data/phat_trien_ha_tang/feature_dexuatdungluong/material/DL_range_ref.csv')
                       [['DL_range', 'DL_range_code']])
    K = 27
    c_thresh = 0.5
    
    return col_to_use, df_feature, K, c_thresh, KDT_fill_list, KDT_train_list, KDT_test, df_DL_range_ref

def prob_Vung(Vung):
    if Vung in ['Vùng 1', 'Vùng 5']:
        prob = 0.45
    else:
        prob = 0.55
    return prob

def model_Vung(Vung):
    if Vung in ['Vùng 7']:
        model = ExtraSurvivalTrees(n_estimators=100,min_samples_split=10,min_samples_leaf=15,n_jobs=-1,random_state=20,verbose=False)
        # model = GradientBoostingSurvivalAnalysis(n_estimators=100, max_depth=1, random_state=20)
    elif Vung in ['Vùng 3']:
        model = SurvivalTree(min_samples_split=10, min_samples_leaf=15, random_state=20)
    else:
        model = GradientBoostingSurvivalAnalysis(n_estimators=100, max_depth=1, random_state=20)
    return model

def preparing_data(df, column_list):
    df_y = df[['danh_gia_hieu_qua', 'DL_range_code']]
    df_y['danh_gia_hieu_qua'] = np.where(df_y['danh_gia_hieu_qua'] == 'Không hiệu quả', True, False)

    df_y_array = np.array(list(df_y.itertuples(index=False, name=None)), dtype=[('danh_gia_hieu_qua', '?'), ('DL_range_code', '<f8')])
    df_x = df[[item for item in df.columns if item not in df_y.columns]]
    df_numeric_x = df_x[column_list]
    
    return df_numeric_x, df_y_array, df_y

def fit_and_score_features(X, y):
    n_features = X.shape[1]
    scores = np.empty(n_features)
    m = RandomSurvivalForest(n_estimators=100,
                           min_samples_split=10,
                           min_samples_leaf=15,
                           n_jobs=-1,
                           random_state=20)
    for j in range(n_features):
        Xj = X[:, j:j+1]
        m.fit(Xj, y)
        scores[j] = m.score(Xj, y)
    return scores

def divide_DL_range(df, col, over_500):
    df_DL_Range = pd.read_csv('/mnt/projects-data/phat_trien_ha_tang/feature_dexuatdungluong/material/DL_range.csv').rename(columns={'DL_Range': 'DL_range'})
    df_DL_Range_SL = df_DL_Range[['sum_port_DLRange', 'DL_range']].drop_duplicates().dropna()

    df_DL_Range_SL_1 = df_DL_Range_SL.loc[df_DL_Range_SL['sum_port_DLRange']>150]
    df_DL_Range_SL_2 = df_DL_Range_SL.loc[df_DL_Range_SL['sum_port_DLRange']<=150] #over_500
    
    if over_500 == False:
        DL_range_list = [0]
        for DL_range in df_DL_Range_SL_1.DL_range.to_list():
            DL_range_split = DL_range.split('-')
            DL_range_list.append(int(DL_range_split[1]))
    else:
        DL_range_list = [496]
        for DL_range in df_DL_Range_SL_2.DL_range.to_list():
            DL_range_split = DL_range.split('-')
            DL_range_list.append(int(DL_range_split[1]))

    df_DL_range_list = []
    for i in range(len(DL_range_list)-1):
        DL_below = DL_range_list[i]
        DL_under = DL_range_list[i+1]
        df_DL_range = df.loc[(df[col] > DL_below) & (df[col] <= DL_under)]
            
        df_DL_range['DL_range'] = '{}-{}'.format(DL_below, DL_under)
        df_DL_range['DL_range_code'] = i
        df_DL_range_list.append(df_DL_range)
        
    return pd.concat(df_DL_range_list)


# -------------------------------
def train_test_data_Vung(Vung, col_list, over_500, KDT_train, KDT_test, K, df_feature):
    df = df_feature
    df = df.loc[df['vung']==Vung]
    df = df.loc[df['danh_gia_hieu_qua'] != 'Chưa xác định']

    over_500=False
    
    if over_500 == True:
        df = df.loc[df['tong_port_sau_6t_hien_tai']>496]
        df = divide_DL_range(df, 'tong_port_sau_6t_hien_tai', over_500)
    else:
        df = df.loc[df['tong_port_sau_6t_hien_tai']<=496]
        df = divide_DL_range(df, 'tong_port_sau_6t_hien_tai', over_500)
    

    df_train = df.loc[df['ky_dau_tu'].isin(KDT_train)]
    df_test = df.loc[df['ky_dau_tu'].isin(KDT_test)]
    
    df_train_max_DL = df_train['tong_port_sau_6t_hien_tai'].max()
    df_train_min_DL = df_train['tong_port_sau_6t_hien_tai'].min()
    
    df_test = df_test.loc[(df_test['tong_port_sau_6t_hien_tai'] <= df_train_max_DL)
                          & (df_test['tong_port_sau_6t_hien_tai'] >= df_train_min_DL)
                         ]

    df_numeric_train_x, df_train_y_array, df_train_y = preparing_data(df_train, col_list[11:])
    df_numeric_test_x, df_test_y_array, df_test_y = preparing_data(df_test, col_list[11:])
    
    return df_numeric_train_x, df_train_y_array, df_train_y, df_numeric_test_x, df_test_y_array, df_test_y, df_train, df_test

# -------------------------------
def loc_feature(c_thresh, KDT_test_name):
    df_feature_estimate = (spark.read.parquet(
    "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_selection_dexuatdungluong.parquet/vung_kydautu={}"\
    .format("Vùng 1_test"+KDT_test_name)).toPandas()
                           .rename(columns={
                               'index': 'feature',
                               '0':'c_index_single_feature_{}'.format('Vùng 1')
                           }))

    Vung_list_train = ['Vùng 1', 'Vùng 2', 'Vùng 3', 'Vùng 4', 'Vùng 5', 'Vùng 6', 'Vùng 7']

    for Vung in Vung_list_train[1:]:
        df_Vung=(spark.read.parquet(
    "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_selection_dexuatdungluong.parquet/vung_kydautu={}"\
    .format(Vung+"_test"+KDT_test_name)).toPandas()
    .rename(columns={'index': 'feature','0':'c_index_single_feature_{}'.format(Vung)}))

        df_feature_estimate = df_feature_estimate.merge(df_Vung, on=['feature'], how='outer')

    feature_list = df_feature_estimate.loc[(df_feature_estimate['c_index_single_feature_Vùng 1']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 2']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 3']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 4']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 5']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 6']>c_thresh) &
                            (df_feature_estimate['c_index_single_feature_Vùng 7']>c_thresh) 
                           ].feature.to_list()
    
    return feature_list

# -------------------------------
def loc_feature_all(c_thresh, KDT_train_list, KDT_test_name):
    if KDT_test_name in ['1H2021']:
        KDT_fea_list = ['1H2021']
    else:
        KDT_fea_list = KDT_train_list[1:]
        
    df_feature_KDT = pd.DataFrame({'feature': loc_feature(c_thresh, '1H2021')})

    feature_selection_list = []
    for KDT in KDT_fea_list:
        df_feature_KDT_ = pd.DataFrame({'feature': loc_feature(c_thresh, KDT)})
        df_feature_KDT = df_feature_KDT.merge(df_feature_KDT_, on=['feature'], how='inner')

    return list(set(list(df_feature_KDT.feature.values)))

# -------------------------------
def train_test_data_Vung_NoLabel(Vung, col_list, over_500, KDT_train, KDT_test, K, df_feature):
    df = df_feature
    print('Training {}'.format(Vung))
    df = df.loc[df['vung']==Vung]
    
    df_train = df.loc[df['ky_dau_tu'].isin(KDT_train)]
    df_train = df_train.loc[df_train['danh_gia_hieu_qua'] != 'Chưa xác định']
    
    df_train = divide_DL_range(df_train, 'tong_port_sau_6t_hien_tai', over_500)
    df_numeric_train_x, df_train_y_array, df_train_y = preparing_data(df_train, col_list[11:])
    
    df_test = df.loc[df['ky_dau_tu'].isin(KDT_test)]
    df_test = df_test.loc[df_test['danh_gia_hieu_qua'] == 'Chưa xác định']
    df_numeric_test_x = df_test[col_list[11:]]
    df_test_y_array = None
    df_test_y = None
    
    return df_numeric_train_x, df_train_y_array, df_train_y, df_numeric_test_x, df_test_y_array, df_test_y, df_train, df_test


def model_DXDL(Vung, K, c_thresh, KDT_train_list, KDT_test_name,df_feature):
    print("test ", KDT_test_name)
    prob = prob_Vung(Vung)
    model = model_Vung(Vung)
    KDT_test_list = [KDT_test_name]
    over_500 = False
        
    Vung_list = []
    KDT_test_name_list = []
    
    column_list = loc_feature_all(c_thresh, KDT_train_list, KDT_test_name)
    for con_index in ['port_dung_sau_6t_hien_tai', 'tong_port_sau_6t_hien_tai', 'danh_gia_hieu_qua', 'nguong_tb','hqkt_6t_hieu_tai','ky_dau_tu','phuong','quan', 'tinh', 'chi_nhanh', 'vung']:
        column_list.insert(0,con_index)    

    Vung_list.append(Vung)

    df_numeric_train_x, df_train_y_array, df_train_y, df_numeric_test_x, df_test_y_array, df_test_y, df_train, df_test  = train_test_data_Vung(Vung, column_list, over_500, KDT_train_list, KDT_test_list, K, df_feature)
    rsf = model
    print(model)

    rsf.fit(df_numeric_train_x, df_train_y_array)

    print('saving {} model...'.format(KDT_test_name))
    filename = "/mnt/projects-data/phat_trien_ha_tang/model/dexuatdungluong/model_DXDL_Label_{}_{}.pkl".format(Vung, KDT_test_name)
    # save model
    pickle.dump(model, open(filename, "wb"))
    # load model
    # loaded_model = pickle.load(open(filename, "rb"))
    
    surv = rsf.predict_survival_function(df_numeric_test_x.fillna(0))

    df_KetQua_list = []

    for i in range(len(df_test.index)):
        df_KetQua = df_test.iloc[[i]]
        df_KetQua_DL_range_code = df_KetQua['DL_range_code'].values[0]
        
        # ---------------
        df_test_sample = pd.DataFrame({'DL_range_code': surv[i].x,
                                      'surv_prob': surv[i].y
                                     })
            
        surv_prob_thresh = prob
        
        df_test_sample['result_predict_prob'] = np.where(df_test_sample['surv_prob'] >= surv_prob_thresh, 'Hiệu quả', 'Không hiệu quả')
        
        # find mapping DL
        df_test_sample_map = df_test_sample.loc[df_test_sample['DL_range_code']==df_KetQua_DL_range_code]
        
        try:
            test_sample_result = df_test_sample_map['result_predict_prob'].values[0]
        except:
            df_KetQua['result_predict'] = 'Hiệu quả'
            df_KetQua['surv_prob'] = prob
        else:
            df_KetQua['result_predict'] = test_sample_result
            df_KetQua['surv_prob'] = df_test_sample_map.surv_prob.values[0]


        df_KetQua_list.append(df_KetQua)


    df_KetQua_test = pd.concat(df_KetQua_list)
    
    label = df_KetQua_test['danh_gia_hieu_qua'].to_list()
    label_pred = df_KetQua_test['result_predict'].to_list()

    y_actu = pd.Series(label, name='Actual')
    y_pred = pd.Series(label_pred, name='Predicted')
    
    try:
        precision = precision_score(y_actu, y_pred, pos_label = 'Hiệu quả')
        recall = recall_score(y_actu, y_pred, pos_label = 'Hiệu quả')
    except:
        print('precision = Ko Tinh Duoc')
        print('recall = Ko Tinh Duoc') 
    else:
        print('precision = ', precision)
        print('recall = ', recall)
    
    return df_KetQua_test

def model_DXDL_NoLabel(Vung, K, c_thresh, KDT_test, KDT_train, KDT_test_name, df_DL_range_ref, df_feature):
    prob = prob_Vung(Vung)
    model = model_Vung(Vung)
    KDT_test = [KDT_test_name]
    over_500 = False 
        
    Vung_list = []
    KDT_test_name_list = []
    
    column_list = loc_feature_all(c_thresh, KDT_train, KDT_test_name)
    for con_index in ['port_dung_sau_6t_hien_tai', 'tong_port_sau_6t_hien_tai', 'danh_gia_hieu_qua', 'nguong_tb','hqkt_6t_hieu_tai','ky_dau_tu','phuong','quan', 'tinh', 'chi_nhanh', 'vung']:
        column_list.insert(0,con_index)    

    Vung_list.append(Vung)

    df_numeric_train_x, df_train_y_array, df_train_y, df_numeric_test_x, df_test_y_array, df_test_y, df_train, df_test  = train_test_data_Vung_NoLabel(Vung, column_list, over_500, KDT_train, KDT_test, K, df_feature)
    rsf = model
    # print(model)

    rsf.fit(df_numeric_train_x, df_train_y_array)

    filename = "/mnt/projects-data/phat_trien_ha_tang/model/dexuatdungluong/model_DXDL_NoLabel_{}_{}.pkl".format(Vung, KDT_test_name)
    # save model
    pickle.dump(model, open(filename, "wb"))
    # load model
    # loaded_model = pickle.load(open(filename, "rb"))

    surv = rsf.predict_survival_function(df_numeric_test_x.fillna(0))

    df_KetQua_list = []
    DL_fix = 0
    for i in range(len(df_test.index)):
    # for i in range(3):
        df_KetQua = df_test.iloc[[i]]
        df_test_sample = pd.DataFrame({'DL_range_code': surv[i].x,
                                      'surv_prob': surv[i].y
                                     })
            
        # print(KDT_train_)
        surv_prob_thresh = prob
        
        df_test_sample['result_predict_prob'] = np.where(df_test_sample['surv_prob'] >= surv_prob_thresh, 'Hiệu quả', 'Không hiệu quả')
        
        try:
            df_test_sample_map = df_test_sample.loc[df_test_sample['result_predict_prob']=='Hiệu quả'].sort_values('DL_range_code', ascending=False).iloc[[0]]
        except:
            DL_fix += 1
            # print(df_test_sample)
            df_test_sample['result_predict_prob'] = np.where(df_test_sample['surv_prob'] >= (prob-0.1), 'Hiệu quả', 'Không hiệu quả')
            try:
                df_test_sample_map = df_test_sample.loc[df_test_sample['result_predict_prob']=='Hiệu quả'].sort_values('DL_range_code', ascending=False).iloc[[0]]
            except:
                df_KetQua['DL_range_code'] = 0
                df_KetQua['DL_range'] = '0-8'
                df_KetQua['result_predict'] = 'Hiệu quả'
                df_KetQua['surv_prob'] = 0.5
            else:
                DL_range_code = df_test_sample_map.DL_range_code.values[0]
                df_KetQua['DL_range'] = df_DL_range_ref.loc[df_DL_range_ref['DL_range_code']==DL_range_code].DL_range.values[0]
                df_KetQua['DL_range_code'] = DL_range_code
                df_KetQua['result_predict'] = df_test_sample_map.result_predict_prob.values[0]
                df_KetQua['surv_prob'] = df_test_sample_map.surv_prob.values[0]
            
            # print(df_KetQua[['DL_range', 'result_predict', 'surv_prob']])
        else:
            DL_range_code = df_test_sample_map.DL_range_code.values[0]
            df_KetQua['DL_range'] = df_DL_range_ref.loc[df_DL_range_ref['DL_range_code']==DL_range_code].DL_range.values[0]
            df_KetQua['DL_range_code'] = DL_range_code
            df_KetQua['result_predict'] = df_test_sample_map.result_predict_prob.values[0]
            df_KetQua['surv_prob'] = df_test_sample_map.surv_prob.values[0]


        df_KetQua_list.append(df_KetQua)
        df_KetQua[['DL_range', 'result_predict', 'surv_prob']]

    # print('SL Phường có XS quá thấp: ', DL_fix)
    df_KetQua_test = pd.concat(df_KetQua_list)
    
    print('precision = No Label')
    print('recall = No Label') 
    
    return df_KetQua_test

def feature_selection(KDT_test, KDT_train_list, df_feature, col_to_use, K):
    KDT_test_list = [KDT_test]
    Vung_list = ['Vùng 1','Vùng 2', 'Vùng 3', 'Vùng 4', 'Vùng 5', 'Vùng 6', 'Vùng 7']
    over_500=False
    print('feature selection for ', KDT_test)
    
    for Vung in Vung_list:
        df_numeric_train_x, df_train_y_array, df_train_y, df_numeric_test_x, df_test_y_array, df_test_y, df_train, df_test  = train_test_data_Vung(Vung, col_to_use, over_500, KDT_train_list, KDT_test_list, K, df_feature)

        df_numeric_train_x = df_numeric_train_x.fillna(0)

        scores = fit_and_score_features(df_numeric_train_x.values, df_train_y_array)

        df_feature_estimate = pd.Series(scores, index=df_numeric_train_x.columns).sort_values(ascending=False).reset_index()
        df_ = spark.createDataFrame(df_feature_estimate)
        df_ = df_.withColumn('vung_kydautu', lit(Vung+"_test"+KDT_test))
        df_.coalesce(1)\
            .write.mode("overwrite")\
            .partitionBy('vung_kydautu')\
            .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_selection_dexuatdungluong.parquet/")\
            .save()

    print('Done Feature Selection ---------------- {}'.format(KDT_test))

def process(K, c_thresh, KDT_train_list, KDT_test_name, df_DL_range_ref, df_feature):
    KetQua_Vung_Label_list = []
    KetQua_Vung_NoLabel_list = []
    Vung_list = ['Vùng 1','Vùng 2', 'Vùng 3', 'Vùng 4', 'Vùng 5', 'Vùng 6', 'Vùng 7']
    for Vung in Vung_list:
        print('-------------------------------------', Vung)

        KDT_test = [KDT_test_name] #list
        # print('test ',KDT_test)
        
        KDT_train = KDT_train_list
        # print('train ',KDT_train)
        
        try:
            # co label
            df_DXDL_Label = model_DXDL(Vung, K, c_thresh, KDT_train_list, KDT_test_name, df_feature)
            df_ = spark.createDataFrame(df_DXDL_Label)
            df_ = df_.withColumn('vung_kydautu', lit(Vung+"_"+KDT_test_name))
            df_.coalesce(1)\
                .write.mode("overwrite")\
                .partitionBy('vung_kydautu')\
                .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_label_dexuatdungluong.parquet/")\
                .save()

            KetQua_Vung_Label_list.append(df_DXDL_Label)
            training_NoLabel = 'not yet'
        except:
            # khong co label
            training_NoLabel = 'done'
            df_DXDL_NoLabel = model_DXDL_NoLabel(Vung, K, c_thresh, KDT_test, KDT_train, KDT_test_name, df_DL_range_ref, df_feature)
            df_ = spark.createDataFrame(df_DXDL_NoLabel)
            df_ = df_.withColumn('vung_kydautu', lit(Vung+"_"+KDT_test_name))
            df_.coalesce(1)\
                .write.mode("overwrite")\
                .partitionBy('vung_kydautu')\
                .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_nolabel_model_dexuatdungluong.parquet/")\
                .save()
            KetQua_Vung_NoLabel_list.append(df_DXDL_NoLabel)
            
        if training_NoLabel != 'done':
            df_DXDL_NoLabel = model_DXDL_NoLabel(Vung, K, c_thresh, KDT_test, KDT_train, KDT_test_name, df_DL_range_ref, df_feature)
            df_ = spark.createDataFrame(df_DXDL_NoLabel)
            df_ = df_.withColumn('vung_kydautu', lit(Vung+"_"+KDT_test_name))
            df_.coalesce(1)\
                .write.mode("overwrite")\
                .partitionBy('vung_kydautu')\
                .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/feature_nolabel_model_dexuatdungluong.parquet/")\
                .save()
            KetQua_Vung_NoLabel_list.append(df_DXDL_NoLabel)
            
    if training_NoLabel == 'not yet':
        df_process_Label = pd.concat(KetQua_Vung_Label_list)
        df_process_NoLabel = pd.concat(KetQua_Vung_NoLabel_list)
        df_result = pd.concat([df_process_Label, df_process_NoLabel])
        print(KDT_test_name)
        print(classification_report(df_result.loc[df_result['danh_gia_hieu_qua']!='Chưa xác định']['danh_gia_hieu_qua'],
                                    df_result.loc[df_result['danh_gia_hieu_qua']!='Chưa xác định']['result_predict'])
             )
        print('precision (all)= ', 
              classification_report(df_result.loc[df_result['danh_gia_hieu_qua']!='Chưa xác định']['danh_gia_hieu_qua'], 
                                    df_result.loc[df_result['danh_gia_hieu_qua']!='Chưa xác định']['result_predict'], output_dict=True)
              ['Hiệu quả']['precision']
             )
        
    else:
        df_result = pd.concat(KetQua_Vung_NoLabel_list)
        
    df_result = df_result[['vung','chi_nhanh','tinh', 'quan', 'phuong', 'ky_dau_tu',
                       'danh_gia_hieu_qua', 'result_predict', 'DL_range', 'surv_prob']]
    df_ = spark.createDataFrame(df_result)
    df_ = df_.withColumn('kydautu', lit(KDT_test_name))
    df_.coalesce(1)\
        .write.mode("overwrite")\
        .partitionBy('kydautu')\
        .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/result_dexuatdungluong.parquet/")\
        .save()
    
    print('DONE De Xuat Dung Luong ', KDT_test_name)
def process_DXDL(date):

    if (int(date[5:7])>=3)&(int(date[5:7])<9):
        kydautu = '2H'+str(int(date[:4]))
        date=str(int(date[:4]))+'-03-01'
    else:
        if (int(date[5:7])>=1)&(int(date[5:7])<3):
            kydautu= '1H'+str(int(date[:4]))
            date=str(int(date[:4])-1)+'-09-01'
        else:
            kydautu= '1H'+str(int(date[:4])+1)
            date=str(int(date[:4]))+'-09-01' 
    path_out_ds = '/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/result_dexuatdungluong.parquet/kydautu={}'.format(kydautu)
    if not hdfs_file_exists(path_out_ds):
        col_to_use, df_feature, K, c_thresh, KDT_fill_list, KDT_train_list, KDT_test_name, df_DL_range_ref = get_context(date)
        feature_selection(KDT_test_name, KDT_train_list, df_feature, col_to_use, K)
        process(K, c_thresh, KDT_train_list, KDT_test_name, df_DL_range_ref, df_feature)

def process_output(date):
    if (int(date[5:7])>=3)&(int(date[5:7])<9):
        kydautu = '2H'+str(int(date[:4]))
        date=str(int(date[:4]))+'-03-01'
    else:
        if (int(date[5:7])>=1)&(int(date[5:7])<3):
            kydautu= '1H'+str(int(date[:4]))
            date=str(int(date[:4])-1)+'-09-01'
        else:
            kydautu= '1H'+str(int(date[:4])+1)
            date=str(int(date[:4]))+'-09-01'
    path_out_ds = '/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/result_phattrienhatang.parquet/kydautu={}'.format(kydautu)
    if not hdfs_file_exists(path_out_ds):
        validate_w = spark.read.parquet('/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/danh_sach_goi_y_tiem_nang.parquet/kydautu={}'.format(kydautu)).toPandas()
        df_dl = spark.read.parquet('/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/result_dexuatdungluong.parquet/kydautu={}'.format(kydautu)).toPandas()
        df_dl.columns = ['vung', 'chi_nhanh', 'tinh', 'quan', 'phuong', 'ky_dau_tu', 
               'danh_gia_hieu_qua', 'result_predict', 'DL_range', 'surv_prob']
        df_dl = df_dl.sort_values(['vung', 'chi_nhanh', 'tinh', 'quan', 'phuong', 'ky_dau_tu', 
                                   'surv_prob','DL_range'],ascending=False)
        df_dl.drop_duplicates(subset=['tinh', 'quan', 'phuong'],keep='first', inplace=True)
        
        validate_full = validate_w.merge(df_dl[['tinh', 'quan', 'phuong','DL_range','surv_prob']], 
                                         on=['tinh', 'quan', 'phuong'], how='outer')
        df_ = spark.createDataFrame(validate_full)
        df_ = df_.withColumn('kydautu', lit(kydautu))
        df_.coalesce(1)\
            .write.mode("overwrite")\
            .partitionBy('kydautu')\
            .option("path", "/data/fpt/ftel/infra/dwh/phat_trien_ha_tang/result_phattrienhatang.parquet/")\
            .save()