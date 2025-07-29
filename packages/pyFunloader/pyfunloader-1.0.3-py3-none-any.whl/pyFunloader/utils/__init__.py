from datetime import datetime

import os

def parse_file_name(url: str):
    
    file_name = os.path.basename(url)

    if (index := file_name.find("&")) != -1:
        file_name = file_name[:index]
    
    if (index := file_name.find("?")) != -1:
        file_name = file_name[:index]
    
    if (index := file_name.find("=")) != -1:
        file_name = file_name[:file_name.find("=")]

    file_name = file_name[:255]
    
    if not file_name:
        file_name = "unnamed"

    return file_name

def humanize(data, time=False):
    hit_limit = 1024 if not time else 60
    magnitudes = ("bytes", "Kb", "Mb", "Gb", "Tb", "Pb") if not time \
        else ("seconds", "minutes", "hours", "days", "months", "years")

    m = 0
    while data > hit_limit and m < len(magnitudes):
        data /= hit_limit
        m += 1

    return f"{data:.2f} {magnitudes[m]}" if not time else f"{int(data)} {magnitudes[m]}"

def parse_progress_details(received_data: int, total_data: int, start_time: datetime):
    speed = received_data / max((datetime.now() - start_time).seconds, 1)

    return (
        humanize((total_data - received_data) / speed, time=True) or 0, # estimate
        humanize(received_data / speed, time=True) or 0, # time passed
        humanize(speed),
        round(
            min(
                (received_data / total_data) * 100, 100
            ), 2
        ) or 0 # percentage
    )