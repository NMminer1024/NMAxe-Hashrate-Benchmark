# NMAxe Hashrate Benchmark

- A Python-based benchmarking tool for optimizing NMAxe and other Axe series mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency.
- Added an executable file and script to facilitate one-click startup for ordinary users

## Features

- Automated benchmarking of different voltage/frequency combinations
- Temperature monitoring and safety cutoffs
- Power efficiency calculations (J/TH)
- Automatic saving of benchmark results
- Graceful shutdown with best settings retention

## Prerequisites

- Windows 10 and above

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone git@github.com:NMminer1024/NMAxe-Hashrate-Benchmark.git
cd NMAxe-Hashrate-Benchmark
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## CMD options：

### options:
  *  -h, --help               Show this help message and exit
  *  -ip, --axe_ip ,          Target Axe IP address , `required`
  *  -fr, --freq_range ,      ASIC Frequency range, default: 400~625 MHz , `optional`
  *  -fs, --freq_step ,       Frequency step, default: 50 MHz , `optional`
  *  -vr, --vcore_range ,     ASIC Vcore range, default: 1000~1300 mV , `optional`
  *  -vs, --vcore_step ,      Vcore step, default: 25 mV , `optional`
  *  -si, --sample_interval , Sample interval in seconds, default: 10 seconds , `optional`
  *  -bt, --benchmark_time ,  Benchmark time for every round in seconds, default: 600 seconds , `optional`
  *  -st, --stabilize_time ,  Wait stabilize time before benchmark in seconds, default: 240 seconds , `optional`
### Sample Usages:
For expert benchmark：
```
benchmark.exe -ip 192.168.123.56 -fr 400,625 -vr 1100,1300 -fs 25 -vs 50 -bt 600 -st 180
```
For default benchmark：
```
benchmark.exe -ip 192.168.123.56 
```

## Output

The benchmark results are saved to `25-03-13_benchmark_results_<ip_address>.json`, containing:
- Complete test results for all combinations
- Top 5 performing configurations ranked by hashrate
- Top 5 most efficient configurations ranked by J/TH
- For each configuration:
  - Average hashrate (with outlier removal)
  - Temperature readings (excluding initial warmup period)
  - VR temperature readings (when available)
  - Power efficiency metrics (J/TH)
  - Input voltage measurements
  - Voltage/frequency combinations tested


## Benchmarking Process

The tool follows this process:
1. Starts with user-specified or default voltage/frequency
2. Tests each combination for 10 minutes
3. Validates hashrate is within 8% of theoretical maximum
4. Incrementally adjusts settings:
   - Increases frequency if stable
   - Increases voltage if unstable
   - Stops at thermal or stability limits
5. Records and ranks all successful configurations
6. Automatically applies the best performing stable settings
7. Restarts system after each test for stability
8. Allows 180-second stabilization period between tests
9. Stop the benchmark early if the hashrate is not up to standard after 5 minutes

## Data Processing

The tool implements several data processing techniques to ensure accurate results:
- Removes 3 highest and 3 lowest hashrate readings to eliminate outliers
- Excludes first 6 temperature readings during warmup period
- Validates hashrate is within 6% of theoretical maximum
- Averages power consumption across entire test period
- Monitors VR temperature when available
- Calculates efficiency in Joules per Terahash (J/TH)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Please use this tool responsibly. Overclocking and voltage modifications can potentially damage your hardware if not done carefully. Always ensure proper cooling and monitor your device during benchmarking.