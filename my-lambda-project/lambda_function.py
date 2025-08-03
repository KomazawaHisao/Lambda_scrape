import requests
import urllib.robotparser
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

def is_scraping_allowed(target_url, user_agent="*"):
    parsed_url = urlparse(target_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = f"{base_url}/robots.txt"

    try:
        with urllib.request.urlopen(robots_url, timeout=5) as response:
            content = response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"[robots.txt取得失敗] {robots_url}: {e}")
        return False

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.parse(content)

    return rp.can_fetch(user_agent, target_url)

def google_search(query, num=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": num,
    }
    response = requests.get(url, params=params)
    results = response.json()
    return [item["link"] for item in results.get("items", [])]

def save_text_to_s3(text, url, bucket_name, folder_name=None):
    s3 = boto3.client('s3')
    from hashlib import sha256
    file_name = sha256(url.encode()).hexdigest() + ".txt"
    # フォルダ名が指定されていればKeyに追加
    if folder_name:
        key = f"{folder_name}/{file_name}"
    else:
        key = file_name
    s3.put_object(Bucket=bucket_name, Key=key, Body=text)
    print(f"S3に保存しました: {key}")

def clear_s3_folder(bucket_name, folder_name):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name + "/")
    # フォルダ（Prefix）にファイルがなければスキップ
    if "Contents" in response and response["KeyCount"] > 0:
        for obj in response["Contents"]:
            s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
        print(f"S3バケット「{bucket_name}」の「{folder_name}」フォルダ配下を全削除しました")
    else:
        print(f"S3上に「{folder_name}」フォルダが存在しないか、既に空です")

def lambda_handler(event, context):
    bucket_name = "learn-data-komahisa2017"
    folder_name = "印刷会社"
    clear_s3_folder(bucket_name, folder_name)  # ← 59行目で全削除
    urls = google_search("印刷会社 site:.jp")
    for url in urls:
        print(f"{url}")
        allowed = is_scraping_allowed(url)
        print(f"Scraping allowed: {url} {allowed}")
        if allowed == True:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print({"statusCode": 500, "body": "Failed to fetch page"})
                continue
            soup = BeautifulSoup(response.content, "html.parser")
            body = soup.body
            if body:
                text = body.get_text(separator="\n", strip=True)
                print(text)
                save_text_to_s3(text, url, bucket_name, folder_name)
            else:
                print("bodyタグが見つかりませんでした")