"""
tatools01

An python parametters library.
"""

__version__ = "1.0.3" # Nhớ update cả Readme.md

__author__ = "Nguyễn Tuấn Anh - nt.anh.fai@gmail.com"
__credits__ = "MIT License"
__console__ = "tact"
import os
import sys
import argparse
import json
 
   
from . import ParamsBase
from tatools01.Thoi_gian.taTimers import MultiTimer


__help__ = """
"""

def console_main():
    print(
        """
Running: 
1. tact
        """
    )
    
    print("""
from tatools01.ParamsBase import TactParameters 
AppName = 'My_Project_Name'

class Params_01(TactParameters):
    def __init__(self):
        super().__init__(ModuleName="Module 01", params_dir='./')
        self.HD = ["Chương trình này nhằm xây dựng tham số cho các chương trình khác"]
        self.test1 = "123"
        self.in_var = 1
        self.myList = [1, 2, 3, 4, 5]
        self.myDict = {"key1": "value1", "key2": "value2"}
        self.Multi_types_param = {
            "int": 42,
            "float": 3.14,
            "str": "Hello, World!",
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }
        self.load_then_save_to_yaml(file_path=f"{AppName}.yml")

# Tạo instance đầu tiên
mPs1 = Params_01()

class Params_02(TactParameters):
    def __init__(self):
        super().__init__(ModuleName="Module 02", params_dir='./')
        self.HD = ["Chương trình này nhằm xây dựng tham số cho các chương trình khác"]
        self.test1 = "456"  # Giá trị khác để test
        self.test2 = "New param"  # Thêm param mới
        self.in_var = 2
        self.load_then_save_to_yaml(file_path=f"{AppName}.yml")

# Tạo instance thứ hai
mPs2 = Params_02()

# Test logging
mPs1.mlog("hello from module 01")
mPs2.mlog("hello from module 02")

print("Module 01 test1:", mPs1.test1)
print("Module 02 test1:", mPs2.test1)
print("Module 02 test2:", mPs2.test2)

# Test đọc lại từ file
print("\n--- Test đọc lại từ file ---")
test_params1 = Params_01()
test_params2 = Params_02()
print("Module 01 test1 (from file):", test_params1.test1)
print("Module 02 test1 (from file):", test_params2.test1)
print("Module 02 test2 (from file):", test_params2.test2)       
          """)

