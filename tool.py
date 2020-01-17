import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException   
import pandas as pd
import numpy as np
import time
import re
import json
import platform
import os
import csv
import sys 
import random
import re

my_platform = platform.system()  # 'Windows' or 'Darwin'
test_mode = 0
FILE_NAME= 'Amazon - Competitor Tracking'

def scroll_down(limit): 
    SCROLL_PAUSE_TIME = 0.5
    height = driver.execute_script("return document.body.scrollHeight")
    one_third = int(height/3)
    driver.execute_script("window.scrollTo(0, " + str(one_third) +  ");")
    time.sleep(SCROLL_PAUSE_TIME)
    if(limit == 1):
        return
    two_third = one_third + one_third
    driver.execute_script("window.scrollTo(0, " + str(two_third) +  ");")
    three_third = two_third + one_third
    time.sleep(SCROLL_PAUSE_TIME)
    if(limit == 2):
        return
    driver.execute_script("window.scrollTo(0, " + str(three_third) +  ");")


#loading params
with open('params.json') as json_file:
    data = json.load(json_file)
    sleep_between_pagesp = data["params"]["sleep_between_pages"]
    total_departments_limitp  = data["params"]["total_departments"]


try:
    sleep_between_pages = int(sleep_between_pagesp)
    print("Sleep between pages (seconds): " +  str(sleep_between_pages))
except:
    sleep_between_pages = -1
    print("No sleep time specified")
    sys.exit()

try:
    total_departments_limit = int(total_departments_limitp)
    print("Department limit set: " +  str(total_departments_limit))
except:
    total_departments_limit = -1
    print("No department limit specified")
    sys.exit()


SLEEP_BETWEEN_PRODUCTS = sleep_between_pages
SLEEP_BETWEEN_SCROLLING_SELLERS = sleep_between_pages
SLEEP_BETWEEN_SELLERS = sleep_between_pages


with open("departments.txt", 'r') as f:
    temp_prev_depts  = f.readlines()

prev_depts = []
for x in temp_prev_depts:
    temp = x.replace("\n","")
    prev_depts.append(temp)

prev_depts.append("https://www.amazon.com/Best-Sellers-MP3-Downloads/zgbs/dmusic/ref=zg_bs_nav_0")
prev_depts.append("https://www.amazon.com/Best-Sellers-MP3-Downloads/zgbs/dmusic/ref=zg_bs_nav_0&pg=1")

prev_seller_ids = []
#read file and fill in previous seller IDs
print("Reading File and Accessing Seller IDs")

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('cred.json', scope)

gc = gspread.authorize(credentials)

worksheet = gc.open(FILE_NAME).worksheet("Competitor Extractions")
data = worksheet.get_all_values()
headers = data.pop(0)
data = pd.DataFrame(data, columns=headers)
data = pd.DataFrame(data)

prev_seller_ids = []
for index, row in data.iterrows():
    seller_id = row['Seller ID']
    prev_seller_ids.append(prev_seller_ids)
          
print("Total Seller IDs extracted: " ,  len(prev_seller_ids))


#main
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

#main automation
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if(my_platform == 'Windows'):
    DRIVER_BIN = os.path.join(PROJECT_ROOT, "drivers/chromedriver.exe")
    driver = webdriver.Chrome(options= options, executable_path = DRIVER_BIN)
else:
    DRIVER_BIN = os.path.join(PROJECT_ROOT, "drivers/chromedriver")
    driver = webdriver.Chrome(options= options, executable_path = DRIVER_BIN)

# extracting all the departments
amazon_best_sellers = "https://www.amazon.com/Best-Sellers/zgbs"
driver.get(amazon_best_sellers)
driver.implicitly_wait(1)
side_box = driver.find_element_by_id("zg_left_col2")
list_depts = side_box.find_elements_by_tag_name("a")
scroll_down(1)

dept_hrefs= []
for x in list_depts:
    href = x.get_attribute("href")
    if (href not in prev_depts and "/dmusic/" not in href):
        dept_hrefs.append(href)

