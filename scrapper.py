# %%
import selenium
from selenium import webdriver
from selenium.webdriver import Chrome as wdChrome, Firefox as wdFirefox, Edge as wdEdge
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.wAebdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as selExcep 

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


import pandas as pd
import numpy as np
import time

# %%
gm_search_keywords = []
with open("keywords.txt") as keywords:
    gm_search_keywords = [kw.rstrip() for kw in keywords]
    
# n = int(len(gm_search_keywords)/4)

# #################
#                 #
# PARTITION = 0   #
#                 #
# #################

# start = n * PARTITION
# end = n * (PARTITION + 1)
# gm_search_keywords = gm_search_keywords[start:end]

# %%
home_url = 'https://www.google.com/maps/place/Lahore,+Punjab,+Pakistan/@74.1943055,31.4831569,11z/data=!3m1!4b1!4m5!3m4!1s0x39190483e58107d9:0xc23abe6ccc7e2462!8m2!3d31.5203696!4d74.3587473'
driver_type = "chromeium"
service = ChromeService(executable_path = ChromeDriverManager().install())
driver = wdChrome(service= service)
driver.get(home_url)
action = ActionChains(driver)
time.sleep(1)

# %%
MAP_SEARCH_XPATH = '//*[@id="searchboxinput"]'
LOCATION_BOX_XPATH = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]'
LOC_BOX_CLASS = "hfpxzc"

# %%
LOC_NAME_XPATH = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[1]/h1'
LOC_RATING_XPATH = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[2]/div/div[1]/div[2]/span[1]/span/span[1]'
LOC_RATING_COUNT_XPATH = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[2]/div/div[1]/div[2]/span[2]/span[1]/button'

# %%
def search_map(query: str) -> None:
    map_searchbar = driver.find_element(By.XPATH, MAP_SEARCH_XPATH)
    map_searchbar.clear()
    map_searchbar.send_keys(query)
    map_searchbar.send_keys(Keys.RETURN)

# %% [markdown]
# ### Collecting hrefs from all locations in a radius

# %%
## Covers all of lahore

start_lat= 31.283179
start_long= 74.080275

stop_lat = 31.671291
stop_long = 74.551132

lat_step = (stop_lat - start_lat) / 4
long_step = (stop_long - start_long) / 4

lat_dist = np.arange(start=start_lat, stop= stop_lat, step= lat_step, dtype= "float32")
long_dist = np.arange(start=start_long, stop= stop_long, step= long_step, dtype= "float32")

geo_loc_grid = np.transpose([np.tile(lat_dist, len(long_dist)), np.repeat(long_dist, len(lat_dist))])

# %%
hrefs_set = set()

last_href = None
find_all_elem = False
curr_url = driver.current_url
template_url = curr_url.split("@")[0]

for query in gm_search_keywords:
    search_map(query)
    print(query)
    for loc in geo_loc_grid:
        lat = loc[0]
        long = loc[1]
        dynamic_url = f"{template_url}@{lat},{long},13z/data=!3m1!4b1"
        driver.get(dynamic_url)
        time.sleep(1)
        while not find_all_elem:
            loc_div = driver.find_element(By.XPATH, LOCATION_BOX_XPATH)
            action.move_to_element(loc_div).perform()
            loc_boxes = driver.find_elements(By.CLASS_NAME, LOC_BOX_CLASS)
            hrefs = [loc_box.get_attribute("href") for loc_box in loc_boxes]
            hrefs_set.update(hrefs)
            loc_div.send_keys(Keys.END)
            time.sleep(3)
            
            if(last_href == None):
                last_href = hrefs[-1]
                continue
            
            if(last_href == hrefs[-1]):
                find_all_elem = True
            else:
                last_href = hrefs[-1]
        find_all_elem = False
        time.sleep(5)
    time.sleep(10)
    
len(hrefs_set)

# %%
href_list = list(hrefs_set)
href_list.sort()
file_name = f"href_list.txt"

with open(file_name, 'a') as my_file:
    for href in href_list:
        my_file.write(href)

# %% [markdown]
# # Extracting data from href

# %%
df = pd.DataFrame()

# %% [markdown]
# ### getting data from each href

# %%
href_list = list()
loc_names = list()
loc_ratings = list()
latitudes = list()
longitudes = list()
total_ratings = list()


# %%
href_list = list(hrefs_set)
href_list.sort()

# %% [markdown]
# ### Getting infro from each href

# %%
for href in href_list:
    lat, long = href.split("!3d")[1].split("!4d")
    long = long.split("!")[0]
    
    driver.get(href)
    time.sleep(1)
    
    check_load = True
    refresh_time = 10
    while(check_load):
        try:
            name = driver.find_element(By.XPATH, LOC_NAME_XPATH).text
            check_load = False
            
        except selExcep.NoSuchElementException:
            # Ip got blocked, Wait for some time and refresh
            time.sleep(refresh_time)
            driver.get(href)
            time.sleep(1)
            refresh_time += 5
    
    try:
        rating = driver.find_element(By.XPATH, LOC_RATING_XPATH).text
        rating_count = driver.find_element(By.XPATH, LOC_RATING_COUNT_XPATH).text.split()[0]
        rating_count = rating_count.replace(",", "")
        rating_count = int(rating_count)  
        
    except selExcep.NoSuchElementException:
        rating = None
        rating_count = None
          
    loc_names.append(name)
    loc_ratings.append(rating)
    latitudes.append(lat)
    longitudes.append(long)
    total_ratings.append(rating_count)
    time.sleep(3)
    

# %%
df["loc_name"] = loc_names
df["loc_rating"] = loc_ratings
df["total_rating"] = total_ratings
df["latitude"] = latitudes
df["longitude"] = longitudes
df

# %%
df.to_csv(f'prototype.csv')

# %%



