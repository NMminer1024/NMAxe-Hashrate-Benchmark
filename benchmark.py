import requests, time, json, signal, sys, argparse



bitaxe_ip = "http://192.168.123.2"




while True:
    response = requests.get(f"{bitaxe_ip}/#/settings", timeout=10)
    response.raise_for_status()
    system_info = response.json()
    print(system_info)


# response = requests.post(f"{bitaxe_ip}/api/system/restart", timeout=10)
# response.raise_for_status()
# print(system_info)