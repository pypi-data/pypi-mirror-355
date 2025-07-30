import json
from .content_config import ContentConfig
import json
import requests
import urllib3
import warnings

# Disable https warnings if the http certificate is not valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

class ContentDocument:

    def __init__(self, content_config):

        if isinstance(content_config, ContentConfig):
            self.repo_url = content_config.repo_url
            self.repo_id = content_config.repo_id
            self.logger = content_config.logger
            self.encoded_credentials = content_config.encoded_credentials
            self.authorization_repo = content_config.authorization_repo
        else:
            raise TypeError("ContentConfig class object expected")


    # Delete document in Mobius based on document_id
    def delete(self, document_id): 

        delete_url = self.repo_url + "/repositories/" + self.repo_id + "/documents?documentid=" + document_id

        # Headers
        headers = {self.authorization_repo: f'Basic {self.encoded_credentials}'
        }

        self.logger.info("--------------------------------")
        self.logger.debug("Method : delete")
        self.logger.info(f"Mobius Delete URL : {delete_url}")
        self.logger.debug(f"Headers : {json.dumps(headers)}")

        try:
           response = requests.delete(delete_url, headers=headers, verify=False)
           self.logger.debug(response.text)

           return response.status_code

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise ValueError(f"An error occurred: {e}")