if(len(dept_hrefs) < total_departments_limit):
    print("Departments left (" + str(len(dept_hrefs)) + ") are less than the number of departments specified to extract (" + str(total_departments_limit) + ")")
    print("Exiting the program")
    sys.exit()

my_departments = random.sample(dept_hrefs, total_departments_limit)
for my_dept in my_departments:
    with open("departments.txt", 'a') as f:
        f.write(my_dept  + "\n")
        prev_depts.append(my_dept)

product_hrefs = []
print("Extracting Products.. Please wait..")
for my_dept in my_departments:
    link_split = my_dept.split("zg_bs_nav_0")
    dept_link = link_split[0] + "zg_bs_nav_0"
    dept_link = dept_link + "&pg=1"
    while(True): 
        driver.get(dept_link)
        try:
            main_box = driver.find_element_by_id("zg-center-div")
            list_products = main_box.find_elements_by_class_name("a-section.a-spacing-none.aok-relative")
        except:
            print("No more products found, all the products for the given department are extracted")
            break
        
        for product in list_products:
            try:
                product_link = product.find_element_by_class_name("a-link-normal").get_attribute("href")
                if(test_mode):
                    if(len(product_hrefs) < 5):
                        product_hrefs.append(product_link)
                else:
                    product_hrefs.append(product_link)
            except:
                pass

        print("=> Total Products Extracted from page: " , len(product_hrefs))
        url_split = dept_link.split("&pg=") 
        cur_page = int(url_split[1])
        new_page = cur_page + 1
        dept_link = url_split[0] + "&pg=" + str(new_page)

    print("=> Total Products Extracted uptil now: " , len(product_hrefs))


my_dict = {}
valid_seller_links = []
print(" *** Extracting Sellers.. Please wait.. ***")
for product in product_hrefs:
    driver.get(product)
    link_found = False
    all_hyps = driver.find_elements_by_tag_name("a")
    for hyp in all_hyps:
        try:
            hyp_text = hyp.text.lower() 
            my_list = re.findall('\d+', hyp_text)
            if(("new" in hyp_text or "used" in hyp_text) and "from" and "(" in hyp_text and ")" in hyp_text and "$" in hyp_text and len(my_list) > 0 and len(hyp_text) < 30):
                link_found = True
                other_link = hyp
                print("Link1 found :", hyp_text)
                break
        except:
            pass
    
    if(not link_found):
        for hyp in all_hyps:
            try:
                hyp_text = hyp.text.lower() 
                my_list = re.findall('\d+', hyp_text)
                if(("new" in hyp_text or "used" in hyp_text) and "from" and "$" in hyp_text and len(my_list) > 0 and len(hyp_text) < 30):
                    link_found = True
                    other_link = hyp
                    print("Link2 found :", hyp_text)
                    break
            except:
                pass
    
    if(not link_found):
        for hyp in all_hyps:
            try:
                hyp_text = hyp.text.lower() 
                my_list = re.findall('\d+', hyp_text)
                if(("new" in hyp_text or "used" in hyp_text) and len(my_list) > 0 and len(hyp_text) < 10):
                    link_found = True
                    other_link = hyp
                    print("Link3 found :", hyp_text)
                    break
            except:
                pass


    if(link_found):
        print("Product found with New/Used Sellers.")
        try:
            other_link_text = other_link.text
            text_split = other_link_text.split("$")
            toExtractFrom = text_split[0]
            my_list = re.findall('\d+', toExtractFrom)
            number_sellers = int(my_list[0])
            print("Number of Used/New sellers: " , number_sellers)
            other_link_href = other_link.get_attribute("href") + "&startIndex=0" 
            while True:
                driver.get(other_link_href)
                driver.implicitly_wait(1)

                #code goes here to extract sellers
                all_divs = driver.find_elements_by_class_name("a-column.a-span2.olpSellerColumn")
                for div in all_divs:
                    try:
                        valid_seller =  False
                        text = div.text.lower()
                        text = text.replace(",", "")
                        text = text[text.find("(")+1:text.find(")")]
                        my_list = re.findall('\d+', text)
                        if(len(my_list) > 0):
                            lifetime_ratings = int(my_list[0])
                            if(lifetime_ratings >= 3000 and lifetime_ratings <= 75000):
                                valid_seller = True
                        
                        h3_ele = div.find_element_by_class_name("a-spacing-none.olpSellerName")
                        href_ele = h3_ele.find_elements_by_tag_name("a")
                        seller_url = href_ele[0].get_attribute("href")
                        url_split = seller_url.split("seller=")
                        id_extra = url_split[1]
                        id_extra_split = id_extra.split("&")
                        seller_id = id_extra_split[0]
                        if(seller_id in prev_seller_ids):
                            valid_seller = False
                
                        if(valid_seller):
                            print("Seller ID: ", seller_id)
                            my_dict[seller_id] = ""
                            print("Valid Seller: ", valid_seller)
                            print("Seller Name: ", href_ele[0].text)
                            my_dict[seller_id] = href_ele[0].text
                            print("Seller Href: " , seller_url)
                            valid_seller_links.append(seller_url)     
                            prev_seller_ids.append(seller_id)
                    except Exception as e:
                        print("E: "  , e)
                        
                url_split = other_link_href.split("&startIndex=")
                cur_index = int(url_split[1])
                new_index = cur_index + 10
                if(new_index > number_sellers):
                    print("All sellers for the given product extracted")
                    break

                other_link_href = url_split[0] + "&startIndex=" + str(new_index)
                time.sleep(SLEEP_BETWEEN_SCROLLING_SELLERS)

        except Exception as e:
            # print("Exception in Products: " , e)
            pass
    
    print("==> Total Valid Sellers Extracted Uptil Now: " , len(valid_seller_links))
    time.sleep(SLEEP_BETWEEN_PRODUCTS)


