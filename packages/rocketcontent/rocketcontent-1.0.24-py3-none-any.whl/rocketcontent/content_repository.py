import json
import requests
import urllib3
import warnings
import base64

from .content_config import ContentConfig

from urllib.parse import quote

# Disable https warnings if the http certificate is not valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

class ContentRepository:
    
    VALID_DEBUG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, content_config):

        if isinstance(content_config, ContentConfig):
            self.repo_url = content_config.repo_url
            self.repo_id = content_config.repo_id
            self.logger = content_config.logger
            self.encoded_credentials = content_config.encoded_credentials
            self.base_url = content_config.base_url
            self.repo_id_enc = content_config.repo_id_enc
            self.authorization_repo = content_config.authorization_repo

            host_and_port = self.base_url.lower().replace("https://","").replace("http://","")

            #admin_credentials = content_config.repo_name + ":" + host_and_port + ":" + content_config.repo_user + ":" +  content_config.repo_pass

            admin_credentials = "ENC(ZjE1YWE4ZTUtM2QzYS00ZDJiLTkyNzktZGZjNmI5ZjdjZDViL3Zkcm5ldGRz):" + host_and_port + ":" + content_config.repo_name  + ":" + content_config.repo_user + ":" +  content_config.repo_pass
            
            # var authorizationToken = btoa(vdrrepository + ":" + host + ":" + port + ":" + docServerName + ":" + userid + ":" + password);
            # vdrrepository:vdrnet8.asg.com:8080:MobiusDemo:demoadmin:mobius
            #"vdrcontentsource:" + hostName + ":" + portNumber + ":" + userid + ":" + password)            
            self.encoded_admin_credentials = base64.b64encode(admin_credentials.encode('utf-8')).decode('utf-8')

        else:
            raise TypeError("ContentConfig class object expected")


    def get_content_classes(self, output_file="content_classes.json"):
        """
        Retrieves the content classes from the Mobius server and saves them to a JSON file.

        Args:
            output_file (str, optional): Output file name. Defaults to "content_classes.json".
        """
        # Make the GET request
        content_classes_url= self.repo_url + "/repositories/" + self.repo_id + "/recordtypes" 
         
        self.logger.info("--------------------------------")
        self.logger.debug("Method : get_content_classes")
        self.logger.info(f"Content Classes URL : {content_classes_url}")
        self.logger.info(f"File : {output_file}")

        return self.__get_cc_inx(content_classes_url, output_file)


    def get_indexes(self, output_file="index.json"):
        """
        Retrieves the index from the Mobius server and saves them to a JSON file.

        Args:
            output_file (str, optional): Output file name. Defaults to "index.json".
        """    
        indexes_url= self.repo_url + "/indexes?repositoryid=" + self.repo_id

        self.logger.info("--------------------------------")
        self.logger.debug("Method : get_indexes")
        self.logger.info(f"Indexes URL : {indexes_url}")
        self.logger.info(f"File : {output_file}")

        return self.__get_cc_inx(indexes_url, output_file)

    def __get_cc_inx(self, url, output_file="content_classes.json", verify_ssl=False):
        """
        Performs a GET request to the provided URL and saves the JSON response to a file.

        Args:
            url (str): The URL to perform the GET request.
            output_file (str, optional): Output file name. Defaults to "content_classes.json".
            verify_ssl (bool, optional): Verify SSL certificate. Defaults to True.
        """
        try:
            response = requests.get(url, verify=False)  # Make a GET request to the specified URL
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()  # Parse the JSON response

            # Parse the JSON response
            data = response.json()

            # Save the JSON data to the output file
            with open(output_file, "w") as file:
                json.dump(data, file, indent=2)

        except requests.exceptions.RequestException as e:
            # Handle request exceptions
            self.logger.error(f"Doing the request: {e}")
        except json.JSONDecodeError:
            # Handle JSON decoding errors
            self.logger.error("Invalid JSON response.")
        except Exception as e:
            # Handle any other unexpected errors
            self.logger.error(f"An unexpected error occurred: {e}")         

    #--------------------------------------------------------------
    # Create Content Class definition
    def create_content_class(self, content_class_json):
        try:

            content_class_definition_url= self.base_url + self.repo_id_ENC + "/reports"
    
            headers = {
                'Accept': 'application/vnd.asg-mobius-admin-reports.v3+json,application/vnd.asg-mobius-admin-reports.v2+json,application/vnd.asg-mobius-admin-reports.v1+json',
                'Content-Type': 'application/vnd.asg-mobius-admin-report.v1+json',
                'Authorization': f'Basic {self.encoded_credentials}'
                }

            self.logger.info("--------------------------------")
            self.logger.debug("Method : create_content_class")
            self.logger.info(f"Content Class definition URL : {content_class_definition_url}")
            self.logger.debug(f"Headers : {json.dumps(headers)}")
            self.logger.debug(f"Body : {json.dumps(content_class_json)}")
                
            # Send the request
            response = requests.post(content_class_definition_url, headers=headers, data=content_class_json, verify=False)
            
            self.logger.debug(response.text)

            return response.status_code
         
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    #--------------------------------------------------------------
    # Create Index Group Definition
    def create_index_group(self, index_group_json):
        try:
            index_group_definition_url= self.base_url + self.repo_id_ENC + "/topicgroups"
    
            headers = {
                'Accept': 'application/vnd.asg-mobius-admin-topic-group.v1+json',
                'Content-Type': 'application/vnd.asg-mobius-admin-topic-group.v1+json',
                'Authorization': f'Basic {self.encoded_credentials}'
                }

            self.logger.info("--------------------------------")
            self.logger.debug("Method : create_index_group")
            self.logger.info(f"Index Group definition URL : {index_group_definition_url}")
            self.logger.debug(f"Headers : {json.dumps(headers)}")
            self.logger.debug(f"Body : {json.dumps(index_group_json)}")
                
            # Send the request
            response = requests.post(index_group_definition_url, headers=headers, data=index_group_json, verify=False)
            
            self.logger.debug(response.text)
        
            return response.status_code
        
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")