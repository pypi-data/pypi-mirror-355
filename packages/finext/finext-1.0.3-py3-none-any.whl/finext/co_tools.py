#co_tools_beta.py
from finlab import data
import finlab
import pickle
import os
import plotly.express as px
import plotly.graph_objects as go
from finlab.backtest import sim
from finlab.tools.event_study import create_factor_data
import tqdm
import numpy as np 
import pandas as pd
from finlab.dataframe import FinlabDataFrame
import cufflinks as cf
from sklearn.linear_model import LinearRegression
from datetime import datetime
from IPython.display import display, HTML
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from typing import List, Tuple, Dict
import fitz  # PyMuPDF

# CatBoost 相關套件
from catboost import CatBoostRegressor, CatBoostClassifier
import matplotlib.pyplot as plt
import seaborn as sns

db_path = "/home/sb0487/trade/finlab/finlab_db" #資料儲存路徑



"""
程式碼傷眼滲入


"""
#若未來相關函式增多再開發
class cofindf(FinlabDataFrame):
    @property
    def pr(self):
        # 計算每行的有效值數量
        valid_counts = self.count(axis=1)
        valid_counts = valid_counts.replace(0, np.nan)
        rank_df = self.rank(axis=1, ascending=True, na_option='keep')
        pr_df = rank_df.div(valid_counts, axis=0) * 100
        return pr_df


#載入區----------------------------------------------------------------------------------------------------------------

class Codata():
    def __init__(self, df_type="findf", db_path="", force_download=False, 
                 html_file="tmp_finlab_report.html",
                 image_file_1="tmp_finlab_report_img1.png", 
                 image_file_2="tmp_finlab_report_img2.png"):
        # super().__init__()
        self.df_type = df_type
        self.db_path = db_path
        data.set_storage(data.FileStorage(db_path))
        data.use_local_data_only = False
        data.force_cloud_download = force_download

        #HTML與圖片暫存
        self.html_file = html_file
        self.image_file_1 = image_file_1
        self.image_file_2 = image_file_2
    
    def get_file_path(self,file_name): 
        return os.path.join(self.db_path, file_name.replace(":", "#") + ".pickle")

    
    def get_update_time(self,filename):
        if os.path.exists(self.get_file_path(filename)):
            modification_time = os.path.getmtime(self.get_file_path(filename))
            last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modification_time))
            print(f"最後更新時間: {last_modified}, {[filename]}")
        else:
            print("檔案不存在,請柬查路徑")

    
    def ouput_type_df(self,file_df):
        if self.df_type == "findf":
            type_df = file_df
        elif self.df_type == "cudf":
            import cudf
            type_df = cudf.DataFrame(file_df)
        elif self.df_type == "sparkdf":
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.appName("Pandas to Spark DataFrame").getOrCreate()
            type_df = spark.createDataFrame(file_df)
        return type_df


    def get(self, file_name, force_download = False ):
        if not os.path.isdir(self.db_path):
            raise OSError("資料夾路徑錯誤")

        if force_download == True:
            data.force_cloud_download = True 
            type_df = data.get(file_name)
            data.force_cloud_download = False
        else:
            type_df = data.get(file_name)
            
        #選擇df輸出型態
        type_df = self.ouput_type_df(type_df)
        self.get_update_time(file_name)
        return type_df

    # @staticmethod
    # def get_update_time(filename):
    #     data.get_update_time(filename)  # 调用 data 类的 get_update_time 方法

    

#產業區----------------------------------------------------------------------------------------------------------------
    
    #把category拆成主分類與細分類
    def get_industry_pro(self):
        industry = self.get('security_industry_themes').dropna()
        def extract_majcategory(category_list):
            matching_categories = set([category.split(':')[0] for category in eval(category_list) if ':' in category])
            return str(list(matching_categories))
        
        def extract_subcategory(category_list):
            matching_categories = [category.split(':')[-1] for category in eval(category_list) if ':' in category]
            return str(matching_categories)
        
        # 应用自定义函数到 DataFrame 的每一行
        industry['maj_category'] = industry['category'].apply(extract_majcategory)
        industry['sub_category'] = industry['category'].apply(extract_subcategory)
        
        return industry

    
    def show_industry(self):
        industry = self.get_industry_pro()
        sub_category_counts_df = pd.DataFrame(industry['sub_category'].apply(eval).explode('sub_category').value_counts()).reset_index()
        maj_category_counts_df = pd.DataFrame(industry['maj_category'].apply(eval).explode('maj_category').value_counts()).reset_index()
        
        industry["maj_category"] = industry["maj_category"].apply(eval)
        industry["sub_category"] = industry["sub_category"].apply(eval)
        industry_explode = industry.explode('maj_category').explode('sub_category')
        industry_explode["count"] = 1
        
        fig = px.treemap(industry_explode, path=[px.Constant("台股產業總總覽"), "maj_category", "sub_category","name"], values='count')
        fig.update_layout(
            margin=dict(t=1, l=1, r=1, b=1)
        )
        
        fig.show()
        return maj_category_counts_df,sub_category_counts_df
    
    def filter_industry(self,file_df, keyword_list, category_type = "maj_category", remove_or_add="remove", exact_or_fuzzy="fuzzy"):
        industry_pro = self.get_industry_pro()
        
        if exact_or_fuzzy == "fuzzy":
            if remove_or_add == "remove":
                
                file_filtered_df = (file_df
                    .loc[:, ~file_df.columns.isin(
                        industry_pro[industry_pro[category_type]
                        .apply(lambda x: bool(set(eval(x)) & set(keyword_list)))]['stock_id']
                        .tolist())]
                )
           
            elif remove_or_add == "add":
                file_filtered_df = (file_df
                    .loc[:, file_df.columns.isin(
                        industry_pro[industry_pro[category_type]
                        .apply(lambda x: bool(set(eval(x)) & set(keyword_list)))]['stock_id']
                        .tolist())]
                )
    
        
        if exact_or_fuzzy == "exact":
            if remove_or_add == "remove": # 完全一樣才移除
                
                file_filtered_df = (file_df
                    .loc[:, ~file_df.columns.isin(
                        industry_pro[industry_pro[category_type]
                        .apply(lambda x: bool(set(eval(x)) == set(keyword_list)))]['stock_id']
                        .tolist())]
                )
    
            elif remove_or_add == "add": # 完全一樣才加入
                file_filtered_df = (file_df
                    .loc[:, file_df.columns.isin(
                        industry_pro[industry_pro[category_type]
                        .apply(lambda x: bool(set(eval(x)) == set(keyword_list)))]['stock_id']
                        .tolist())]
                )
        
        return file_filtered_df



    
    
    #把category拆成主分類與細分類
    def get_industry_pro(self):
        industry = self.get('security_industry_themes').dropna()
        def extract_majcategory(category_list):
            matching_categories = set([category.split(':')[0] for category in eval(category_list) if ':' in category])
            return str(list(matching_categories))
        
        def extract_subcategory(category_list):
            matching_categories = [category.split(':')[-1] for category in eval(category_list) if ':' in category]
            return str(matching_categories)
        
        # 应用自定义函数到 DataFrame 的每一行
        industry['maj_category'] = industry['category'].apply(extract_majcategory)
        industry['sub_category'] = industry['category'].apply(extract_subcategory)
        
        return industry

