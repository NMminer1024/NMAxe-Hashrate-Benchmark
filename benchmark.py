
import requests, time, json, ctypes, sys
from src.log import *
from argparse import ArgumentParser, ArgumentTypeError
import re

_VERSION_           = "v0.2.01"
FW_VERSION_REQUIRED = "v2.5.21" # The minimum firmware version required for this tool

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

def compare_versions(version1, version2):
    pattern = re.compile(r'v?(\d+)\.(\d+)\.(\d+)([a-z]?)')
    
    # check if the versions match the pattern
    match1 = pattern.match(version1)
    match2 = pattern.match(version2)
    
    if not match1 or not match2:
        raise ValueError("Invalid version format")
    
    # extract the version parts
    major1, minor1, patch1, suffix1 = match1.groups()
    major2, minor2, patch2, suffix2 = match2.groups()
    
    major1, minor1, patch1 = int(major1), int(minor1), int(patch1)
    major2, minor2, patch2 = int(major2), int(minor2), int(patch2)
    
    # compare the version parts
    if major1 != major2:
        return major1 - major2
    if minor1 != minor2:
        return minor1 - minor2
    if patch1 != patch2:
        return patch1 - patch2
    if suffix1 != suffix2:
        # if one version has a suffix and the other doesn't, the one without the suffix is considered greater
        if not suffix1:
            return -1
        if not suffix2:
            return 1
        return ord(suffix1) - ord(suffix2)
    
    return 0

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

