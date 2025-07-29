from azure.storage.blob import BlobServiceClient
from pathlib import Path

class AzureBlobStorageHelper:
    def __init__(self, connection_string: str, container_name: str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def upload_file(self, local_path: str, blob_name: str = None):
        blob_name = blob_name or Path(local_path).name
        with open(local_path, "rb") as data:
            self.container_client.upload_blob(name=blob_name, data=data, overwrite=True)

    def download_file(self, blob_name: str, local_path: str):
        with open(local_path, "wb") as file:
            download_stream = self.container_client.download_blob(blob_name)
            file.write(download_stream.readall())

    def list_blobs(self, prefix: str = ""):
        return [blob.name for blob in self.container_client.list_blobs(name_starts_with=prefix)]

    def delete_blob(self, blob_name: str):
        self.container_client.delete_blob(blob_name)

# Example usage (this would go in a separate script or notebook):
# helper = AzureBlobStorageHelper("your-connection-string", "your-container-name")
# helper.upload_file("data.csv")
# helper.download_file("data.csv", "downloaded_data.csv")
# print(helper.list_blobs())
