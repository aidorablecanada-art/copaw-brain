#!/usr/bin/env python3

import os
import json
import time
import requests
import psutil
import logging
import threading
from datetime import datetime
from flask import Flask, jsonify

# ===== Configuration from environment =====
BRAIN_URL = os.environ.get('BRAIN_URL')
NODE_PORT = int(os.environ.get('NODE_PORT', 3001))
NODE_NAME = os.environ.get('NODE_NAME', os.uname().nodename)
NODE_ID = os.environ.get('NODE_ID', f"worker-{os.uname().nodename}-{int(time.time())}")
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', 5))  # seconds

# Fail fast if BRAIN_URL is not set
if not BRAIN_URL:
    raise ValueError("❌ BRAIN_URL environment variable is required!")

# ===== Logging setup =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== Flask app =====
app = Flask(__name__)

# ===== Node state =====
current_task = None
task_start_time = None
stats = {
    'completed_tasks': 0,
    'failed_tasks': 0,
    'total_work_time': 0
}

# ===== Node specs =====
NODE_SPECS = {
    'platform': os.uname().sysname,
    'arch': os.uname().machine,
    'cpus': psutil.cpu_count(),
    'totalMemory': round(psutil.virtual_memory().total / 1024 / 1024),  # MB
    'freeMemory': round(psutil.virtual_memory().available / 1024 / 1024),  # MB
    'uptime': time.time() - psutil.boot_time()
}

# ===== Registration & Heartbeat =====
def register_with_brain():
    """Register this worker with the brain server"""
    try:
        response = requests.post(
            f"{BRAIN_URL}/api/nodes/register",
            json={'id': NODE_ID, 'name': NODE_NAME, 'specs': NODE_SPECS},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"🧠 Successfully registered with brain server as {NODE_NAME}")
            return True
        else:
            logger.error(f"❌ Failed to register: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to register with brain server: {e}")
        return False

def send_heartbeat():
    """Send heartbeat to brain server"""
    try:
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        memory = psutil.virtual_memory()
        load_data = {
            'cpu': load_avg[0] * 100,
            'memory': ((memory.total - memory.available) / memory.total) * 100,
            'disk': 0
        }
        response = requests.post(
            f"{BRAIN_URL}/api/nodes/{NODE_ID}/heartbeat",
            json=load_data,
            timeout=5
        )
        if response.status_code != 200:
            logger.warning(f"⚠️ Failed to send heartbeat: {response.status_code}")
    except Exception as e:
        logger.error(f"⚠️ Failed to send heartbeat: {e}")

