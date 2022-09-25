from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import numpy as np
import os
import sys
import time

application_path = os.path.dirname(sys.executable)

website = "http://www.sczg.unizg.hr/student-servis/ponuda-poslova/"
path = "chromedriver_win32/chromedriver.exe"

# headless-mode
options = Options()
options.headless = True

service = Service(executable_path=path)
driver = webdriver.Chrome(service=service, options=options)
driver.get(website)


# Get all links of sites where different job ads are posted
elements = driver.find_elements(by="xpath", value='(//div[@class="content"]/h2/a | //div[@class="content"]/h2/strong/a)')
links = [elem.get_attribute("href") for elem in elements]


print("\nDownloading...")
time.sleep(1)

job_df = pd.DataFrame()


# Iterate through each link and save ads in a dataframe
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
                {"full_ad": [job.text], "category": [category]}) for job in job_listings],
                ignore_index=True
                )

        job_df = pd.concat([job_df, df_temp], ignore_index=True)

    print("■", end="", flush=True)

driver.quit()


# Clean dataframe
job_df = job_df.apply(
    lambda x: x.str.strip()
    ).replace(
        "", np.nan
        )

job_df["full_ad"] = job_df["full_ad"].replace(
    r"^[^\d]",
    np.nan,
    regex=True
    )

job_df = job_df.dropna().reset_index(drop=True)

# Towns near Zagreb
town_list = ["Velika Gorica", "Samobor", "Zaprešić", "Sveta Nedelja", "Dugo Selo", "Jastrebarsko", "Sveti Ivan Zelina", "Zabok", "Oroslavlje", "Donja stubica"]

def find_town(row):

    if row["town"] is np.nan:
        for town in town_list:
            if town in row["full_ad"]:
                row["town"] = town
    return row


# Use regex to extract information from job ad
job_df["title"] = job_df["full_ad"].str.extract("(?:\d{4}\s?/)(.+?[^od])\. ")

job_df["work_hours"] = job_df["full_ad"].str.extract("(?<=vrijeme:)\s*(.+?)\. ")

job_df["hourly_rate"] = job_df["full_ad"].str.extract("(\d{1,4}[,\.]?\d{,2}\s*)(?:[Kk]u?[nN][a]?|HRK)(?=[h/\.]*)")
job_df["hourly_rate"] = job_df["hourly_rate"].replace(",", ".", regex=True)
job_df["hourly_rate"] = pd.to_numeric(job_df["hourly_rate"])

job_df["town"] = job_df["full_ad"].str.extract("(Zagreb)")
job_df = job_df.apply(find_town, axis=1)

job_df["street adress"] = job_df["full_ad"].str.extract("([A-ZŠČĆŽĐ][a-zščćžđ]+(?:\s[A-ZŠČĆŽĐ]?[a-zščćžđ]+){,2}?\s\d+\w?)[^\.]*?Zagreb")
ulica_other = job_df["full_ad"].str.extract("Zagreb[^.]*?([A-ZŠČĆŽĐ][a-zščćžđ]+(?:\s[A-ZŠČĆŽĐ]?[a-zščćžđ]+)*?\s\d+\w?)")
job_df["street adress"] = job_df["street adress"].fillna(ulica_other[0])

job_df["contact_info"] = job_df["full_ad"].str.extract("(?:[kK]ontakt|[pP]rijav\w+).{,10}:(.*?)(?:\.\s|$)")

job_df["skills"] = job_df["full_ad"].str.extract("(?:[zZ]nanj|[vV]ještin|[Pp]otreb]\w+).{,10}:(.*?)(?:\.\s)")


job_df.to_csv(f"{application_path}/student_job_data.csv")

print("\nDownload Complete!\n")

input("\nPlease refresh your excel workbook.")
time.sleep(1)

sys.exit()
