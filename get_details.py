import ssl
import json
import logging
import datetime
from pyVim import connect
from getpass import getpass
from pyVmomi import vim, vmodl, VmomiSupport


def connect_to_vmware(host, username, password, ignore_ssl):
    """
    Connect to VMware vCenter server.
    """
    context = ssl.create_default_context()

    if ignore_ssl:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        vmware_connect = connect.SmartConnect(
            host=host,
            user=username,
            pwd=password,
            sslContext=context,
        )
        return vmware_connect
    except vmodl.MethodFault as error:
        logging.error(f"Failed to connect to VMware vCenter: {error}")
        return None


def get_vm_inventory(content, fetch_custom_attributes):
    """
    Retrieve VM inventory information.
    """
    logging.info("Fetching VM inventory")
    start_time = datetime.datetime.now()

    properties = [
        "name",
        "config.annotation",
        "config.hardware",
        "config.guestFullName",
        "summary.config.guestId",
        "summary.runtime.powerState",
        "summary.storage",
        "summary.quickStats",
        "guest.net",
        "config.files",
        "config.changeVersion",
        "config.version",
        "config.hardware.device",
        "guest.toolsStatus",
        "guest.hostName",
        "guest.ipAddress",
        "runtime.host",
        "runtime.connectionState",
    ]

    if fetch_custom_attributes:
        properties.append("summary.customValue")

    virtual_machines = batch_fetch_properties(
        content,
        vim.VirtualMachine,
        properties,
    )

    if fetch_custom_attributes:
        virtual_machines = process_custom_attributes(virtual_machines, content)

    fetch_time = datetime.datetime.now() - start_time
    logging.info(f"Fetched VM inventory in {fetch_time}")

    return virtual_machines


def batch_fetch_properties(content, objtype, properties):
    """
    Batch fetch properties for a given object type.
    """
    view_ref = content.viewManager.CreateContainerView(
        container=content.rootFolder, type=[objtype], recursive=True
    )

    try:
        PropertyCollector = vmodl.query.PropertyCollector
        property_spec = PropertyCollector.PropertySpec()
        property_spec.type = objtype
        property_spec.pathSet = properties

        traversal_spec = PropertyCollector.TraversalSpec()
        traversal_spec.name = "traverseEntities"
        traversal_spec.path = "view"
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__

        obj_spec = PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True
        obj_spec.selectSet = [traversal_spec]

        filter_spec = PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        props = content.propertyCollector.RetrieveContents([filter_spec])
    finally:
        view_ref.Destroy()

    results = {}
    for obj in props:
        properties = {}
        properties["obj"] = obj.obj
        properties["id"] = obj.obj._moId

        for prop in obj.propSet:
            properties[prop.name] = prop.val

        results[obj.obj._moId] = properties

    return results


def process_custom_attributes(virtual_machines, content):
    """
    Process custom attributes for virtual machines.
    """
    all_custom_attributes = {}
    if content.customFieldsManager and content.customFieldsManager.field:
        all_custom_attributes.update(
            {
                f.key: f.name
                for f in content.customFieldsManager.field
                if f.managedObjectType in (vim.VirtualMachine, None)
            }
        )

    for vm_id, vm_properties in virtual_machines.items():
        if "summary.customValue" in vm_properties:
            custom_values = vm_properties["summary.customValue"]
            processed_custom_values = {}
            for custom_value in custom_values:
                key = custom_value.key
                value = custom_value.value
                if key in all_custom_attributes:
                    processed_custom_values[all_custom_attributes[key]] = value
                else:
                    processed_custom_values[key] = value
            vm_properties["summary.customValue"] = processed_custom_values

    return virtual_machines


def save_to_json(data):
    """
    Save VM inventory data to JSON file.
    """
    with open("vminfo.json", "w", encoding="utf-8") as f:
        json.dump(data, f, cls=VmomiSupport.VmomiJSONEncoder, indent=4)


def main():
    logging.basicConfig(level=logging.INFO)

    host = input("Enter vCenter hostname/IP: ")
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    ignore_ssl = True  # Set to True for self-signed certificates
    fetch_custom_attributes = True

    connection = connect_to_vmware(host, username, password, ignore_ssl)
    if connection:
        content = connection.RetrieveContent()
        vm_inventory_data = get_vm_inventory(content, fetch_custom_attributes)
        save_to_json(vm_inventory_data)
        logging.info("VM inventory data saved to vminfo.json")
    else:
        logging.error("Failed to connect to VMware vCenter.")


if __name__ == "__main__":
    main()
