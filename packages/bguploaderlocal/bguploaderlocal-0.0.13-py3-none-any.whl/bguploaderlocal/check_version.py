import requests
import sys
import os
import time
from packaging import version

try:
	from importlib.metadata import version as get_installed_version
except ImportError:
	from importlib_metadata import version as get_installed_version  # type: ignore [python < 3.8]

PACKAGE_NAME = "bguploaderlocal"
CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache', PACKAGE_NAME)
CACHE_FILE = os.path.join(CACHE_DIR, 'last_version_check')
CHECK_INTERVAL = 86400  # 24 hours in seconds

def should_check_version():
	try:
		# Create cache dir if it doesn't exist
		os.makedirs(CACHE_DIR, exist_ok=True)
		# Read last check time
		if os.path.exists(CACHE_FILE):
			with open(CACHE_FILE, 'rt') as f:
				last_check = float(f.read())
				if time.time() - last_check < CHECK_INTERVAL:
					return False
		# Write current time
		with open(CACHE_FILE, 'wt') as f:
			f.write(str(time.time()))
	except Exception:
		pass
	return True

def check_latest_version():
	try:
		current_version = get_installed_version(PACKAGE_NAME)
		pypi_url = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
		resp = requests.get(pypi_url, timeout=1.5)
		if resp.status_code == 200:
			latest_version = resp.json()["info"]["version"]
			if version.parse(latest_version) > version.parse(current_version):
				print(f"\n\033[93mNOTICE:\033[0m A new version of '{PACKAGE_NAME}' is available: {latest_version} (you have {current_version})")
				print(f"Upgrade with: pip install --upgrade {PACKAGE_NAME}\n")
	except Exception:
		pass