import requests, time, json, signal, sys
from src.log import *
from argparse import ArgumentParser, ArgumentTypeError

_VERSION_ = "v0.1.01"

def load_logo():  
    log_p("===========================================DISCLAIMER=================================================")
    log_e("This tool will stress test your NMAxe by running it at various voltages and frequencies.")
    log_e("While safeguards are in place, running hardware outside of standard parameters carries inherent risks.")
    log_e("Use this tool at your own risk. The author(s) are not responsible for any damage to your hardware.")
    log_e("NOTE: Ambient temperature significantly affects these results. The optimal settings found may not")
    log_e("work well if room temperature changes substantially. Re-run the benchmark if conditions change.")      
    log_p("======================================================================================================")                                                                          
    log_i("            ___          ___         ")
    log_i("           /\\__\\        /\\__\     ")
    log_i("          /::|  |      /::|  |       ")
    log_i("         /:|:|  |     /:|:|  |       ")
    log_i("        /:/|:|  |__  /:/|:|__|__     ")
    log_i("       /:/ |:| /\\__\\/:/ |::::\\__\\")
    log_i("       \\/__|:|/:/  /\\/__/~~/:/  /  ")
    log_i("           |:/:/  /       /:/  /     ")
    log_i("           |::/  /       /:/  /      ")
    log_i("           /:/  /       /:/  /       ")
    log_i("           \\/__/        \\/__/      ")
    log_i(f"{_VERSION_}".center(40, '-'))

def validate_range(value):
    try:
        # check if the string contains exactly one comma
        if value.count(',') != 1:
            raise ArgumentTypeError(f"Invalid range format: {value}. Expected format: number1,number2")
        # split the string into two numbers
        min_val, max_val = map(int, value.split(','))
        # check if the first number is less than the second number
        if min_val >= max_val:
            raise ArgumentTypeError(f"Invalid range: {value}. The first number must be less than the second number.")
        return value
    except ValueError:
        raise ArgumentTypeError(f"Invalid range format: {value}. Expected format: number1,number2")

def get_system_info(ip):
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(f"http://{ip}/api/system/info", timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.Timeout:
            log_e(f"Timeout while fetching system info. Attempt {attempt + 1} of {retries}.")
        except requests.exceptions.ConnectionError:
            log_e(f"Connection error while fetching system info. Attempt {attempt + 1} of {retries}.")
        except requests.exceptions.RequestException as e:
            log_e(f"Error fetching system info: {e}")
            break
        time.sleep(5)  # Wait before retrying
    return None

def est_benchmark_time(freq_min, freq_max, freq_step, vcore_min, vcore_max, vcore_step, sample_interval, benchmark_time=600):
    freq_steps = (freq_max - freq_min) // freq_step + 1
    log_i(f"Total frequency steps: {freq_steps}")
    vcore_steps = (vcore_max - vcore_min) // vcore_step + 1
    log_i(f"Total vcore steps: {vcore_steps}")
    total_steps = freq_steps * vcore_steps
    return total_steps * benchmark_time



if __name__ == "__main__":
    load_logo()
    # Parse arguments
    parser = ArgumentParser(description="=============== NMAxe Benchmark Tool ===============")
    parser.add_argument("-fr", "--freq_range", type=validate_range, default="400,625", help="ASIC Frequency range, default: 400~625 MHz")
    parser.add_argument("-fs ", "--freq_step", type=int, default=25, help="Frequency step, default: 25 MHz")
    parser.add_argument("-vr", "--vcore_range", type=validate_range, default="1000,1300", help="ASIC Vcore range, default: 1000~1300 mV")
    parser.add_argument("-vs", "--vcore_step", type=int, default=25, help="Vcore step, default: 25 mV")
    parser.add_argument("-si", "--sample_interval", type=int, default=10, help="Sample interval in seconds, default: 10 seconds")
    parser.add_argument("-bt", "--benchmark_time", type=int, default=600, help="Benchmark time in seconds, default: 600 seconds")
    parser.add_argument("-ip", "--axe_ip", type=str, help= "Target Axe IP address", required=True)
    args = parser.parse_args()

    # Extract the min and max values from the range strings of frequency and vcore
    freq_min_val, freq_max_val   = map(int, args.freq_range.split(','))
    vcore_min_val, vcore_max_val = map(int, args.vcore_range.split(','))
    freq_step       = args.freq_step
    vcore_step      = args.vcore_step
    sample_interval = args.sample_interval
    benchmark_time  = args.benchmark_time

    log_i(f"Freq  range from {freq_min_val}MHz to {freq_max_val}MHz, step: {freq_step}MHz")
    log_i(f"Vcore range from {vcore_min_val}mV to {vcore_max_val}mV, step: {vcore_step}mV")
    log_i(f"Sample every {sample_interval} seconds")

    est_time = est_benchmark_time(freq_min_val, freq_max_val, freq_step, vcore_min_val, vcore_max_val, vcore_step, sample_interval, benchmark_time)
    log_i(f"Estimated total benchmark time about {est_time//3600} hours {est_time%3600//60} minutes, please be patient...")
    sys.exit(0)



    while True:
        info = get_system_info(args.axe_ip)
        # log_i(json.dumps(info, indent=4))
        time.sleep(5)