#便利工具區----------------------------------------------------------------------------------------------------------------

        # def month_forward_sell(self,forward_days = 1):
        #     exits_df = self.get('price:收盤價')<0
        #     def update_row(row):
        #         if row.name in self.monthly_revenue.index:
        #             return True
        #         else:
        #             return row
        
        #     rev_date = exits_df.apply(update_row, axis=1)
        #     rev_date_shifted = rev_date.shift(-1)
        #     for i in range(1,forward_days+1):
        #         rev_date_shifted_n = rev_date.shift(-i)
        #         rev_date_shifted = rev_date_shifted  | rev_date_shifted_n
                
        return rev_date_shifted
    
    #把日資料轉成月資料(營收發布截止日),他們有說之後會改成電子檔上傳日
    def day_to_month(self,file_df):
        monthly_index_df = FinlabDataFrame(index=self.get("monthly_revenue:當月營收").index)
        file_df  = monthly_index_df.join(file_df, how='left')
        return file_df

    def to_day(self,file_df):
        monthly_index_df = FinlabDataFrame(index=self.get('price:收盤價').index)
        file_df  = monthly_index_df.join(file_df, how='left')
        return file_df
    
    #轉為日資料並藉由資料異動時間點保留財報發布日資訊(index_str_to_date會向下填滿)    
    def q_to_day(self,file_df):
        file_df =file_df.index_str_to_date()
        file_df =file_df.where(file_df.ne(file_df.shift()), np.nan)
        day_index_df = FinlabDataFrame(index=self.get('price:收盤價').index)
        c = pd.concat([file_df,day_index_df])
        file_df = FinlabDataFrame(c[~c.index.duplicated()].sort_index())
        return file_df

    def q_to_weekday(self,quarter_df):
        """
        更快速的版本，使用pandas內建方法
        """
        # 取得收盤價數據並創建平日index
        close = self.get('price:收盤價')
        close_df = close < 0  # 創建boolean數據框，保留平日index
        
        # 處理quarter_df的index和數據
        quarter_df = quarter_df.index_str_to_date()
        quarter_df = quarter_df.where(quarter_df.ne(quarter_df.shift()), np.nan)
        
        # 確保index是datetime格式並排序
        close_df = close_df.copy()
        quarter_df.index = pd.to_datetime(quarter_df.index)
        close_df.index = pd.to_datetime(close_df.index)
        
        # 創建結果數據框
        result_df = pd.DataFrame(
            index=close_df.index,
            columns=quarter_df.columns,
            dtype=float
        )
        
        # 對每個quarter的日期，找到close_df中最近的較小日期
        for quarter_date in quarter_df.index:
            # 找到該日期對應的工作日（最近的較小或等於的工作日）
            target_date = close_df.index[close_df.index <= quarter_date]
            if len(target_date) > 0:
                target_date = target_date[-1]  # 取最近的
                result_df.loc[target_date] = quarter_df.loc[quarter_date]
        
        # 用close的index重新索引結果
        result_df = result_df.reindex(close.index)[quarter_df.index[0]:]
        
        return result_df


    def get_pr(self,file_df):
        #判斷是否為季資料
        text = file_df.index[1]  # 假設 roa.index[0] 是 '2013-Q1'
        try:
            if 'Q' in text:
                print("finlab 1.2.27版本以後季資料rank會轉成日期，get_pr亦同")
        except:
            pass
        # 計算每行的有效值數量
        rank_df = file_df.rank(axis=1, ascending=True, na_option='keep')
        valid_counts = rank_df.count(axis=1)
        valid_counts[valid_counts == 0] = np.nan
        pr_df = rank_df.div(valid_counts, axis=0) * 100
        
        return pr_df
   
    def display_report_statis(self, file_df):
        mean_return = file_df["return"].mean()
        return_std = file_df["return"].std()
        mean_period = file_df["period"].mean()
        
        # 複利報酬率計算
        log_return_mean = mean_return - 0.5 * (return_std ** 2)
        periods_per_year = 240 / mean_period
        annual_compound_return = (1 + log_return_mean) ** periods_per_year - 1
        
        # 計算勝率
        win_rate = (file_df["return"] > 0).mean()
        
        # 組成 JSON 資料 (小數位數比照 HTML)
        stats_json = {
            "交易筆數": len(file_df),
            "平均報酬率": f"{mean_return * 100:.2f}%",  # 3位小數轉百分比 = 1位小數
            "平均MDD": f"{file_df['mdd'].mean():.3f}",
            "報酬率標準差": f"{return_std:.3f}",
            "平均持有期間(交易日)": f"{mean_period:.3f}",
            "勝率": f"{win_rate * 100:.2f}%",  # 3位小數轉百分比 = 1位小數
            "最大年化報酬率(波動調整_泰勒展開)": f"{annual_compound_return * 100:.2f}%"  # 3位小數轉百分比 = 1位小數
        }
        
        html_content = """
        <sorry style="font-size: larger;">交易統計</sorry>
        <ul>
          <li>交易筆數: {}</li>
          <li>平均報酬率: {}</li>
          <li>平均MDD: {}</li>
          <li>報酬率標準差: {}</li>
          <li>平均持有期間(交易日): {}</li>
          <li>勝率: {}</li>
          <li>最大年化報酬率(波動調整_泰勒展開): {}</li>
        </ul>
        """.format(len(file_df),
                   stats_json["平均報酬率"],
                   stats_json["平均MDD"],
                   stats_json["報酬率標準差"],
                   stats_json["平均持有期間(交易日)"],
                   stats_json["勝率"],
                   stats_json["最大年化報酬率(波動調整_泰勒展開)"])
        
        display(HTML(html_content))
        return stats_json
#爬蟲區----------------------------------------------------------------------------------------------------------------------
    
    #爬年報
    def crawl_annual_report_(self,year,symbol,save_dir,sleep = 2):
        #init
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        year = str(year)
        symbol = str(symbol)
        
    
        d = webdriver.Chrome(options=chrome_options)
        d.maximize_window()
    
        try:
            while True:
                d.get(f'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id={symbol}&year={year}&mtype=F&dtype=F04&') 
                time.sleep(sleep)
                
                page_content = d.page_source
                if "查詢過量" in page_content:
                    print(f"當前股票為{symbol},查詢過量，被證交所檔下，休息10秒")
                    time.sleep(10)
                    continue  
                else:
                    break  # 如果没有查詢過量，退出循环
    
            pdf_link = d.find_element(By.XPATH, "//a[contains(@href, 'javascript:readfile2') and contains(@href, 'F04')]")
            pdf_link.click()
            time.sleep(sleep)
        
            # 切換分頁
            all_tabs = d.window_handles
            d.switch_to.window(all_tabs[1])
            time.sleep(sleep)
    
            
            # 找到pdf連結,注意此連結為不定時浮動
            pdf_link2 = d.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
            pdf_url = pdf_link2.get_attribute('href')
        
            
            # 建構dir(若無),保存pdf
            os.makedirs(save_dir, exist_ok=True)
            file_name = f"{year}_{symbol}.pdf" 
            file_path = os.path.join(save_dir, file_name)
            
            # 下载 PDF 文件并保存
            response = requests.get(pdf_url)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"PDF 文件已保存到: {file_path}")
            failed_symbol =None
            
        except ModuleNotFoundError as e:
            print(f"Module not found error: {e}")
            
        except NameError as e:
            print(f"Name not defined error: {e}") 
            
        except Exception as e:
            print(f"{symbol}_{year}年年報未找到")
            failed_symbol = symbol
            
        finally:
            d.quit()
            
        return failed_symbol
    #爬年報,多個
    def crawl_annual_reports(self,year,stock_list,save_dir,sleep = 2):
        failed_list = list(filter(None, (self.crawl_annual_report_(year, x, save_dir, sleep) for x in stock_list)))
        return failed_list
        
    #爬季報
    def crawl_quarterly_report_(self,year,quarter,symbol,save_dir,sleep = 2):
        
        #init
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        year = str(year)
        symbol = str(symbol)
        format_quarter = "0"+str(quarter)
        ad = str(int(year)+1911)
        # 初始化Chrome瀏覽器
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
    
        d = webdriver.Chrome(options=chrome_options)
        d.maximize_window()
    
        try:
            while True:
                d.get(f'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id={symbol}&year={year}&seamon=&mtype=A&dtype=AI1&') 
                time.sleep(sleep)
                
                page_content = d.page_source
                if "查詢過量" in page_content:
                    print(f"當前股票為{symbol},查詢過量，被證交所檔下，休息10秒")
                    time.sleep(10)
                    continue  
                else:
                    break  # 如果没有查詢過量，退出循环
           
            pdf_name = f"{ad}{format_quarter}_{symbol}_AI1.pdf"
            pdf_link = d.find_element(By.XPATH, f"//a[contains(@href, 'javascript:readfile2') and contains(@href,'{pdf_name}')]")
            pdf_link.click()
            time.sleep(sleep)
        
            # 切換分頁
            all_tabs = d.window_handles
            d.switch_to.window(all_tabs[1])
            time.sleep(sleep)
    
            # 找到pdf連結,注意此連結為不定時浮動
            pdf_link2 = d.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
            pdf_url = pdf_link2.get_attribute('href')
        
            
            # 建構dir(若無),保存pdf
            os.makedirs(save_dir, exist_ok=True)
            file_name = f"{year}_Q{quarter}_{symbol}.pdf" 
            file_path = os.path.join(save_dir, file_name)
            
            # 下载 PDF 文件并保存
            response = requests.get(pdf_url)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"PDF 文件已保存到: {file_path}")
            failed_symbol =None
            
        except ModuleNotFoundError as e:
            print(f"Module not found error: {e}")
            
        except NameError as e:
            print(f"Name not defined error: {e}") 
        
        except:
            print(f"{symbol}_{year}_Q{quarter}季報未找到")
            failed_symbol = symbol
            
        finally:
            d.quit()
        return failed_symbol
    #爬季報,多個
    def crawl_quarterly_reports(self,year,quarter,stock_list,save_dir,sleep = 2):
        failed_list = list(filter(None, (self.crawl_quarterly_report_(year,quarter, x, save_dir, sleep) for x in stock_list)))
        return failed_list


    #用save_dir抓下來的檔案與全部的股票代號清單all_stock_list比較,找出尚未下載的pdf
    def get_undownloaded_stocks(self,save_dir,all_stock_list):
        download_stock_list = [f.split('.')[0][-4:] for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f))]
        result = [elem for elem in all_stock_list if elem not in download_stock_list]
        return result

