"""Functions for Azure Embedding/Chat Models."""


def resolve_azure_deployment(deployment: str, dict_: dict[str, str]) -> str:
    """Resolve Azure deployment name.

    Args:
        deployment: Azure deployment name
        dict_: dictionary mapping from env vars

    Returns:
        azure deployment name
    """
    deployment = deployment.lower()
    if deployment not in dict_:
        raise ValueError(f"Deployment '{deployment}' not found.")
    return dict_[deployment]
