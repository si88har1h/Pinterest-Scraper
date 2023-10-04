import argparse
from scrape import scrape
import os
import requests
import json
import csv


def download_images_from_files(output_directory, output_format):
    image_dir = os.path.join(output_directory, 'images')
    os.makedirs(image_dir, exist_ok=True)

    # Iterate over the JSON or CSV files in the output directory
    for file_name in os.listdir(output_directory):
        if file_name.endswith(f'.{output_format}'):
            file_path = os.path.join(output_directory, file_name)

            if output_format == 'json':
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
            elif output_format == 'csv':
                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    data = [row for row in reader]

            # Iterate over the data and download images
            for item in data:
                image_url = item.get('image_url')
                if image_url:
                    image_name = os.path.basename(image_url)
                    image_path = os.path.join(image_dir, image_name)

                    # Download and save the image
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        with open(image_path, 'wb') as img_file:
                            img_file.write(response.content)
                            print(f"Downloaded: {image_name}")


def main():
    parser = argparse.ArgumentParser(description="Web Scraping CLI")

    # Input file containing URLs
    parser.add_argument(
        "input_file", help="Path to the input file with one URL per line")

    parser.add_argument("output_format", choices=[
                        "json", "csv"], help="Output format (json or csv)")

    parser.add_argument("--output_directory", default="./output",
                        help="Output directory for saving files")

    args = parser.parse_args()

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    with open(args.input_file, "r") as file:
        urls = file.read().splitlines()

    for url in urls:
        if args.output_format == "json":
            csv_file_name, json_file_name = scrape(
                url, output_format="json", output_directory=args.output_directory)
        elif args.output_format == "csv":
            csv_file_name, json_file_name = scrape(
                url, output_format="csv", output_directory=args.output_directory)
        else:
            print("Invalid output format. Please choose 'json' or 'csv'.")

    # Download images from the generated files
    download_images_from_files(args.output_directory, args.output_format)


if __name__ == "__main__":
    main()