def restart_system(ip):
    try:
        time.sleep(1)
        log_i("Restarting the miner...")
        response = requests.post(f"http://{ip}/api/system/restart", timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        log_w("Miner restarted!")
        return True
    except requests.exceptions.RequestException as e:
        log_e(f"Error restarting the system: {e}")
        return False

def get_system_info(ip):
    try:
        response = requests.get(f"http://{ip}/api/system/info", timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.Timeout:
        log_e(f"Target Axe {ip} is responding timeout")
        return None
    except requests.exceptions.ConnectionError:
        log_e(f"Target Axe {ip} is not reachable")
        return None
    except requests.exceptions.RequestException as e:
        log_e(f"Error fetching system info: {e}")
        return None

def set_system_settings(ip, core_voltage, frequency):
    settings = {
        "coreVoltage": core_voltage,
        "frequency": frequency
    }
    try:
        response = requests.patch(f"http://{ip}/api/system", json=settings, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        log_i(f"System settings update, Vcore: {core_voltage}mV, Frequency: {frequency}MHz")
        return True
    except requests.exceptions.RequestException as e:
        log_e(f"Error setting system settings: {e}")
        return False

def est_benchmark_time(freq_min, freq_max, freq_step, vcore_min, vcore_max, vcore_step, benchmark_time, stabilize_time):
    freq_steps = (freq_max - freq_min) // freq_step + 1
    vcore_steps = (vcore_max - vcore_min) // vcore_step + 1
    total_steps = freq_steps * vcore_steps
    return total_steps, total_steps * benchmark_time + total_steps * stabilize_time  # 'stabilize_time' seconds for system stabilization

def countdown_timer(seconds):
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\r[{get_current_time()}] Benchmark will start after {remaining:3d}s...")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 100 + "\r")
    sys.stdout.flush()

def benchmark(target_ip, sample_interval, benchmark_time):
    log_i("Benchmark start...")
    current_count, total_count = 0, benchmark_time // sample_interval
    hr_sum, eff_sum, pwr_sum, at_sum = 0, 0, 0, 0
    hr_avg, eff_avg, pwr_avg, at_avg = 0, 0, 0, 0
    exp_hr, err_cnt , zero_hr_cnt = 0, 0, 0
    remaining_time = benchmark_time
    while True:
        time.sleep(sample_interval)
        info = get_system_info(target_ip)
        if info == None:
            time.sleep(1)
            err_cnt += 1
            if err_cnt >= 3:
                log_e("Failed to get system info 3 times. Exiting this round...")
                break
            log_e(f"Failed to get system info, {err_cnt}/3")
            continue
        else:
            if info.get('hashRate', 0) == 0:
                zero_hr_cnt += 1
            else :
                zero_hr_cnt = 0

        # If the hashrate is continuous zero for 5 times, exit the benchmark
        if zero_hr_cnt >= 5:
            log_e("Get zero-hashrate 5 times. Exiting this round...")
            break



        current_count += 1
        hr, vt, at, freq, vcore, vbus, ibus = info.get('hashRate', 0), info.get('vrTemp', 0), info.get('temp', 0), info.get('frequency', 0), info.get('coreVoltageActual', 0), info.get('voltage', 0), info.get('current', 0)
        small_core_count, asic_count        = info.get("smallCoreCount", 0), info.get("asicCount", 0)
        exp_hr                              = freq * ((small_core_count * asic_count) / 1000)  # Calculate expected hashrate based on frequency
        # Calculate the sum values
        at_sum                              += at
        hr_sum                              += hr
        eff_sum                             += ((vbus * ibus / 1e6) / (hr / 1e3)) if hr > 0 else 0
        pwr_sum                             += vbus*ibus/1e6
        # Calculate the average values
        hr_avg                              = hr_sum / current_count
        eff_avg                             = eff_sum / current_count
        pwr_avg                             = pwr_sum / current_count
        at_avg                              = at_sum / current_count
        remaining_time                      = (benchmark_time - current_count * sample_interval) if (benchmark_time - current_count * sample_interval) > 0 else 0
        log_i(f"[{target_ip}] [{remaining_time:4d}s] [{(100*current_count/total_count):5.1f}%] | HR: {hr:6.1f}GH/s | EXP HR: {exp_hr:4.0f}GH/s | VT: {vt:3.1f}°C | AT: {at:3.1f}°C | Freq: {freq:3d}MHz | Vcore: {vcore:4d}mV | Vbus: {vbus:5d}mV | Ibus: {ibus:4d}mA |")
        # log_i(f"[{int(remaining_time):4d}s] [{(100*current_count/total_count):5.1f}%] | HR: {hr:6.1f}GH/s | EXP HR: {exp_hr:4.0f}GH/s | VT: {int(vt):3d}°C | AT: {int(at):3d}°C | Freq: {int(freq):3d}MHz | Vcore: {int(vcore):4d}mV | Vbus: {int(vbus):5d}mV | Ibus: {int(ibus):4d}mA |")

        # Check if the benchmark is completed
        if current_count >= total_count:
            break
        # to save time, if the average hashrate is too low, exit the benchmark
        if current_count >= total_count/2 and hr_avg < exp_hr*0.5:
            log_e("The average hashrate is too low. Exiting this round...")
            break

    result = (hr_sum / total_count) >= exp_hr*0.94 # Check if the average hashrate is at least 94% of the expected hashrate
    return result, hr_avg, exp_hr, eff_avg, pwr_avg, at_avg

def save_benchmark_report(target_ip, result):
    try:
        now = datetime.now().strftime('%y-%m-%d')
        filename = f"{now}_benchmark_results_{target_ip}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=4)
        log_i(f"Results saved to {filename}")
    except IOError as e:
        log_e(f"Error saving results to file: {e}")

if __name__ == "__main__":
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    load_logo()
    # Parse arguments
    parser = ArgumentParser(description="=============== NMAxe Benchmark Tool ===============")
    parser.add_argument("-fr", "--freq_range", type=validate_range, default="400,625", help="ASIC Frequency range, default: 400~625 MHz")
    parser.add_argument("-fs ", "--freq_step", type=int, default=50, help="Frequency step, default: 50 MHz")
    parser.add_argument("-vr", "--vcore_range", type=validate_range, default="1000,1300", help="ASIC Vcore range, default: 1000~1300 mV")
    parser.add_argument("-vs", "--vcore_step", type=int, default=25, help="Vcore step, default: 25 mV")
    parser.add_argument("-si", "--sample_interval", type=int, default=10, help="Sample interval in seconds, default: 10 seconds")
    parser.add_argument("-bt", "--benchmark_time", type=int, default=600, help="Benchmark time for every round in seconds, default: 600 seconds")
    parser.add_argument("-st", "--stabilize_time", type=int, default=240, help="Wait stabilize time before benchmark in seconds, default: 240 seconds")
    parser.add_argument("-ip", "--axe_ip", type=str, help= "Target Axe IP address", required=True)
    args = parser.parse_args()

    # Extract the min and max values from the range strings of frequency and vcore
    freq_min_val, freq_max_val   = map(int, args.freq_range.split(','))
    vcore_min_val, vcore_max_val = map(int, args.vcore_range.split(','))
    freq_step       = args.freq_step
    vcore_step      = args.vcore_step
    sample_interval = args.sample_interval
    benchmark_time  = args.benchmark_time
    stabilize_time  = args.stabilize_time
    target_ip       = args.axe_ip   
    # Get the system info to check if the system is online and firmware version supported
    info = get_system_info(target_ip)
    if info == None:
        log_e("Failed to get system info. make sure the target Axe is online and the IP address is correct.")
        sys.exit(1)
        

    # For NMAxe, check if the firmware version is supported
    # For other Axe models, the firmware version check is not required
    board_type = info.get('boardType', "Unknown")
    if "NMAxe" in board_type:
        version = info.get('version', "v0.0.00")
        result = compare_versions(version, FW_VERSION_REQUIRED)
        if result < 0:
            log_w(f"WARNING: The firmware version {version} haven't supported yet. firmware required {FW_VERSION_REQUIRED} at least.")
            sys.exit(1)

    # Estimate the total time cost
    est_cnt, est_time = est_benchmark_time(freq_min_val, freq_max_val, freq_step, vcore_min_val, vcore_max_val, vcore_step, benchmark_time, stabilize_time)
    freq_steps = (freq_max_val - freq_min_val) // freq_step + 1
    # Best case: find stable config at minimum voltage for each frequency
    best_time = freq_steps * (benchmark_time + stabilize_time)
    log_i(f"Freq  range from {freq_min_val}MHz to {freq_max_val}MHz, step: {freq_step}MHz")
    log_i(f"Vcore range from {vcore_min_val}mV to {vcore_max_val}mV, step: {vcore_step}mV")
    log_i(f"Sample every {sample_interval} seconds, estimated time range:")
    log_i(f"       Best case:  {best_time//3600}h {best_time%3600//60}m {best_time%60}s (if all frequencies are stable at minimum voltage)")
    log_i(f"       Worst case: {est_time//3600}h {est_time%3600//60}m {est_time%60}s (if all combinations need to be tested)")
    log_i(f"       Total {est_cnt} combinations maximum, please be patient...")

    benchmark_count = 0
    results = []
    # Calculate total number of voltage steps for more accurate time estimation
    vcore_steps = (vcore_max_val - vcore_min_val) // vcore_step + 1
    freq_steps = (freq_max_val - freq_min_val) // freq_step + 1
    completed_freq_count = 0
    
    for freq in range(freq_min_val, freq_max_val + freq_step, freq_step):#increase the freq if stabel
        vcore_count = 0  # Track voltage steps for current frequency
        for vcore in range(vcore_min_val, vcore_max_val + vcore_step, vcore_step):# increase the vcore if unstabel
            benchmark_count += 1
            vcore_count += 1
            # Calculate remaining time based on current position in loops
            remaining_frequencies = ((freq_max_val - freq) // freq_step) + 1  # Including current frequency
            remaining_vcore_for_current_freq = ((vcore_max_val - vcore) // vcore_step) + 1  # Including current vcore
            # Worst case: complete all remaining vcore for current freq + all vcore for remaining frequencies
            remaining_rounds_max = remaining_vcore_for_current_freq + (remaining_frequencies - 1) * vcore_steps
            # Best case: only one vcore test per remaining frequency
            remaining_rounds_min = remaining_frequencies
            est_time_remaining_max = remaining_rounds_max * (benchmark_time + stabilize_time)
            est_time_remaining_min = remaining_rounds_min * (benchmark_time + stabilize_time)
            # Update estimated total based on actual completion rate
            estimated_total = completed_freq_count + remaining_frequencies
            log_w(f"============================================== rounds [{benchmark_count:3d}/~{est_cnt:3d}], freq [{completed_freq_count:3d}/{freq_steps:3d}], vcore [{vcore_count:2d}/{vcore_steps:2d}], {est_time_remaining_min//3600}h {est_time_remaining_min%3600//60}m ~ {est_time_remaining_max//3600}h {est_time_remaining_max%3600//60}m left =========================================================")
            # Set the system settings
            if set_system_settings(target_ip, vcore, freq) == False:
                log_e("Failed to set system settings. Exiting...")
                sys.exit(1)

            # Restart the system
            restart_system(target_ip)

            # Wait for the system to stabilize
            log_w("Waiting for the system to stabilize...")
            countdown_timer(stabilize_time)  

            # Start the benchmark
            res, avg_hr, exp_hr, avg_eff, avg_pwr, avg_at = benchmark(target_ip, sample_interval, benchmark_time)

            log_w(f"Completed! | Avg HR: {avg_hr:6.1f}GH/s | expected HR: {exp_hr:6.1f}GH/s | Avg EFF: {avg_eff:6.3f}J/TH | Avg PWR: {avg_pwr:6.3f}W")
            if res == True:
                completed_freq_count += 1  # Increment completed frequency count
                log_i(f"Stable setting {vcore}mV, Freq: {freq}MHz, increase freq and retrying...")
                # Save the benchmark results
                result = {
                    "coreVoltage": f"{vcore}mV",
                    "frequency": f"{freq}MHz",
                    "expectedHashRate": f"{round(exp_hr, 1)}GH/s",
                    "averageHashRate": f"{round(avg_hr, 1)}GH/s",
                    "averageTemperature": f"{round(avg_at, 1)}'C",  # average asic temperature
                    "efficiencyJTH": f"{round(avg_eff, 2)}J/TH",
                    "averagePower": f"{round(avg_pwr, 2)}W"
                }
                results.append(result)
                save_benchmark_report(target_ip, results)
                break
            else:   
                log_w(f"Unstable settings {vcore}mV, Freq: {freq}MHz, increase Vcore and retrying...")
                time.sleep(1)

    log_i("Benchmark completed!")
    max_avg_hr, best_result = 0, None
    # Find the best result
    log_i("Results:")
    for i, result in enumerate(results):
        log_i(f"[{i+1}] {result}")
        avg_hr = float(result['averageHashRate'].replace('GH/s', ''))
        if avg_hr > max_avg_hr:
            max_avg_hr = avg_hr
            best_result = result

    # Print the best result
    if best_result:
        log_i("Best Result:")
        log_i(f"{best_result}")
        log_i("Use the best result to set the system settings.")
        # Set the best system settings
        set_system_settings(target_ip, int(best_result['coreVoltage'].replace('mV', '')), int(best_result['frequency'].replace('MHz', '')))
        # Restart the system
        restart_system(target_ip)
    log_i("Exiting...")





