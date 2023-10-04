from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import csv
import os
from urllib.parse import urlparse, parse_qs


def generate_csv_filename(url):
    # Parse the URL to extract query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Get the 'q' parameter and remove any leading/trailing whitespace
    query_param = query_params.get('q', [''])[0].strip()

    # Replace '%20' with underscores and add the '.csv' extension
    file_name = query_param.replace('%20', '_') + '.csv'

    return file_name


def scrape(url, output_format, output_directory=None):
    csv_file_name = generate_csv_filename(url)
    json_file_name = csv_file_name.replace('.csv', '.json')

    # Initialize the WebDriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Set a maximum wait time for waiting for elements
    wait = WebDriverWait(driver, 10)

    # Perform an initial scroll to load more content (5 full scrolls)
    for _ in range(5):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # Define a function to scrape a page

    def scrape_page(driver):
        parent_xpath = '//*[@id="mweb-unauth-container"]/div/div[2]/div[2]/div/div/div/div[1]'
        parent_element = wait.until(
            EC.presence_of_element_located((By.XPATH, parent_xpath)))

        children = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, f'{parent_xpath}/*')))

        pages_data = []

        # Iterate through the children and find the anchor tags within each child
        for child in children:
            try:
                anchor_tag = child.find_element(By.TAG_NAME, 'a')
                href = anchor_tag.get_attribute('href')
                driver.execute_script(f"window.open('{href}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                time.sleep(5)

                media_element = driver.find_element(By.TAG_NAME, 'img')
                if media_element:
                    image_url = media_element.get_attribute('src')
                    if driver.find_elements(By.XPATH, '//*[@data-test-id="aggregated-comment-list"]'):

                        comment_list_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@data-test-id="aggregated-comment-list"]')))

                        comment_elements = comment_list_element.find_elements(
                            By.CSS_SELECTOR, '.tBJ.dyH.iFc.sAJ.O2T.zDA.swG')

                        comments = [comment.text.strip()
                                    for comment in comment_elements]

                    else:
                        comments = []

                    comment_count = len(comments)

                    page_title = driver.title

                    page_data = {
                        "title": page_title,
                        "image_url": image_url,
                        "comments": comments,
                        "comment_count": comment_count
                    }

                    pages_data.append(page_data)

                driver.close()

                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print("Error:", str(e))

        return pages_data

    try:
        pages_data = scrape_page(driver)

    except Exception as e:
        print("Error:", str(e))

    finally:
        driver.quit()

    if output_format == 'json':
        if output_directory is not None:
            json_file_path = os.path.join(output_directory, json_file_name)
        else:
            json_file_path = json_file_name

        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(pages_data, json_file, ensure_ascii=False, indent=4)
        print(f"Data saved to {json_file_path}")
    else:
        if output_directory is not None:
            csv_file_path = os.path.join(output_directory, csv_file_name)
        else:
            csv_file_path = csv_file_name

        # Define the CSV file name
        fieldnames = ['title', 'image_url', 'comments', 'comment_count']

        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for page in pages_data:
                writer.writerow(page)
        print(f"Data saved to {csv_file_path}")

    return csv_file_name, json_file_name
