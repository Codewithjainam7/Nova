"""
Skill: system_telemetry
Description: Gathers real-time CPU, RAM, battery, and disk statistics.
"""
import psutil

def run(**kwargs):
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat_pct = battery.percent if battery else None
    power_plugged = battery.power_plugged if battery else None
    
    return {
        "status": "SUCCESS",
        "cpu_percent": cpu,
        "ram_percent": ram,
        "battery_percent": bat_pct,
        "charging": power_plugged
    }
