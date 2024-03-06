# VMware VM Inventory Fetcher

This Python script allows you to fetch the inventory of virtual machines from VMware vCenter, including custom attributes.

## Usage

1. Clone the repository:

```bash
git clone https://github.com/your-username/vmware-vm-inventory-fetcher.git
cd vmware-vm-inventory-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the script:
```bash
python get_details.py
```
4. Follow the prompts to enter your vCenter hostname/IP, username, and password.
5. Optionally, you can choose to fetch custom attributes as well.
6. The script will fetch the VM inventory and save it to vminfo.json in the current directory.

## Configuration

You can configure the script by modifying the following variables in get_details.py:

- **ignore_ssl:** Set to True if using self-signed certificates.
- **fetch_custom_attributes:** Set to True if you want to fetch custom attributes.