def get_task_from_brain():
    """Get next task from brain server"""
    try:
        response = requests.get(f"{BRAIN_URL}/api/nodes/{NODE_ID}/task", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'task_id' in data:
                return data
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get task: {e}")
        return None

def submit_task_result(task_id, result, error=None):
    """Submit task result to brain server"""
    try:
        data = {'task_id': task_id, 'result': result}
        if error:
            data['error'] = error
        response = requests.post(f"{BRAIN_URL}/api/nodes/{NODE_ID}/result", json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Result submitted for task {task_id}")
            return True
        else:
            logger.error(f"❌ Failed to submit result: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to submit result: {e}")
        return False

# ===== Task execution =====
def execute_task(task):
    """Execute a task based on its type"""
    global task_start_time
    task_start_time = time.time()
    task_type = task['type']
    task_data = task['data']
    logger.info(f"📋 Executing task: {task_type}")
    try:
        # Map task types to functions
        func_map = {
            'file_processing': execute_file_processing,
            'file_chunk': execute_file_chunk,
            'web_scraping': execute_web_scraping,
            'scraping_chunk': execute_scraping_chunk,
            'data_processing': execute_data_processing,
            'data_chunk': execute_data_chunk,
            'computation': execute_computation,
            'computation_chunk': execute_computation_chunk
        }
        if task_type not in func_map:
            raise ValueError(f"Unknown task type: {task_type}")
        result = func_map[task_type](task_data)
        stats['completed_tasks'] += 1
        stats['total_work_time'] += time.time() - task_start_time
        logger.info(f"✅ Task completed: {task_type}")
        return result
    except Exception as e:
        stats['failed_tasks'] += 1
        logger.error(f"❌ Task failed: {task_type} - {e}")
        return {'error': str(e)}

# ===== Task execution helpers =====
def execute_file_processing(files):
    results, total_size = [], 0
    for file_path in files:
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                results.append({'path': file_path, 'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'exists': True})
                total_size += stat.st_size
            else:
                results.append({'path': file_path, 'exists': False})
        except Exception as e:
            results.append({'path': file_path, 'error': str(e), 'exists': False})
    return {
        'files': results,
        'total_files': len(files),
        'total_size': total_size,
        'processed_files': len([f for f in results if f.get('exists')])
    }

def execute_file_chunk(chunk_data):
    return execute_file_processing(chunk_data['files'])

def execute_web_scraping(urls):
    results = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                results.append({'url': url, 'status': response.status_code,
                                'title': extract_title(response.text),
                                'content_length': len(response.text),
                                'success': True})
            else:
                results.append({'url': url, 'status': response.status_code,
                                'error': f'HTTP {response.status_code}', 'success': False})
        except Exception as e:
            results.append({'url': url, 'error': str(e), 'success': False})
    return {
        'scraped_data': results,
        'total_urls': len(urls),
        'successful_scrapes': len([r for r in results if r['success']]),
        'urls_processed': len(urls)
    }

def execute_scraping_chunk(chunk_data):
    return execute_web_scraping(chunk_data['urls'])

def execute_data_processing(data_items):
    if not isinstance(data_items, list):
        data_items = [data_items]
    processed = []
    for item in data_items:
        try:
            processed_item = {
                'original': item,
                'string_repr': str(item),
                'length': len(str(item)),
                'is_numeric': str(item).replace('.', '').replace('-', '').isdigit(),
                'hash': hash(str(item))
            }
            processed.append(processed_item)
        except Exception as e:
            processed.append({'original': item, 'error': str(e)})
    return {
        'processed_data': processed,
        'total_items': len(data_items),
        'items_processed': len(processed),
        'numeric_items': len([p for p in processed if p.get('is_numeric')])
    }

def execute_data_chunk(chunk_data):
    return execute_data_processing(chunk_data['items'])

def execute_computation(numbers):
    if not isinstance(numbers, list):
        numbers = [numbers]
    processed_numbers = []
    for num in numbers:
        try:
            processed_numbers.append(float(num))
        except:
            continue
    if not processed_numbers:
        return {'error': 'No valid numbers found'}
    total = sum(processed_numbers)
    count = len(processed_numbers)
    average = total / count
    return {
        'sum': total, 'count': count, 'average': average,
        'min': min(processed_numbers), 'max': max(processed_numbers),
        'numbers_processed': len(processed_numbers)
    }

def execute_computation_chunk(chunk_data):
    return execute_computation(chunk_data['numbers'])

def extract_title(html_content):
    try:
        import re
        match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    except:
        pass
    return 'No title found'

# ===== Worker & heartbeat loops =====
def worker_loop():
    global current_task
    logger.info(f"🤖 Worker {NODE_NAME} started polling for tasks")
    while True:
        try:
            if current_task is None:
                task = get_task_from_brain()
                if task:
                    current_task = task
                    logger.info(f"📋 Received task: {task['type']} ({task['task_id']})")
                    result = execute_task(task)
                    submit_task_result(task['task_id'], result, result.get('error'))
                    current_task = None
                else:
                    time.sleep(POLL_INTERVAL)
            else:
                time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error in worker loop: {e}")
            if current_task:
                submit_task_result(current_task['task_id'], None, str(e))
                current_task = None
            time.sleep(POLL_INTERVAL)

def heartbeat_loop():
    while True:
        try:
            send_heartbeat()
            time.sleep(30)
        except Exception as e:
            logger.error(f"❌ Error in heartbeat loop: {e}")
            time.sleep(30)

# ===== Flask routes =====
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'node_id': NODE_ID,
        'name': NODE_NAME,
        'specs': NODE_SPECS,
        'current_task': current_task,
        'stats': stats,
        'uptime': time.time() - psutil.boot_time(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'node_id': NODE_ID, 'timestamp': datetime.now().isoformat()})

# ===== Main =====
if __name__ == '__main__':
    logger.info(f"🖥️ Worker {NODE_NAME} starting on port {NODE_PORT}")
    logger.info(f"🧠 Brain Server: {BRAIN_URL}")

    if register_with_brain():
        logger.info("🤖 Worker ready for tasks")
        threading.Thread(target=worker_loop, daemon=True).start()
        threading.Thread(target=heartbeat_loop, daemon=True).start()
        app.run(host='0.0.0.0', port=NODE_PORT, threaded=True)
    else:
        logger.error("❌ Failed to register with brain server")
        exit(1)