#讀檔pdf區----------------------------------------------------------------------------------------------------------------------
    
    #用spark分散式讀取
    def load_pdf_spark(self,stock_list,pdf_path,memory = "5g"):
        from pyspark.sql import SparkSession
        
        # 起 Spark
        spark = SparkSession.builder.appName("Read PDFs with Spark")\
        .config("spark.driver.memory", memory)\
        .config("spark.driver.maxResultSize", memory)\
        .getOrCreate() # 內存大小
    
        def process_pdf(filename):
            if filename.endswith('.pdf'):
                #stock_symbol = filename.split('_')[1].split('.')[0] # 分割,取出股票代耗
                stock_symbol = filename.split('.')[0][-4:]
                if stock_symbol in stock_list: 
                    file_path = os.path.join(pdf_path, filename)
                    content = "".join(page.get_text() for page in fitz.open(file_path)) #打開pdf, 逐行讀取並合併
                    return stock_symbol, content
    
        # 使用 Spark 讀取每個 PDF 文件
        pdf_contents = spark.sparkContext.parallelize(os.listdir(pdf_path)).map(process_pdf).filter(lambda x: x).collect()
        
        # 將結果轉換為 Pandas DataFrame
        pdf_df = pd.DataFrame(pdf_contents, columns=["Stock Symbol", "PDF Content"]).set_index("Stock Symbol")
        return pdf_df

    #單線程讀取
    def load_pdf(self,stock_list, pdf_path):
        def process_pdf(filename):
            if filename.endswith('.pdf'):
                stock_symbol = filename.split('.')[0][-4:]
                if stock_symbol in stock_list:
                    file_path = os.path.join(pdf_path, filename)
                    content = "".join(page.get_text() for page in fitz.open(file_path))  
                    return stock_symbol, content
        
        pdf_contents = [process_pdf(filename) for filename in os.listdir(pdf_path) if filename.endswith('.pdf')]
        pdf_contents = [item for item in pdf_contents if item is not None]
        
        # 将结果转换为 Pandas DataFrame
        pdf_df = pd.DataFrame(pdf_contents, columns=["Stock Symbol", "PDF Content"]).set_index("Stock Symbol")
        return pdf_df

#相關係數區----------------------------------------------------------------------------------------------------------------------

    # 相關數排名
    def get_corr_ranked(self,stock_symbol: str, close: pd.DataFrame) -> None:
        stock_symbol = str(stock_symbol)
        correlation_with_target = close.corr()[stock_symbol].drop(stock_symbol)
        most_related = correlation_with_target.nlargest(30)
        least_related = correlation_with_target.nsmallest(30)
        
        for title, data in [("Most", most_related), ("Least", least_related)]:
            fig = px.bar(data, title=f'Top 30 Stocks {title} Related to {stock_symbol}', labels={'value': 'Correlation', 'index': 'Stocks'})
            fig.show()

    # 時間序列比較圖
    def get_tm_series_chart(self,stock_symbols: list, close: pd.DataFrame, lag: int = 0) -> None:
        stock1, stock2 = map(str, stock_symbols)
        
        if lag > 0:
            shifted_stock2 = close[stock2].shift(lag)
            valid_idx = ~shifted_stock2.isna()
            stock2_values = shifted_stock2[valid_idx]
            stock1_values = close[stock1][valid_idx]
        else:
            stock1_values = close[stock1]
            stock2_values = close[stock2]
        
        correlation = stock1_values.corr(stock2_values)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=close.index, y=close[stock1], mode='lines', name=stock1, yaxis='y1'))
        fig.add_trace(go.Scatter(x=close.index, y=shifted_stock2 if lag > 0 else close[stock2], mode='lines', name=f'{stock2} (lag={lag})', yaxis='y2'))
        
        fig.update_layout(
            title=f'時間序列比較圖 (lag={lag}, correlation={correlation:.2f})',
            xaxis=dict(title='日期'),
            yaxis=dict(title=f'{stock1} 收盤價', side='left'),
            yaxis2=dict(title=f'{stock2} 收盤價', side='right', overlaying='y')
        )
        
        fig.show()

