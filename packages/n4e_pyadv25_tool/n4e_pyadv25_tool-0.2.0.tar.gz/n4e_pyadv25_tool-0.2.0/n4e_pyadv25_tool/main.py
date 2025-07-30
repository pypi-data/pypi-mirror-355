import json
import pandas as pd


def export_hosts_to_excel(json_file: str, excel_file: str = "hosts_info.xlsx") -> None:
    """
    Читает JSON-файл Zabbix, извлекает имя и IP хостов, сохраняет в Excel-файл.
    
    :param json_file: путь к JSON-файлу Zabbix
    :param excel_file: путь к итоговому Excel-файлу
    """
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    hosts_data = []
    for host in data["zabbix_export"]["hosts"]:
        host_info = {
            "name": host["name"],
            "ip": host["interfaces"][0]["ip"],
        }
        hosts_data.append(host_info)

    df = pd.DataFrame(hosts_data)
    df.to_excel(excel_file, index=False)

    print(f"Данные успешно сохранены в файл {excel_file}")


if __name__ == "__main__":
    export_hosts_to_excel("zbx_export_hosts.json")
