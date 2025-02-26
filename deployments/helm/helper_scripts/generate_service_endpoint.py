import sys

def generate_service_endpoint(
        service_name="service_name",
        namespace="default",
        port=80
):
    url = f"http://{service_name}.{namespace}.svc.cluster.local:{port}"
    return url


if __name__ == "__main__":
    if len(sys.argv) > 1:
        service_name = sys.argv[1]
    else:
        service_name = "service_name"

    if len(sys.argv) > 2:
        namespace = sys.argv[2]
    else:
        namespace = "default"

    if len(sys.argv) > 3:
        port = sys.argv[3]
    else:
        port = 80

    # Generate URL
    url = generate_service_endpoint(service_name, namespace, port)
    print(url)