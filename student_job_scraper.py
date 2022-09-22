from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import numpy as np
import os
import sys

print("Starting download...")

application_path = os.path.dirname(sys.executable)

website = "http://www.sczg.unizg.hr/student-servis/ponuda-poslova/"
path = "chromedriver_win32/chromedriver.exe"

# headless-mode
options = Options()
options.headless = True

service = Service(executable_path=path)
driver = webdriver.Chrome(service=service, options=options)
driver.get(website)


elements = driver.find_elements(by="xpath", value='(//div[@class="content"]/h2/a | //div[@class="content"]/h2/strong/a)')
links = [elem.get_attribute("href") for elem in elements]


print("Downloading...")

job_df = pd.DataFrame()

for link in links:
    driver.get(link)
    
    job_site = driver.find_elements(
        by="xpath", 
        value='//div[@class="newsItem"]'
        )

    for element in job_site:
            
        category = element.find_element(
            by="xpath", 
            value='./h1'
            ).text
        job_listings = element.find_elements(
            by="xpath", 
            value='./div/p'
            )

        df_temp = pd.concat(
            [pd.DataFrame(
                {"full_desc": [job.text], "category": [category]}) for job in job_listings], 
                ignore_index=True
                )
        
        job_df = pd.concat([job_df, df_temp], ignore_index=True)
        
    print("■", end="")

driver.quit()


job_df = job_df.apply(
    lambda x: x.str.strip()
    ).replace(
        "", np.nan
        )

job_df["full_desc"] = job_df["full_desc"].replace(
    r"^[^\d]", 
    np.nan, 
    regex=True
    )

job_df = job_df.dropna().reset_index(drop=True)


zgzup_mjesta = pd.read_csv("zgzup_mjesta.csv", encoding="utf8")
town_list = list(zgzup_mjesta["Mjesto"])

def find_town(row):

    if row["mjesto"] is np.nan:
        for town in town_list:
            if town in row["full_desc"]:
                row["mjesto"] = town
    return row


job_df["naslov"] = job_df["full_desc"].str.extract("(?:\d{4}\s?/)(.+?[^od])\. ")

job_df["radno_vrijeme"] = job_df["full_desc"].str.extract("(?<=vrijeme:)\s*(.+?)\. ")

job_df["satnica/kn"] = job_df["full_desc"].str.extract("(\d{1,4}[,\.]?\d{,2}\s*)(?:[Kk]u?[nN][a]?|HRK)(?=[h/\.]*)")
job_df["satnica/kn"] = job_df["satnica/kn"].replace(",", ".", regex=True)
job_df["satnica/kn"] = pd.to_numeric(job_df["satnica/kn"])

job_df["mjesto"] = job_df["full_desc"].str.extract("(Zagreb)")
job_df = job_df.apply(find_town, axis=1)

job_df["ulica"] = job_df["full_desc"].str.extract("([A-ZŠČĆŽĐ][a-zščćžđ]+(?:\s[A-ZŠČĆŽĐ]?[a-zščćžđ]+){,2}?\s\d+\w?)[^\.]*?Zagreb")
ulica_other = job_df["full_desc"].str.extract("Zagreb[^.]*?([A-ZŠČĆŽĐ][a-zščćžđ]+(?:\s[A-ZŠČĆŽĐ]?[a-zščćžđ]+)*?\s\d+\w?)")
job_df["ulica"] = job_df["ulica"].fillna(ulica_other[0])

job_df["kontakt"] = job_df["full_desc"].str.extract("(?:[kK]ontakt|[pP]rijav\w+).{,10}:(.*?)(?:\.\s|$)")

job_df["vjestine"] = job_df["full_desc"].str.extract("(?:[zZ]nanj|[vV]ještin|[Pp]otreb]\w+).{,10}:(.*?)(?:\.\s)")


job_df.to_csv(f"{application_path}/student_job_data.csv")

print("\nDownload Complete!\n")
input("Press enter to continue")