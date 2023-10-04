from flask import Flask, request, render_template, send_file
from scrape import scrape
import tempfile
import zipfile
import os
import shutil
import requests
import json
import csv

app = Flask(__name__)
app.config['DEBUG'] = True


def download_and_save_images(images_data, output_directory, subdirectory):
    images_dir = os.path.join(output_directory, 'images', subdirectory)
    os.makedirs(images_dir, exist_ok=True)

    for index, image_info in enumerate(images_data):
        image_url = image_info.get('image_url')
        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    # Generate a unique filename for each image
                    image_filename = f'image_{index}.jpg'
                    image_filepath = os.path.join(images_dir, image_filename)
                    with open(image_filepath, 'wb') as image_file:
                        image_file.write(response.content)
            except Exception as e:
                print(f"Error downloading image {image_url}: {str(e)}")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'urls_file' not in request.files:
            return "No file part"

        urls_file = request.files['urls_file']
        # Default to CSV if not specified
        output_format = request.form.get('output_format', 'csv')

        if urls_file.filename == '':
            return "No selected file"

        urls_content = urls_file.read().decode('utf-8').splitlines()

        temp_dir = tempfile.mkdtemp()

        for url in urls_content:
            csv_file_name, json_file_name = scrape(
                url, output_format)  # Scrape and generate files

            # Determine which file to copy based on the selected output format
            if output_format == 'csv':
                file_name = csv_file_name
            elif output_format == 'json':
                file_name = json_file_name
            else:
                return "Invalid output format"

            # Extract the subdirectory name from the file name
            subdirectory = os.path.splitext(file_name)[0]

            original_file_path = os.path.join(os.getcwd(), file_name)
            temp_file_path = os.path.join(temp_dir, file_name)

            # Copy the file to the temporary directory
            shutil.copy(original_file_path, temp_file_path)

            # Extract image URLs from JSON or CSV files and download images
            if output_format == 'json':
                images_data = json.load(
                    open(original_file_path, 'r', encoding='utf-8'))
            elif output_format == 'csv':
                images_data = []
                with open(original_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    csv_reader = csv.DictReader(csvfile)
                    for row in csv_reader:
                        image_url = row.get('image_url')
                        if image_url:
                            images_data.append({'image_url': image_url})

            download_and_save_images(images_data, temp_dir, subdirectory)

        zip_file_name = 'scraped_data.zip'
        with zipfile.ZipFile(zip_file_name, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    subdirectory = os.path.basename(root)
                    zipf.write(os.path.join(root, file), os.path.join(
                        subdirectory, file))  # Save with subdirectory

        shutil.rmtree(temp_dir)

        return send_file(zip_file_name, as_attachment=True)

    # Render an HTML template for the form
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
