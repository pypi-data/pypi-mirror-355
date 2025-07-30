# 🧨 HTTP Prober

<h1 align="center">
  <img src="img/banner.png" alt="http-prober" width="450px">
  <br>
</h1>

<div align="center">

**The http-prober is a Async http statuscode probing CLI tool. Which can check list of urls and print the status code of it.**

</div>

<div align="center">
  
![GitHub last commit](https://img.shields.io/github/last-commit/pevinkumar10/http-prober) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/pevinkumar10/http-prober) [![GitHub license](https://img.shields.io/github/license/pevinkumar10/http-prober)](https://github.com/pevinkumar10/http-prober/blob/main/LICENSE)

</div>

## 🚀 Features:

- Uses Asynchronous programming to enumerate the status code.
- Best modular design with the focus on future improvement and enhancement.
- Improved UI for better UX. 

## 📦 Tool structure:
```
.
├── CHANGELOG.md                            # Change log file.
├── LICENSE                                 # License.
├── README.md                               # Readme file.
├── http-prober.py                          # Http-prober file.
├── http_prober                             # Http-prober package.
│   ├── __init__.py 
│   └── modules                             # Modules for http-prober
│       ├── __init__.py
│       ├── cli                             # CLI modules.
│       │   ├── __init__.py
│       │   └── cli.py                      # CLI handler file.     
│       ├── core.py                         # Core file for HashBrute.
│       ├── prober                          # Prober module.
│       │   ├── __init__.py
│       │   └── prober.py                   
│       ├── tests                           # Test module for http-prober.
│       │   ├── __init__.py
│       │   ├── test_cli.py                 # CLI module test.
│       │   ├── test_prober.py              # Prober module test.
│       │   └── test_utils.py               # Utils suppory module test.
│       └── utils                           # Utility module for support funtions.
│           ├── __init__.py
│           └── utils.py
├── img
│   └── banner.png
├── requirements.txt                        # Dependency for http-prober.
├── setup.py                                # Setup file for http-prober.
└── urls.txt                                # Sample urls for test module.
```

## Installation:

### Install it from PyPi:

For windows:

```bash

pip install Http-Prober

```

For Linux and Unix:

```bash

pipx install Http-Prober
```

This will install the tool in an isolated environment (Recommended). 

### Manual Installation:

- Step 1:
    ```bash
    git clone https://github.com/pevinkumar10/http-prober.git

    cd http-prober
    ```
- Step 2:
    Install dependencies:
  
  ```bash
  pip install -r requirments.txt
  ```
  
    Run:
  
  ```
  python3 -m http-prober
  ```
    
    or

    Install it as a tool by setup.py:

    ```
    pipx install .
    ```

## ⚙️ Options:

<h1 align="center">
  <img src="img/prober-help.png" alt="http-prober" width="450px">
  <br>
</h1>

* `--url` or `-u` : Input url to check status code.
* `--url-list` or `-uL` : List of urls to check status code.
* `--concurrency` or `-c` : Number of concurrency allowed to run simultaniously (default : 100).
* `--verbose` or `-v` : To set verbose mode flag for more detailed output.
* `--help` or `-h`  :  To see all the available options.

## 🧪 Example:

<h1 align="center">
  <img src="img/example-run.png" alt="http-prober" width="450px">
  <br>
  </h1>
  
```bash

    http-prober --url-list urls.txt --verbose

```

## 📄 License

This project is licensed under the [MIT](./LICENSE) License. See the LICENSE file for details.

