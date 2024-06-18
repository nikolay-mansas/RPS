# For windows

1. Installing python 3.11
https://www.python.org/downloads/release/python-3119/

2. Installing the project and unzip it
https://github.com/nikolay-mansas/RPS/archive/refs/heads/master.zip

3. After installation, open the console, open the directory where the project folder is located via cd. Change the config.py in folder server optional.
```
cd server && pip install -r requirements.txt && python server.py
```


# For linux

```
sudo apt-get update && sudo apt-get install git python3 python3-pip
```
```
git clone https://github.com/nikolay-mansas/RPS.git
```
```
cd RPS && cd server && pip3 install -r requirements.txt
```
Change the config.py in folder server optional.
```
python3 server.py
```