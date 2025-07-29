import wget
import zipfile
import os
import urllib.request

class Config:
    # 统一放在用户目录下
    RUNTIME_PROVISION_DIR = os.path.join(os.path.expanduser('~'), 'runtime_provisioner')

def get_chrome_109_exe() -> str:
    chrome_exe = os.path.join(Config.RUNTIME_PROVISION_DIR, 'Chrome109', 'chrome.exe')
    if os.path.exists(chrome_exe):
        return chrome_exe
    # 设置User-Agent避免403错误
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')]
    urllib.request.install_opener(opener)
    
    url = 'https://pub-d7ccffce644a4b24b641510c3a9e6cfb.r2.dev/Chrome109.zip'
    wget.download(url, os.path.join(Config.RUNTIME_PROVISION_DIR, 'Chrome109.zip'))
    # 解压
    with zipfile.ZipFile(os.path.join(Config.RUNTIME_PROVISION_DIR, 'Chrome109.zip'), 'r') as zip_ref:
        zip_ref.extractall(Config.RUNTIME_PROVISION_DIR)

    return chrome_exe

os.makedirs(Config.RUNTIME_PROVISION_DIR, exist_ok=True)
