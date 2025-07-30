import json
from pprint import pprint

import pandas as pd

json_file_name = "zbx_export_hosts.json"
# шаг 1: чтение json файла
with open(json_file_name, "r", encoding="utf-8") as file:
    data = json.load(file)

# шаг 2: извлечение данных
hosts_data = []
for host in data["zabbix_export"]["hosts"]:
    host_info = {
        "name": host["name"],
        "ip": host["interfaces"][0]["ip"],
    }
    hosts_data.append(host_info)

# шаг 3: преобразование данных в dataframe
df = pd.DataFrame(hosts_data)

# шаг 4: экспорт в файл xlsx
df.to_excel("hosts_info.xlsx", index=False)

print("Данные успешно сохранены в файл hosts_info.xlsx")

