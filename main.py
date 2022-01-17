# https://mmzztt.com/photo/
from email import header
import json
import logging
import os
import random
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(filename)s %(lineno)d %(levelname)s %(message)s", datefmt='%Y-%m-%d  %H:%M:%S %a')

def save_curr_data(conf_path='./conf.json',curr_url=None,curr_img_url=None):
    conf = {
        "currUrl":curr_url,
        "currImgUrl":curr_img_url,
    }
    with open(conf_path, 'w',encoding ='utf8') as f:
        json.dump(conf,f,ensure_ascii = False)

def read_curr_data_curr_url(conf_path='./conf.json'):
    with open(conf_path, 'r',encoding ='utf8') as f:
        conf = json.loads(f.read())
        return conf['currUrl'] 

def save_img_to_file(img_url, dic_path, dic_name):
    '''
    保存图片到指定位置
    '''
    if not os.path.exists(dic_path):
        os.mkdir(dic_path)
    dic_name = dic_name.replace('/','_').replace('\\','_').replace(' ','')
    p = os.path.join(dic_path, dic_name)
    if not os.path.exists(p):
        os.mkdir(p)
    file_name = img_url[str(img_url).rindex('/') + 1:]
    file_name = file_name.replace('/','_').replace('\\','_').replace(' ','')
    file_path = os.path.join(p, file_name)
    if os.path.exists(file_path):
        return True
    r = requests.get(url=img_url, headers={
        "referer": 'https://mmzztt.com/',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    })
    with open(file_path, 'wb') as f:
        if len(r.content) > 10:
            f.write(r.content)
            return True
        else:
            return False


def create_driver():
    '''
    创建驱动
    '''
    options = webdriver.FirefoxOptions()
    # options.set_headless(True)
    options.add_argument("--headless")  # 设置火狐为headless无界面模式
    options.add_argument("--disable-gpu")
    return webdriver.Firefox(options=options)


def find_imgs(driver: webdriver):
    '''
    获取详情页所有图片
    '''
    name = ''
    nowhandle = driver.current_window_handle
    allhandles = driver.window_handles
    # 目标页和搜索栏目页切换下
    for handle in allhandles:
        if handle != nowhandle:
            driver.switch_to.window(handle)
            name = driver.find_element(
                By.CSS_SELECTOR, 'h1.uk-article-title.uk-text-truncate').text
            temp_name: str = name
            while(True):
                img = driver.find_element(
                    By.CSS_SELECTOR, 'figure.uk-inline>img')
                next = driver.find_element(
                    By.CSS_SELECTOR, 'div.uk-position-center-right.uk-overlay.uk-overlay-default.f-swich')
                if img is None:
                    break
                img_url = img.get_attribute('src')
                temp_name = driver.find_element(
                    By.CSS_SELECTOR, 'h1.uk-article-title.uk-text-truncate').text
                if not temp_name.startswith(name):
                    name = temp_name
                if save_img_to_file(img_url, save_path, name):
                    # 保存成功 记录当前进度  当前页URL，当前imgurl
                    save_curr_data(curr_url=driver.current_url,curr_img_url=img_url)
                    logging.info("%s download done!", img_url)
                else:
                    # 失败 等待1分钟后继续
                    sleep(60)
                    continue
                next.click()
                sleep(random.randint(1, 10))
            driver.close()
            driver.switch_to.window(nowhandle)


def find_urls(driver):
    '''
    查找每页的详情地址
    '''
    return driver.find_elements(By.CSS_SELECTOR, 'h2.uk-card-title.uk-margin-small-top.uk-margin-remove-bottom>a')


def process_single_page(driver, save_path):
    '''
    处理单页
    '''
    driver.get('https://mmzztt.com/photo/')
    sleep(3)
    curr_url = read_curr_data_curr_url()
    if curr_url is not None:
        js = f"window.open('{curr_url}')"
        driver.execute_script(js)
        sleep(3)
        find_imgs(driver)
    else:
        links = find_urls(driver)
        for link in links:
            link.click()
            sleep(3)
            find_imgs(driver)
            break


if __name__ == '__main__':
    save_path = './py_imgs'
    driver = create_driver()
    try:
        process_single_page(driver, save_path)
        driver.close()
    except Exception as e:
        logging.error(msg='异常',exc_info=e)
    finally:
        driver.quit()
        os.system("ps -aux | grep firefox | awk '{print $2}' | xargs kill")