print(" *** Extracting Info from Sellers ***")
for link in valid_seller_links:
    try:
        valid_seller_check = True
        driver.get(link)
        table_elements = driver.find_elements_by_class_name("a-text-right")
        daily_count_seller =  table_elements[16].text
        daily_count_seller = daily_count_seller.replace(",","")
        lifetime_ratings = table_elements[19].text
        if(int(daily_count_seller) < 75):
            print("Not a valid seller, less than 75 last month's ratings")
            valid_seller_check = False
        
        if(valid_seller_check):
            print("Its a valid seller, extracting Additional Info")
            product_href = driver.find_element_by_partial_link_text("Products")
            seller_url = driver.current_url
            url_split = seller_url.split("seller=")
            id_extra = url_split[1]
            id_extra_split = id_extra.split("&")
            seller_id = id_extra_split[0]
            seller_name  = my_dict[seller_id]
            print("Last Month Count:" , daily_count_seller)
            print("Lifetime count: ", lifetime_ratings)        
            print("Seller URL =", seller_url)
            print("Seller ID: ", seller_id)
            try:
                product_href.click()
                pagination = driver.find_element_by_class_name("a-pagination")
                li_items = pagination.find_elements_by_tag_name("li")
                # print("Length Li Items: ", len(li_items))
                page_list = []
                for li in li_items:
                    try:
                        my_list = re.findall('\d+', li.text)
                        if(not len(my_list) == 0):
                            page_list.append(int(my_list[0]))
                    except Exception as e:
                        pass
                        # print("Inner Exception: " , e)
                if(not len(page_list) == 0):
                    product_max_page = max(page_list)
                else:
                    product_max_page = 1
            
            except:
                product_max_page = 1
            
            print("Product Max Page: ", product_max_page)
            to_write = [seller_name,seller_url,"",seller_id, lifetime_ratings, daily_count_seller, product_max_page]
            worksheet.append_row(to_write , value_input_option='RAW')
            print(" ** Wrote seller to File! ** ")
        
        time.sleep(SLEEP_BETWEEN_SELLERS)
        
    except Exception as e:
        # print("Exception in Sellers: ", e)
        pass

    