#因子測試區----------------------------------------------------------------------------------------------------------------------



    def get_quartertly_factor_analysis(self,factor_list: List[str], pr: Tuple[int, int], n_high_or_low: int)-> pd.DataFrame:
        close = self.get('price:收盤價')
        market_value = self.get('etl:market_value')
        
        # Initialize DataFrame to store results
        factor_report_df_all = pd.DataFrame(columns=[
            "因子名稱", "策略條件", "PR_Range", "限制因子數值正負", "創n期高or低", "總交易筆數", 
            "策略年化報酬率", "策略MDD", "策略sortino(日)", "個股平均報酬率", "個股平均MDD", 
            "個股報酬率標準差", "個股平均持有期間(交易日)", "個股平均處於獲利天數", 
            "個股最大年化複利報酬"
        ])
    
        def calculate_factor_report(conditions: pd.DataFrame, factor_name: str, strategy_type: str, pr: Tuple[int, int], pn: str, n_high_or_low: int):
            pr_range = np.nan
            if strategy_type in ["qoq", "yoy", "factor_market_value_ratio","origin_value"]:
                n_high_or_low = np.nan
                pr_range = f"{pr[0]}-{pr[1]}"
            
            try:
                # Simulate strategy and generate report
                report = sim(position=conditions, position_limit=1, fee_ratio=1.425/1000*0.2, trade_at_price="open",upload=False)
                trades = report.get_trades()
                
                report_data = {
                    '因子名稱': factor_name,
                    '策略條件': strategy_type,
                    'PR_Range': pr_range,
                    '限制因子數值正負': pn,
                    '創n期高or低': n_high_or_low,
                    '總交易筆數': len(trades),
                    '策略年化報酬率': report.get_stats()["cagr"],
                    '策略MDD': report.get_stats()["max_drawdown"],
                    '策略sortino(日)': report.get_stats()["daily_sortino"],
                    '個股平均報酬率': trades["return"].mean(),
                    '個股平均MDD': trades["mdd"].mean(),
                    '個股報酬率標準差': trades["return"].std(),
                    '個股平均持有期間(交易日)': trades["period"].mean(),
                    '個股平均處於獲利天數': trades["pdays"].mean(),
                    '個股最大年化複利報酬': (1 + trades["return"].mean()) ** (240 / trades["period"].mean()) - 1,
                }
                return pd.DataFrame([report_data])
            except Exception:
                return None
    
        def generate_conditions(factor_df : pd.DataFrame, strategy_type: str, pr: Tuple[int, int], pn: str, n_high_or_low: int):
            pr_down, pr_up = pr
            conditions = None
            
            if pn == "pos":
                if strategy_type == "qoq":
                    conditions = (
                        (self.get_pr(factor_df / factor_df.shift(1)) > pr_down) & 
                        (self.get_pr(factor_df / factor_df.shift(1)) < pr_up) &
                        (factor_df > 0) & (close > 0)
                    )
                elif strategy_type == "yoy":
                    conditions = (
                        (self.get_pr(factor_df / factor_df.shift(4)) > pr_down) & 
                        (self.get_pr(factor_df / factor_df.shift(4)) < pr_up) &
                        (factor_df > 0) & (close > 0)
                    )
                elif strategy_type == "higest":
                    conditions = (factor_df == factor_df.rolling(n_high_or_low).max()) & (factor_df > 0) & (close > 0)
                elif strategy_type == "factor_market_value_ratio":
                    factor_market_value_ratio = factor_df / market_value
                    conditions = (
                        (self.get_pr(factor_market_value_ratio / factor_market_value_ratio.shift(4)) > pr_down) & 
                        (self.get_pr(factor_market_value_ratio / factor_market_value_ratio.shift(4)) < pr_up) &
                        (factor_df > 0) & (close > 0)
                    )
                elif strategy_type == "lowest":
                    conditions = (factor_df == factor_df.rolling(n_high_or_low).min()) & (factor_df > 0) & (close > 0)
                elif strategy_type == "origin_value":
                    conditions = (self.get_pr(factor_df)>pr_down) & (self.get_pr(factor_df)<pr_up)& (factor_df > 0) & (close > 0)
                    
            elif pn == "neg":
                if strategy_type == "qoq":
                    conditions = (
                        (self.get_pr(factor_df / factor_df.shift(1)) > pr_down) & 
                        (self.get_pr(factor_df / factor_df.shift(1)) < pr_up) &
                        (factor_df < 0) & (close > 0)
                    )
                elif strategy_type == "yoy":
                    conditions = (
                        (self.get_pr(factor_df / factor_df.shift(4)) > pr_down) & 
                        (self.get_pr(factor_df / factor_df.shift(4)) < pr_up) &
                        (factor_df < 0) & (close > 0)
                    )
                elif strategy_type == "higest":
                    conditions = (factor_df == factor_df.rolling(n_high_or_low).max()) & (factor_df < 0) & (close > 0)
                elif strategy_type == "factor_market_value_ratio":
                    factor_market_value_ratio = factor_df / market_value
                    conditions = (
                        (self.get_pr(factor_market_value_ratio / factor_market_value_ratio.shift(4)) > pr_down) & 
                        (self.get_pr(factor_market_value_ratio / factor_market_value_ratio.shift(4)) < pr_up) &
                        (factor_df < 0) & (close > 0)
                    )
                elif strategy_type == "lowest":
                    conditions = (factor_df == factor_df.rolling(n_high_or_low).min()) & (factor_df < 0) & (close > 0)
                elif strategy_type == "origin_value":
                    conditions = (self.get_pr(factor_df)>pr_down) & (self.get_pr(factor_df)<pr_up)& (factor_df < 0) & (close > 0)
                    
            return conditions
    
        def run_factor_analysis(factor_list, strategy_types, pos_neg_options, pr, n_high_or_low):
            factor_report_df_all = pd.DataFrame()
            for factor in factor_list:
                factor_df = self.get(factor)
                factor_name = factor.split(":")[1]
                
                for strategy_type in strategy_types:
                    for pn in pos_neg_options:
                        conditions = generate_conditions(factor_df, strategy_type, pr, pn, n_high_or_low)
                        report_df = calculate_factor_report(conditions, factor_name, strategy_type, pr, pn, n_high_or_low)
                        
                        if report_df is not None:
                            factor_report_df_all = pd.concat([factor_report_df_all, report_df])
            
            return factor_report_df_all
    
        # Run the analysis loop
        strategy_types = ["qoq", "yoy", "higest", "factor_market_value_ratio", "lowest","origin_value"]
        pos_neg_options = ["pos", "neg"]
        factor_report_df_all = run_factor_analysis(factor_list, strategy_types, pos_neg_options, pr, n_high_or_low)
        
        return factor_report_df_all.reset_index(drop=True)



#tg----------------------------------------------------------------------------------------------------------------------


