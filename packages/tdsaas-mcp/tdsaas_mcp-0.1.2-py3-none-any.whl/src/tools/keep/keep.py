import hmac
import base64
import os
import time
import requests
from typing import Dict, Any

class Keep:

    def __init__(self):
        self.secret = os.getenv("SECRET", "")
        self.host = os.getenv("HOST", "")
        self.get_all_keep_user_list_api_url = f"{self.host}/api/operation/get_all_keep_user_list.php"
        self.get_to_be_renew_user_list_api_url = f"{self.host}/api/operation/get_to_be_renew_user_list.php"
        self.get_user_detail_api_url = f"{self.host}/api/operation/get_user_detail.php"
    
    def _generate_sign(self, sign_str: str) -> str:
        # 构建签名字符串
        sign_str = f"{sign_str}"
        
        # 使用HMAC-SHA256计算签名
        hmac_obj = hmac.new(
            self.secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            'sha256'
        )
        
        # Base64编码
        return base64.b64encode(hmac_obj.digest()).decode('utf-8')

    def get_all_keep_user_list(self):# 生成签名
        t = time.time()

        sign = self._generate_sign(str(t)+'|'+self.get_all_keep_user_list_api_url)
        
        # 准备请求数据
        data = {
            "t": t,
            "sign": sign
        }
        
        # 发送POST请求
        response = requests.post(self.get_all_keep_user_list_api_url, data=data)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回JSON响应
        return response.json()

    def get_to_be_renew_user_list(self, days: int):
        t = time.time()

        sign = self._generate_sign(str(days)+'|'+str(t)+'|'+self.get_to_be_renew_user_list_api_url)
        
        # 准备请求数据
        data = {
            "days": days,
            "t": t,
            "sign": sign
        }
        
        # 发送POST请求
        response = requests.post(self.get_to_be_renew_user_list_api_url, data=data)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回JSON响应
        return response.json()

    def get_user_detail(self, corp_name: str):
        t = time.time()

        sign = self._generate_sign(corp_name+'|'+str(t)+'|'+self.get_user_detail_api_url)
        
        # 准备请求数据
        data = {
            "corp_name": corp_name,
            "t": t,
            "sign": sign
        }
        
        # 发送POST请求
        response = requests.post(self.get_user_detail_api_url, data=data)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回JSON响应
        return response.json()