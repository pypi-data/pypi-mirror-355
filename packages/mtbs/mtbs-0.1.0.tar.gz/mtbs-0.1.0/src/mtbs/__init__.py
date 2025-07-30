import csv
import json
import logging
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Dict, List
import requests

logger = logging.getLogger("mtbs")
match os.getenv('MTBS_LOG_LEVEL'):
    case 'CRITICAL':
        _LOG_LEVEL = logging.CRITICAL
    case 'FATAL':
        _LOG_LEVEL = logging.FATAL
    case 'INFO':
        _LOG_LEVEL = logging.INFO
    case 'DEBUG':
        _LOG_LEVEL = logging.DEBUG
    case 'WARNING':
        _LOG_LEVEL = logging.WARNING
    case 'ERROR':
        _LOG_LEVEL = logging.ERROR
    case _:
        _LOG_LEVEL = logging.ERROR
        
logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),  # console display
        # logging.FileHandler("app.log")  # Save logs in a file
    ]
)
mtbs_db_list_url = "{base_url}/api/database"
mtbs_base_url = "{base_url}/api/dataset"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.'", 
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Origin": "{base_url}",
    "Connection": "keep-alive",
    "Referer": "{base_url}",
    "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin", "Priority": "u=0", "TE": "trailers", 
}
headers_data = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "{base_url}",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Origin": "{base_url}",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
}
def hello() -> str:
    return "Hello from mtbs!!"

def read_metabase_config_from_browser():
    global mtbs_db_list_url,mtbs_base_url, headers, headers_data
    db_path = copy_firefox_cookies()
    if not db_path:
        print("No Firefox profile found or cookies.sqlite not available.")
        return
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT host, name, value FROM moz_cookies where host like '%metabase-prd%';")
        cookies = cursor.fetchall()
        if not cookies:
            print("No cookies found for metabase-prd.")
            return
        mtbs_db_list_url = mtbs_db_list_url.format(base_url=f"https://{cookies[0][0]}")
        mtbs_base_url = mtbs_base_url.format(base_url=f"https://{cookies[0][0]}")
        headers['Origin'] = headers['Origin'].format(base_url=f"https://{cookies[0][0]}")
        headers['Referer'] =  headers['Referer'].format(base_url=f"https://{cookies[0][0]}/question")
        headers['Cookie'] = ";".join([f'{name}={value}' for _, name, value in cookies])
        headers_data['Cookie'] = headers['Cookie']
        headers_data['Origin'] = headers['Origin']
        headers_data['Referer'] = headers['Referer']

def copy_firefox_cookies() -> Path:
    profile_path = next(Path.home().glob(".mozilla/firefox/*.default-release"), None)
    if not profile_path:
        return None
    source_file = profile_path / "cookies.sqlite"
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / "cookies_firefox.sqlite"
    shutil.copy2(source_file, temp_file)
    return temp_file

def payload_template(query, database) -> dict:
    return {
        "type":"native",
        "native":{
            "query":f"{query}",
            "template-tags":{}
        },
        "database":database,
        "parameters":[]
    }

def read_cookies(cookie_file='cookies.json'):
    global mtbs_base_url, headers, headers_data
    with open(cookie_file, 'r') as file:
        data = json.load(file)
    
    mtbs_db_list_url = mtbs_db_list_url.format(base_url=f"{data[0]['Host raw']}")
    mtbs_base_url = mtbs_base_url.format(base_url=f"{data[0]['Host raw']}")
    headers['Origin'] = headers['Origin'].format(base_url=data[0]['Host raw'])
    headers['Referer'] = headers['Referer'].format(base_url=f"{data[0]['Host raw']}question")
    headers['Cookie'] = ";".join([f'{item["Name raw"]}={item["Content raw"]}' for item in data])
    headers_data['Cookie'] = headers['Cookie']
    headers_data['Origin'] = headers['Origin']
    headers_data['Referer'] = headers['Referer']


def send_sql(url, query=None, database=None, raw=False) -> str:
    logger.debug(f"Sending SQL query to {url} for database {database} with query: \n {query}")
    empty = {"data": {"cols": [], "rows": []}} if raw else []
    if not url or not query or not database:
        logger.error("Url, Query and database must be provided.")
        return empty
    
    try:
        response = requests.post(url, headers=headers, json=payload_template(query, database), timeout=240)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.error("The request timed out.")
        return empty
    except Exception as e:
        logger.error(f"Error while retrieving or decoding JSON: {e}")
        logger.error("Raw response content: %s", getattr(response, 'text', '')[:500])
        return empty
    if raw:
        return data
        # return json.dumps(data, ensure_ascii=False)
    
    results = raw_to_object(data)
    return json.dumps(results, ensure_ascii=False)

def raw_to_object(data):
    cols = [col['name'] for col in data['data']['cols']]
    rows = data['data']['rows']
    results = [dict(zip(cols, row)) for row in rows]
    return results

def recursive_sql(url, query, database, limit=2000, offset=0, write_header=True, output_file=None):
    current_offset = offset
    first_batch = True
    while True:
        query_limit = query + f" LIMIT {limit} OFFSET {current_offset};"
        result_raw = send_sql(url, query_limit, database, raw=True)
        if not result_raw or 'data' not in result_raw or 'rows' not in result_raw['data']:
            logger.error(f"Stop: no data for {query_limit}")
            break
        headers = [col['name'] for col in result_raw['data']['cols']]
        result = result_raw['data']['rows']
        
        if not result:
            logger.error(f"Stop: no rows for {query_limit}")
            break
        logger.info(f"Result: {result}")

        if output_file is not None:
            with open(output_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                if (write_header or first_batch) and len(headers) > 0:
                    writer.writerow([str(item) if item is not None else "None" for item in headers])
                    first_batch = False
                for i in result:
                    writer.writerow([str(item) if item is not None else "None" for item in i])

        if len(result) < limit:
            break
        current_offset += limit


def load_json(json_file_path: str) -> List[Dict]:
    """Charge un fichier JSON avec validation."""
    try:
        absolute_path = Path(json_file_path)
        if not absolute_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {json_file_path}")
        
        with open(absolute_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Validation minimale du format
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                raise ValueError("Format JSON invalide. Attend une liste de dictionnaires.")

            return data

    except json.JSONDecodeError:
        raise ValueError("Fichier JSON malformé")
    except Exception as e:
        raise RuntimeError(f"Erreur de chargement : {str(e)}")
    
def get_databases():
    try:
        _data = load_json("database_full_list.json")
        #data = sorted(_data, key=lambda x: x["name"].lower())
        _data.sort(key=lambda x: x["name"].lower())
        data = {item["name"]: item["id"] for item in _data}
        return data
    except Exception as e:
        print(f"❌ Critical error : {e}")
        return None
    
def databases_list() -> List[Dict]:

    response = requests.get(mtbs_db_list_url, headers=headers, timeout=240)
    response.raise_for_status()

    data = {db['name']: db['id'] for db in response.json()['data']}
    return data
    #return json.dumps(data, ensure_ascii=False)