# 在 co_tools_beta.py 的 Codata 類中添加以下方法

    def tg_extract_position_info(self, report):
        """提取持倉資訊
        
        Args:
            report: finlab 回測報告物件
            
        Returns:
            tuple: (進場股票列表, 持有股票列表, 出場股票列表, 最後日期)
        """
        trades = report.get_trades()
        last_date = report.daily_benchmark.index[-1]
        position_info = report.position_info2()
        
        if isinstance(position_info, dict) and 'positions' in position_info:
            positions = position_info['positions']
        else:
            positions = []
        
        enter_stocks = []
        hold_stocks = []
        exit_stocks = []
        
        for position in positions:
            if not isinstance(position, dict):
                continue
                
            asset_id = position.get('assetId', '')
            asset_name = position.get('assetName', '')
            stock_display = f"{asset_id} {asset_name}" if asset_id and asset_name else (asset_id or asset_name)
            
            action_type = position.get('action', {}).get('type', '')
            current_weight = position.get('currentWeight', 0)
            
            # 忽略過去的交易記錄
            if action_type == 'exit_p':
                continue
                
            # 根據動作類型分類
            if action_type == 'entry':
                enter_stocks.append(stock_display)
            elif current_weight != 0:
                hold_stocks.append(stock_display)
                if action_type == 'exit':
                    exit_stocks.append(stock_display)
        
        return enter_stocks, hold_stocks, exit_stocks, last_date
    
    def tg_generate_strategy_message(self, report, strategy_config):
        """生成策略 Telegram 訊息
        
        Args:
            report: finlab 回測報告物件
            strategy_config: 策略配置字典，包含以下鍵值：
                - name: 策略名稱
                - description: 策略說明
                - author: 策略作者
                - direction: 策略多空方向 (多/空)
                - notes: 策略備註 (可選)
                - enter_label: 進場標籤 (可選)
                - hold_label: 持倉標籤 (可選)
                - exit_label: 出場標籤 (可選)
                
        Returns:
            str: 格式化的 Telegram 訊息
        """
        # 提取持倉資訊
        trades = report.get_trades()
        enter_stocks, hold_stocks, exit_stocks, last_date = self.tg_extract_position_info(report)
        
        # 獲取統計數據
        stats_dict = self.display_report_statis(trades)
        
        # 處理策略配置預設值
        direction = strategy_config.get('direction', '多')
        notes = strategy_config.get('notes', '')
        
        # 根據多空方向設定標籤
        if direction == '空':
            enter_label = strategy_config.get('enter_label', '放空股票')
            exit_label = strategy_config.get('exit_label', '回補股票')
        else:
            enter_label = strategy_config.get('enter_label', '買入股票')
            exit_label = strategy_config.get('exit_label', '賣出股票')
        
        hold_label = strategy_config.get('hold_label', '當前持倉')
        
        # 生成訊息
        msg = f"""🔔🔔🔔<b>策略通知</b>
<pre>策略名稱: {strategy_config['name']}
策略說明: {strategy_config['description']}
策略作者: {strategy_config['author']}
策略多空: {direction}
策略備註: {notes}

預定換股日: {last_date}

📈
{enter_label}: {enter_stocks}
{hold_label}: {hold_stocks}
{exit_label}: {exit_stocks}

🔢
總交易筆數: {stats_dict["交易筆數"]}
平均報酬率: {stats_dict["平均報酬率"]}
平均持有天數: {stats_dict["平均持有期間(交易日)"]}
勝率: {stats_dict["勝率"]}
最大年化報酬率(波動調整_泰勒展開): {stats_dict["最大年化報酬率(波動調整_泰勒展開)"]}</pre>"""
 
        
        return msg.strip()
    
    def tg_create_strategy_message_quick(self, report, strategy_name, strategy_description, 
                                    strategy_author, strategy_direction="多", 
                                    strategy_notes="", **kwargs):
        """快速創建策略訊息的便利方法
        
        Args:
            report: finlab 回測報告
            strategy_name: 策略名稱
            strategy_description: 策略說明
            strategy_author: 策略作者
            strategy_direction: 策略方向 (多/空)
            strategy_notes: 策略備註
            **kwargs: 其他自定義標籤
            
        Returns:
            str: 格式化的 Telegram 訊息
        """
        strategy_config = {
            'name': strategy_name,
            'description': strategy_description,
            'author': strategy_author,
            'direction': strategy_direction,
            'notes': strategy_notes,
            **kwargs
        }
        
        return self.tg_generate_strategy_message(report, strategy_config)

    def tg_capture_report_images(self, html_filename=None, 
                                 output_image1=None,
                                 output_image2=None):
        """
        同步版本的 HTML 轉圖片方法
        
        Args:
            html_filename: HTML 檔案名稱 (None 則使用預設)
            output_image1: 第一張截圖檔名 (None 則使用預設)
            output_image2: 第二張截圖檔名 (None 則使用預設)
        """
        import asyncio
        
        # 使用預設值或傳入值
        html_filename = html_filename or self.html_file
        output_image1 = output_image1 or self.image_file_1
        output_image2 = output_image2 or self.image_file_2
        
        if not os.path.exists(html_filename):
            print(f"錯誤: HTML 檔案 '{html_filename}' 不存在")
            return False
        
        try:
            asyncio.run(self.tg_capture_html_to_image(html_filename, output_image1, output_image2))
            return True
        except Exception as e:
            print(f"截圖失敗: {e}")
            return False

    
    async def tg_capture_html_to_image(self, html_file_path, output_image_path1, output_image_path2, 
                                       browser_type='chromium', full_page=True, 
                                       viewport_width=1920, viewport_height=1080):
        """
        將本地 HTML 檔案轉換為圖片
        
        Args:
            html_file_path: HTML 檔案路徑
            output_image_path1: 第一張截圖路徑（原始頁面）
            output_image_path2: 第二張截圖路徑（點選後頁面）
            browser_type: 瀏覽器類型 ('chromium', 'firefox', 'webkit')
            full_page: 是否截取完整頁面
            viewport_width: 視窗寬度
            viewport_height: 視窗高度
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # 啟動瀏覽器
            if browser_type == 'chromium':
                browser = await p.chromium.launch()
            elif browser_type == 'firefox':
                browser = await p.firefox.launch()
            elif browser_type == 'webkit':
                browser = await p.webkit.launch()
            else:
                raise ValueError("不支援的瀏覽器類型")
            
            # 轉換為絕對路徑
            abs_html_file_path = os.path.abspath(html_file_path)
            file_url = f"file:///{abs_html_file_path.replace(os.sep, '/')}"
            print(f"正在開啟: {file_url}")
            
            page = await browser.new_page()
            await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
            
            try:
                # 載入頁面
                await page.goto(file_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # 第一次截圖：原始頁面
                print(f"正在擷取原始頁面到: {output_image_path1}")
                await page.screenshot(path=output_image_path1, full_page=full_page)
                
                # 尋找選股按鈕 - 使用多種選擇器嘗試
                selectors = [
                    'a:has-text("選股")',  # 簡單文字選擇器
                    'a[role="tab"]:has-text("選股")',  # 帶role屬性
                    '.tab:has-text("選股")',  # class選擇器
                    'a.tab-active:has-text("選股")',  # 原始選擇器
                ]
                
                element_found = False
                for selector in selectors:
                    try:
                        print(f"嘗試選擇器: {selector}")
                        await page.wait_for_selector(selector, timeout=5000)
                        print(f"找到選股按鈕，正在點選...")
                        await page.click(selector)
                        element_found = True
                        break
                    except Exception as e:
                        print(f"選擇器 {selector} 失敗: {e}")
                        continue
                
                if not element_found:
                    print("無法找到選股按鈕，列出所有可能的選項...")
                    # 列出所有包含"選股"的元素
                    elements = await page.query_selector_all('*')
                    for element in elements[:20]:  # 只檢查前20個元素避免太多輸出
                        text = await element.text_content()
                        if text and "選股" in text:
                            tag_name = await element.evaluate('el => el.tagName')
                            class_name = await element.get_attribute('class')
                            print(f"找到包含'選股'的元素: {tag_name}, class: {class_name}, text: {text}")
                    
                    # 嘗試直接點擊任何包含"選股"文字的元素
                    try:
                        await page.click('text=選股')
                        element_found = True
                        print("使用 text=選股 成功點擊")
                    except:
                        print("所有方法都失敗")
                
                if element_found:
                    await page.wait_for_timeout(2000)  # 等待頁面更新
                    
                    # 第二次截圖：點選後
                    print(f"正在擷取選股後頁面到: {output_image_path2}")
                    await page.screenshot(path=output_image_path2, full_page=full_page)
                    print("擷取成功！")
                else:
                    print("無法點擊選股按鈕，只保存原始截圖")
                    
            except Exception as e:
                print(f"發生錯誤: {e}")
                # 除錯：印出頁面內容
                try:
                    html_content = await page.content()
                    print("頁面 HTML 內容片段：", html_content[:500])
                except:
                    print("無法取得頁面內容")
                    
            finally:
                await browser.close()

    def tg_send_photo(self, bot_token, channel_ids, photo_path, caption=""):
        """
        發送圖片到 Telegram
        
        Args:
            bot_token: Bot token
            channel_ids: 頻道ID列表
            photo_path: 圖片路徑
            caption: 圖片說明
            
        Returns:
            dict: 發送結果
        """
        if not os.path.exists(photo_path):
            print(f"圖片檔案不存在: {photo_path}")
            return {}
            
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        results = {}
        
        for cid in channel_ids:
            try:
                with open(photo_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': cid, 'caption': caption}
                    resp = requests.post(url, files=files, data=data)
                    results[cid] = resp.status_code
                    
                    if resp.status_code != 200:
                        print(f"發送圖片至 {cid} 失敗: {resp.text}")
                    else:
                        print(f"圖片成功發送至 {cid}")
                        
            except Exception as e:
                print(f"發送圖片至 {cid} 發生錯誤: {e}")
                results[cid] = 0
                
        return results

    def tg_clean_files(self, clean_html=True, clean_images=True):
        """
        清理產生的檔案
        
        Args:
            clean_html: 是否刪除 HTML 檔案
            clean_images: 是否刪除圖片檔案
        """
        files_to_clean = []
        
        if clean_html and os.path.exists(self.html_file):
            files_to_clean.append(self.html_file)
            
        if clean_images:
            if os.path.exists(self.image_file_1):
                files_to_clean.append(self.image_file_1)
            if os.path.exists(self.image_file_2):
                files_to_clean.append(self.image_file_2)
        
        cleaned_files = []
        for file_path in files_to_clean:
            try:
                os.remove(file_path)
                cleaned_files.append(file_path)
                print(f"已刪除檔案: {file_path}")
            except Exception as e:
                print(f"刪除檔案 {file_path} 失敗: {e}")
                
        return cleaned_files

    def tg_generate_and_send_complete(self, report, strategy_config, bot_token, channel_ids, 
                                      send_images=True, clean_files=True, 
                                      clean_html=True, clean_images=True):
        """
        完整的策略推送流程：生成訊息 -> 截圖 -> 發送 -> 清理
        
        Args:
            report: finlab 回測報告
            strategy_config: 策略配置
            bot_token: Bot token
            channel_ids: 頻道ID列表
            send_images: 是否發送圖片
            clean_files: 是否清理檔案
            clean_html: 是否刪除 HTML 檔案
            clean_images: 是否刪除圖片檔案
            
        Returns:
            dict: 執行結果
        """
        results = {'message_sent': False, 'images_sent': [], 'files_cleaned': []}
        
        try:
            # 1. 生成文字訊息並發送
            msg = self.tg_generate_strategy_message(report, strategy_config)
            
            # 發送文字訊息
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            for cid in channel_ids:
                payload = {"chat_id": cid, "text": msg, "parse_mode": "HTML"}
                resp = requests.post(url, json=payload)
                if resp.status_code == 200:
                    results['message_sent'] = True
                    print(f"文字訊息成功發送至 {cid}")
                else:
                    print(f"文字訊息發送至 {cid} 失敗: {resp.text}")
            
            # 2. 如果需要發送圖片
            if send_images:
                # 生成截圖
                if self.tg_capture_report_images():
                    # 發送第一張圖片
                    if os.path.exists(self.image_file_1):
                        result1 = self.tg_send_photo(bot_token, channel_ids, self.image_file_1, "策略報告 - 原始頁面")
                        if any(status == 200 for status in result1.values()):
                            results['images_sent'].append(self.image_file_1)
                    
                    # 發送第二張圖片
                    if os.path.exists(self.image_file_2):
                        result2 = self.tg_send_photo(bot_token, channel_ids, self.image_file_2, "策略報告 - 選股頁面")
                        if any(status == 200 for status in result2.values()):
                            results['images_sent'].append(self.image_file_2)
                else:
                    print("截圖失敗，跳過圖片發送")
            
            # 3. 清理檔案
            if clean_files:
                cleaned = self.tg_clean_files(clean_html, clean_images)
                results['files_cleaned'] = cleaned
                
        except Exception as e:
            print(f"完整推送流程發生錯誤: {e}")
            
        return results


#CatBoost特徵重要性分析區----------------------------------------------------------------------------------------------------------------

    def _handle_dataframe(self, df, target_col):
        """處理不同類型的 DataFrame，保持原始格式的效能優勢"""
        # 檢查是否為 polars DataFrame
        if hasattr(df, 'select') and hasattr(df, 'drop'):
            print("⚡ 使用 Polars DataFrame (高效能模式)")
            
            # 使用 Polars 的高效操作
            feature_cols = [col for col in df.columns if col != target_col]
            X = df.select(feature_cols).to_numpy()  # 直接轉為 numpy，避免 pandas 開銷
            y = df.select(target_col).to_numpy().flatten()
            feature_names = feature_cols
            
            return X, y, feature_names
        
        # pandas DataFrame
        elif isinstance(df, pd.DataFrame):
            print("📊 使用 Pandas DataFrame")
            X = df.drop(columns=[target_col])
            y = df[target_col]
            feature_names = X.columns.tolist()
            
            return X.values, y.values, feature_names
        
        else:
            raise ValueError("支援的格式: pandas.DataFrame 或 polars.DataFrame")
    
    def analyze_feature_importance(self, df, target_col='target', model_type='regressor', 
                                 loss_type='RMSE', use_gpu=True, iterations=200, 
                                 depth=6, learning_rate=0.1, l2_leaf_reg=3, top_n=None):
        """
        分析特徵重要性並繪製美化圖表
        
        參數:
        df: DataFrame (pandas.DataFrame 或 polars.DataFrame)
        target_col: 目標變量
        model_type: 'regressor', 'classifier'
        loss_type: 'RMSE', 'MAE', 'both'
        use_gpu: 是否使用 GPU 加速
        l2_leaf_reg: L2 正則化參數 (1-10)
        top_n: 顯示前 N 個重要特徵 (None = 顯示全部)
        """
        # 高效處理不同格式的 DataFrame
        X, y, feature_names = self._handle_dataframe(df, target_col)
        
        # 如果沒有指定 top_n，顯示全部特徵
        if top_n is None:
            top_n = len(feature_names)
        
        # 基礎參數 - MAE 不支援 GPU，自動調整
        gpu_compatible = use_gpu and (loss_type != 'MAE' and loss_type != 'both')
        
        base_params = {
            'iterations': iterations,
            'depth': depth,
            'learning_rate': learning_rate,
            'l2_leaf_reg': l2_leaf_reg,
            'task_type': 'GPU' if gpu_compatible else 'CPU',
            'verbose': 0
        }
        
        # 顯示 GPU/CPU 使用狀況
        if loss_type == 'MAE' and use_gpu:
            print("⚠️  MAE 不支援 GPU，自動切換為 CPU 模式")
        elif loss_type == 'both' and use_gpu:
            print("⚠️  MAE 模型將使用 CPU，RMSE 模型使用 GPU")
        
        # 顯示運算資訊
        device_info = "🚀 GPU" if use_gpu else "🖥️  CPU"
        print(f"使用 {device_info} 進行訓練 ")
        print(f"📈 數據維度: {X.shape[0]} 樣本, {X.shape[1]} 特徵")
        print(f"📋 將顯示 {top_n} 個特徵重要性")
        
        if model_type == 'regressor':
            if loss_type == 'both':
                return self._compare_loss_functions(X, y, feature_names, base_params, top_n)
            else:
                return self._single_model_analysis(X, y, feature_names, base_params, loss_type, model_type, top_n)
        else:  # classifier
            print(f"📊 將數值型目標轉換為二元分類：正值→1(上漲), 負值/零→0(下跌)")
            return self._single_model_analysis(X, y, feature_names, base_params, loss_type, model_type, top_n)
    
    def _single_model_analysis(self, X, y, feature_names, base_params, loss_type, model_type, top_n):
        """單一模型分析"""
        if model_type == 'regressor':
            if loss_type not in ['RMSE', 'MAE']:
                raise ValueError("regressor 的 loss_type 必須是 'RMSE', 'MAE', 或 'both'")
            
            params = base_params.copy()
            params['loss_function'] = loss_type
            model = CatBoostRegressor(**params)
            model.fit(X, y)
            model_name = f"CatBoost Regressor ({loss_type})"
            
        else:  # classifier
            # 數值型目標變量轉換為二元分類
            y_class = (y > 0).astype(int)
            
            # 顯示轉換統計（使用 numpy 高效計算）
            unique, counts = np.unique(y_class, return_counts=True)
            class_counts = dict(zip(unique, counts))
            total = len(y_class)
            
            print(f"   類別 0 (下跌): {class_counts.get(0, 0)} 樣本")
            print(f"   類別 1 (上漲): {class_counts.get(1, 0)} 樣本")
            print(f"   上漲比例: {class_counts.get(1, 0) / total * 100:.1f}%")
            
            model = CatBoostClassifier(**base_params)
            model.fit(X, y_class)
            model_name = "CatBoost Classifier (Binary)"
        
        print("✅ 訓練完成")
        
        # 特徵重要性 - 取得所有特徵
        importance = model.get_feature_importance()
        full_importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # 圖表顯示用 (限制顯示數量，避免圖表過於擁擠)
        plot_top_n = min(top_n, 20)  # 圖表最多顯示20個
        plot_df = full_importance_df.head(plot_top_n)
        
        # 美化圖表
        fig, ax = plt.subplots(figsize=(12, max(8, plot_top_n * 0.4)))
        
        # 顏色配置
        colors = plt.cm.viridis(np.linspace(0, 1, len(plot_df)))
        
        # 水平條形圖
        bars = ax.barh(range(len(plot_df)), plot_df['importance'], 
                       color=colors, alpha=0.8, edgecolor='white', linewidth=0.8)
        
        # 設定 y 軸標籤
        ax.set_yticks(range(len(plot_df)))
        ax.set_yticklabels(plot_df['feature'], fontsize=11)
        
        # 添加數值標籤
        for i, (bar, importance_val) in enumerate(zip(bars, plot_df['importance'])):
            width = bar.get_width()
            ax.text(width + max(plot_df['importance']) * 0.01, 
                    bar.get_y() + bar.get_height()/2, 
                    f'{importance_val:.2f}',
                    ha='left', va='center', fontweight='bold', fontsize=10)
        
        # 美化標題和標籤
        ax.set_xlabel('Feature Importance', fontsize=14, fontweight='bold')
        title_text = f'{model_name} Feature Importance'
        if len(full_importance_df) != plot_top_n:
            title_text += f' (Top {plot_top_n} of {len(full_importance_df)})'
        ax.set_title(title_text, fontsize=16, fontweight='bold', pad=20)
        
        # 反轉 y 軸順序 (重要性高的在上)
        ax.invert_yaxis()
        
        # 添加網格
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # 設定 x 軸範圍
        ax.set_xlim(0, max(plot_df['importance']) * 1.15)
        
        # 美化邊框
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # 調整佈局
        plt.tight_layout()
        
        # 添加背景色漸變效果
        ax.set_facecolor('#f8f9fa')
        
        plt.show()
        
        # 返回完整的重要性排序結果 (所有特徵)
        return full_importance_df
    
    def _compare_loss_functions(self, X, y, feature_names, base_params, top_n):
        """比較 RMSE 和 MAE 的特徵重要性"""
        print("🔄 比較 RMSE 和 MAE 的特徵重要性差異...")
        
        # 訓練 RMSE 模型 (可用 GPU)
        rmse_params = base_params.copy()
        rmse_params['loss_function'] = 'RMSE'
        # RMSE 保持原始 GPU 設定
        rmse_model = CatBoostRegressor(**rmse_params)
        rmse_model.fit(X, y)
        
        # 訓練 MAE 模型 (強制 CPU)
        mae_params = base_params.copy()
        mae_params['loss_function'] = 'MAE'
        mae_params['task_type'] = 'CPU'  # MAE 強制使用 CPU
        mae_model = CatBoostRegressor(**mae_params)
        mae_model.fit(X, y)
        
        print("✅ 兩個模型訓練完成")
        
        # 獲取特徵重要性
        rmse_importance = rmse_model.get_feature_importance()
        mae_importance = mae_model.get_feature_importance()
        
        # 使用 numpy 高效操作
        comparison_data = {
            'feature': feature_names,
            'RMSE_importance': rmse_importance,
            'MAE_importance': mae_importance,
            'importance_diff': rmse_importance - mae_importance
        }
        
        # 完整的比較結果
        full_comparison = pd.DataFrame(comparison_data).sort_values('RMSE_importance', ascending=False)
        
        # 繪製比較圖 (限制顯示數量)
        plot_top_n = min(top_n, 15)  # 比較圖最多顯示15個
        plot_comparison = full_comparison.head(plot_top_n)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, max(8, plot_top_n * 0.4)))
        
        # RMSE vs MAE 比較
        x = np.arange(len(plot_comparison))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, plot_comparison['RMSE_importance'], width, 
                        label='RMSE', alpha=0.8, color='#2E86AB')
        bars2 = ax1.bar(x + width/2, plot_comparison['MAE_importance'], width, 
                        label='MAE', alpha=0.8, color='#A23B72')
        
        # 添加數值標籤
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        ax1.set_xlabel('Features', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Importance', fontweight='bold', fontsize=12)
        title_text = 'RMSE vs MAE Feature Importance Comparison'
        if len(full_comparison) != plot_top_n:
            title_text += f' (Top {plot_top_n} of {len(full_comparison)})'
        ax1.set_title(title_text, fontweight='bold', fontsize=14)
        ax1.set_xticks(x)
        ax1.set_xticklabels(plot_comparison['feature'], rotation=45, ha='right')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_facecolor('#f8f9fa')
        
        # 重要性差異圖
        diff_data = plot_comparison.sort_values('importance_diff')
        colors = ['#FF6B6B' if x < 0 else '#4ECDC4' for x in diff_data['importance_diff']]
        
        bars3 = ax2.barh(range(len(diff_data)), diff_data['importance_diff'], 
                         color=colors, alpha=0.8, edgecolor='white', linewidth=0.8)
        
        # 添加數值標籤
        for i, (bar, diff) in enumerate(zip(bars3, diff_data['importance_diff'])):
            width = bar.get_width()
            ax2.text(width + (max(abs(diff_data['importance_diff'])) * 0.02 * (1 if width >= 0 else -1)), 
                    bar.get_y() + bar.get_height()/2, 
                    f'{diff:.2f}',
                    ha='left' if width >= 0 else 'right', va='center', 
                    fontweight='bold', fontsize=10)
        
        ax2.set_yticks(range(len(diff_data)))
        ax2.set_yticklabels(diff_data['feature'], fontsize=11)
        ax2.set_xlabel('Importance Difference (RMSE - MAE)', fontweight='bold', fontsize=12)
        ax2.set_title('Feature Importance Difference', fontweight='bold', fontsize=14)
        ax2.axvline(x=0, color='black', linestyle='--', alpha=0.7, linewidth=2)
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.set_facecolor('#f8f9fa')
        ax2.invert_yaxis()
        
        # 美化邊框
        for ax in [ax1, ax2]:
            for spine in ax.spines.values():
                spine.set_visible(False)
        
        plt.tight_layout()
        plt.show()
        
        # 返回完整的比較結果 (所有特徵)
        return full_comparison
    
#高效資料合併區----------------------------------------------------------------------------------------------------------------

    def combine(self, features: Dict[str, pd.DataFrame], resample=None, sample_filter=None, output_format="pandas", precision="f32", **kwargs):
        """
        合併多個特徵資料框並支援精度壓縮和記憶體回收
        
        參數:
            features: 包含特徵資料框的字典
            resample: 重採樣頻率 (如 '1D', '1H' 等) 或可迭代的索引
            sample_filter: 用於過濾樣本的資料框
            output_format: 輸出格式，'pandas' 或 'polars'
            precision: 數值精度，'f16', 'f32'(默認) 或 'f64'
            **kwargs: 傳遞給 resample 方法的參數
            
        返回:
            合併後的資料框，格式根據 output_format 參數決定
        """
        from collections.abc import Iterable
        import gc
        
        # 檢查參數
        if output_format not in ["pandas", "polars"]:
            raise ValueError("output_format 必須是 'pandas' 或 'polars'")
        
        if precision not in ["f16", "f32", "f64"]:
            raise ValueError("precision 必須是 'f16', 'f32' 或 'f64'")
            
        # 如果選擇 polars 格式，確保已安裝 polars
        if output_format == "polars":
            try:
                import polars as pl
            except ImportError:
                raise ImportError("要使用 polars 輸出，請先安裝 polars 庫: pip install polars")
        
        # 內部重採樣函數
        def resampler(df, resample_param, **inner_kwargs):
            if resample_param is None:
                return df
            elif isinstance(resample_param, Iterable) and not isinstance(resample_param, str):
                # 如果是可迭代對象（如列表、索引），使用 reindex
                return df.reindex(resample_param, method='ffill')
            else:
                # 如果是字串（如 '1D', '1H'），使用 resample
                return df.resample(resample_param, closed='right', label='right', **inner_kwargs).last()
        
        if len(features) == 0:
            return pd.DataFrame() if output_format == "pandas" else pl.DataFrame()
        
        unstacked = {}
        union_index = None
        union_columns = None
        concats = []
        
        # 處理特徵資料框
        for name, df in features.items():
            # 處理可調用對象
            if callable(df):
                df = df()
                
            if isinstance(df.index, pd.MultiIndex):
                concats.append(df)
            else:
                # 檢查是否為 FinlabDataFrame 類型
                if hasattr(df, 'index_str_to_date'):
                    df = df.index_str_to_date()
                    
                # 應用重採樣
                udf = resampler(df, resample, **kwargs)
                unstacked[name] = udf
                
                # 計算聯集索引和交集欄位
                if union_index is not None:
                    union_index = union_index.union(udf.index)
                else:
                    union_index = udf.index
                    
                if union_columns is not None:
                    union_columns = union_columns.intersection(udf.columns)
                else:
                    union_columns = udf.columns
        
        final_index = None
        
        # 處理 unstacked 資料
        for name, udf in unstacked.items():
            udf = udf\
                .reindex(index=union_index, columns=union_columns)\
                .ffill()\
                .T\
                .unstack()
            unstacked[name] = udf.values
            
            if final_index is None:
                final_index = udf.index
        
        # 處理已有 MultiIndex 的 DataFrame
        for i, c in enumerate(concats):
            c.index = c.index.set_names(['datetime', 'instrument'])
            if union_index is not None:
                concats[i] = c[c.index.get_level_values('datetime').isin(union_index)]
        
        # 合併所有資料
        if unstacked:
            unstack_df = pd.DataFrame(unstacked, index=final_index)
            unstack_df.index = unstack_df.index.set_names(['datetime', 'instrument'])
            concats.append(unstack_df)
        
        ret = pd.concat(concats, axis=1)
        ret.sort_index(inplace=True)
        
        # 應用樣本過濾器
        if sample_filter is not None:
            if hasattr(sample_filter, 'index_str_to_date'):
                sample_filter = sample_filter.index_str_to_date()
                
            usf = resampler(sample_filter, resample, **kwargs)
            
            if union_index is not None and union_columns is not None:
                usf = usf.reindex(index=union_index, columns=union_columns)
                
            usf = usf.ffill()\
               .T\
               .unstack()\
               .reindex(ret.index)\
               .astype(bool).fillna(False)
               
            ret = ret.loc[usf.values]
        
        # 精度壓縮
        if precision == "f16":
            for col in ret.select_dtypes(include=['float64', 'float32']).columns:
                ret[col] = ret[col].astype(np.float16)
        elif precision == "f32":
            for col in ret.select_dtypes(include=['float64']).columns:
                ret[col] = ret[col].astype(np.float32)
        
        # 如果要求 polars 輸出，則轉換為 polars DataFrame
        if output_format == "polars":
            # 處理 MultiIndex
            if isinstance(ret.index, pd.MultiIndex):
                df_reset = ret.reset_index()
                pl_df = pl.from_pandas(df_reset)
            else:
                pl_df = pl.from_pandas(ret)
            
            # 在 Polars 中應用精度壓縮
            if precision == "f16":
                # Polars 沒有 float16，使用 float32
                for col in pl_df.columns:
                    if pl_df[col].dtype in [pl.Float64, pl.Float32]:
                        pl_df = pl_df.with_columns(pl_df[col].cast(pl.Float32))
            elif precision == "f32":
                for col in pl_df.columns:
                    if pl_df[col].dtype == pl.Float64:
                        pl_df = pl_df.with_columns(pl_df[col].cast(pl.Float32))
            
            # 統一記憶體清理
            try:
                del ret, df_reset, unstacked, concats, unstack_df
            except:
                pass
            gc.collect()
            
            return pl_df
        
        # 統一記憶體清理
        try:
            del unstacked, concats, unstack_df
        except:
            pass
        gc.collect()
        
        return ret

 #一般分析區------------------------------------------------------------------------------------------------

    def create_factor_data(self, factor, adj_close, days=[1,2], event=None):
        """
        原始 finlab 的 create_factor_data 函數
        """
        factor = {'factor':factor} if isinstance(factor, pd.DataFrame) else factor

        ref = next(iter(factor.values())) if event is None else event
        ref = ref[~ref.index.isna()]

        sids = adj_close.columns.intersection(ref.columns)
        dates = adj_close.index.intersection(
            FinlabDataFrame.to_business_day(ref.index))
        
        ret = {}
        for name, f in factor.items():
            reashaped_f = f.reindex(dates, method='ffill').reindex(columns=sids)
            ret[f'{name}_factor'] = reashaped_f.unstack().values
            ret[f'{name}_factor_quantile'] = (reashaped_f.rank(axis=1, pct=True) // 0.2).unstack().values

        total_index = None
        for d in days:
            temp = (adj_close.shift(-d-1) / adj_close.shift(-1) - 1)\
                .reindex(index=dates, method='ffill').reindex(columns=sids)\
                .unstack()
            
            ret[f"{d}D"] = temp.values
            total_index = temp.index

        if event is not None:
            event = event[event.index.notna()]
            reshaped_event = event.reindex(index=dates, method='ffill').reindex(columns=sids)
            ret['event'] = reshaped_event.unstack().values


        ret = pd.DataFrame(ret, index=total_index.swaplevel(0, 1))\
            .replace([-np.inf, np.inf], np.nan)\
            .dropna()

        if 'event' in ret:
            ret = ret[ret['event'] == True]
            ret.drop(columns=['event'], inplace=True)

        ret.index.names = ['date', 'asset']
        return ret

    def co_event_analysis(self, buy:"dataframe"):
        """
        用finlab原始程式碼改的,用以分析事件發生前後之報酬率變化
        注意:
        
        1.記憶體量不夠可能會錯誤
        2.cross over
        
        參考:
        https://www.finlab.tw/event-study-usage/
        https://doc.finlab.tw/reference/tools/
        """
        adj_close = self.get('etl:adj_close')
        factor_data = self.create_factor_data(buy, adj_close, event=buy)
        buy_time_distribution = pd.DataFrame(buy.sum(axis=1)).reset_index() 
        buy_time_distribution.rename(columns = {0:'number of times'}, inplace = True)
        buy_time_distribution
        fig1 = px.area(buy_time_distribution, x="date", y="number of times",color="number of times",
                     title="事件發生次數與日期分布")
        fig1.show()
        
        #用加權指數當成benchmark,排除加權指數時間變因
        benchmark = self.get('benchmark_return:發行量加權股價報酬指數')
        benchmark_pct = benchmark.reindex(adj_close.index, method='ffill').pct_change()
        stock_pct = adj_close.pct_change()
        def get_period(df, date, sample):
            i = df.index.get_loc(date)
            return df.iloc[i+sample[0]: i+sample[1]].values
        
        #轉換成,獨立事件與時間報酬率
        ret = []
        sample_period=(-40, -20) #
        estimation_period=(-15, 30)# 觀察事件前15日與後30日變化
        for date, sid in tqdm.tqdm(factor_data.index):
        
            X1, Y1 = get_period(benchmark_pct, date, sample_period)[:,0], \
                get_period(stock_pct[sid], date, sample_period)
            X2, Y2 = get_period(benchmark_pct, date, estimation_period)[:,0], \
                get_period(stock_pct[sid], date, estimation_period)
        
            # Run CAPM
            cov_matrix = np.cov(Y1, X1)
            beta = cov_matrix[0, 1] / cov_matrix[1, 1]
            AR = np.array(Y2) - beta * X2
            ret.append(AR)
        #計算事件發生日前後的日報酬率變化\
        ret = pd.DataFrame(ret, columns=range(*estimation_period))
        
        # range_estimation_period_begin =  estimation_period[0]
        # range_estimation_period_end = len(ret[0])
        # if range_estimation_period_end>30:
        #     range_estimation_period_end =30
        # ret = pd.DataFrame(ret, columns=range(range_estimation_period_begin,range_estimation_period_end))
            
        ret_df = pd.DataFrame(ret.mul(100).mean()).reset_index() 
        ret_df_re = ret_df.rename(columns = {"index":"days",0:"return"})
        ret_df_re
        fig2 = px.bar(ret_df_re, x="days", y="return",color="return",
                     title="事件發生日前後的日報酬率變化")
        # fig.add_trace(go.Scatter(
        #     x=list(ret_df_re["days"]),
        #     y=list(ret_df_re["return"]),
        #     xperiod="M1",
        #     xperiodalignment="middle",
        #     hovertemplate="%{y}%{_xother}"
        # ))
        fig2.show()
        
        #計算累計報酬率,並將事件發生日作基準點
        accum_ret_df = pd.DataFrame(ret.mul(100).cumsum(axis=1).mean()).reset_index() 
        accum_ret_df_re = accum_ret_df.rename(columns = {"index":"days",0:"return"})
        accum_ret_df_re["return_accumulated"] = accum_ret_df_re["return"] -accum_ret_df_re.at[15,"return"]
        std = ret.mul(100).cumsum(axis=1).std() * 0.1
        accum_ret_df_re
        fig3 = px.line(accum_ret_df_re, x="days", y="return_accumulated",
                 title="累計報酬率,以事件發生日作基準點")
        
        fig3.show()
        return accum_ret_df_re   


