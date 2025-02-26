import subprocess
import json

def get_pod_ips(label_selector= None, namespace=None):
    """
    Get the IP addresses of all pods with the given label selector.

    Args:
        label_selector (str): The label selector to filter pods.

    Returns:
        list: A list of IP addresses of the pods.
    """
    if label_selector:
        command = ["microk8s", "kubectl", "get", "pods", "-l", label_selector, "-o", "json"]
    else:
        command = ["microk8s", "kubectl", "get", "pods", "-o", "json"]

    if namespace:
        command.extend(["-n", namespace])
    try:
        # Run the kubectl command to get pod details in JSON format
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the JSON output
        pods = json.loads(result.stdout)

        # Extract the IP addresses
        pod_ips = [pod["status"]["podIP"] for pod in pods["items"]]

        return pod_ips

    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl command: {e}")
        return []
    

def main():
    # Get the IP addresses of the pods
    pod_ips = get_pod_ips(namespace="ollama")

    # Print each IP address on a new line
    for ip in pod_ips:
        print(ip)

if __name__ == "__main__":
    main()