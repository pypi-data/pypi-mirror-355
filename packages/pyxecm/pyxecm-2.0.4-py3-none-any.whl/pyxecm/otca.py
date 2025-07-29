"""OTCA stands for Content Aviator and is an OpenText offering for LLMM-based Agentic AI.

The REST API is documented here (OT internal):
https://confluence.opentext.com/display/CSAI/LLM+Project+REST+APIs

"""

__author__ = "Dr. Marc Diefenbruch"
__copyright__ = "Copyright (C) 2024-2025, OpenText"
__credits__ = ["Kai-Philip Gatzweiler"]
__maintainer__ = "Dr. Marc Diefenbruch"
__email__ = "mdiefenb@opentext.com"

import hashlib
import json
import logging
import platform
import sys
import time
from importlib.metadata import version

import requests

from pyxecm.otcs import OTCS

APP_NAME = "pyxecm"
APP_VERSION = version("pyxecm")
MODULE_NAME = APP_NAME + ".otca"

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
OS_INFO = f"{platform.system()} {platform.release()}"
ARCH_INFO = platform.machine()
REQUESTS_VERSION = requests.__version__

USER_AGENT = (
    f"{APP_NAME}/{APP_VERSION} ({MODULE_NAME}/{APP_VERSION}; "
    f"Python/{PYTHON_VERSION}; {OS_INFO}; {ARCH_INFO}; Requests/{REQUESTS_VERSION})"
)

REQUEST_HEADERS = {"User-Agent": USER_AGENT, "accept": "application/json", "Content-Type": "application/json"}

REQUEST_TIMEOUT = 60
REQUEST_RETRY_DELAY = 20
REQUEST_MAX_RETRIES = 2

default_logger = logging.getLogger(MODULE_NAME)


class OTCA:
    """Interact with Content Aviator REST API."""

    logger: logging.Logger = default_logger

    _config: dict
    _context = ""
    _embed_token: str | None = None
    _chat_token: str | None = None

    def __init__(
        self,
        chat_url: str,
        embed_url: str,
        otds_url: str,
        client_id: str,
        client_secret: str,
        otcs_object: OTCS,
        synonyms: list | None = None,
        inline_citation: bool = True,
        logger: logging.Logger = default_logger,
    ) -> None:
        """Initialize the Content Aviator (OTCA) object.

        Args:
            chat_url (str):
                The Content Aviator base URL for chat.
            embed_url (str):
                The Content Aviator base URL for embedding.
            otds_url (str):
                The OTDS URL.
            client_id (str):
                The Core Share Client ID.
            client_secret (str):
                The Core Share client secret.
            otcs_object (OTCS):
                The OTCS object.
            synonyms (list):
                List of synonyms that are used to generate a better response to the user.
            inline_citation (bool):
                Enable/Disable citations in the answers.
            logger (logging.Logger, optional):
                The logging object to use for all log messages. Defaults to default_logger.

        """

        if logger != default_logger:
            self.logger = logger.getChild("otca")
            for logfilter in logger.filters:
                self.logger.addFilter(logfilter)

        otca_config = {}

        otca_config["chatUrl"] = chat_url + "/v1/chat"
        otca_config["searchUrl"] = chat_url + "/v1/context"
        otca_config["embedUrl"] = embed_url + "/v1/embeddings"
        otca_config["clientId"] = client_id
        otca_config["clientSecret"] = client_secret
        otca_config["otdsUrl"] = otds_url

        otca_config["synonyms"] = synonyms if synonyms else []
        otca_config["inlineCitation"] = inline_citation

        self._config = otca_config
        self.otcs_object = otcs_object

    # end method definition

    def config(self) -> dict:
        """Return the configuration dictionary.

        Returns:
            dict: Configuration dictionary

        """

        return self._config

    # end method definition

    def get_context(self) -> str:
        """Return the current chat context (history).

        Returns:
            str:
                Chat history.

        """

        return self._context

    # end method definition

    def get_synonyms(self) -> list:
        """Get configured synonyms.

        Returns a list of lists. The inner lists are the set
        of terms that are synonyms of each other.

        Args:
            synonyms (list):
                List of synonyms that are used to generate a better response to the user.

        """

        return self.config()["synonyms"]

    # end method definition

    def add_synonyms(self, synonyms: list) -> None:
        """Add synonyms to the existing synonyms.

        Args:
            synonyms (list):
                List of synonyms that are used to generate a better response to the user.

        """

        self.config()["synonyms"].extend(synonyms)

    # end method definition

    def request_header(self, service_type: str = "chat", content_type: str = "application/json") -> dict:
        """Return the request header used for requests.

        Consists of Bearer access token and Content Type

        Args:
            service_type (str, optional):
                Service type for which the header should be returned.
                Either "chat" or "embed". "chat" is the default.

            content_type (str, optional):
                Custom content type for the request.
                Typical values:
                * application/json - Used for sending JSON-encoded data
                * application/x-www-form-urlencoded - The default for HTML forms.
                  Data is sent as key-value pairs in the body of the request, similar to query parameters.
                * multipart/form-data - Used for file uploads or when a form includes non-ASCII characters

        Returns:
            dict: The request header values.

        """

        request_header = REQUEST_HEADERS

        if content_type:
            request_header["Content-Type"] = content_type

        if service_type == "chat" and self._chat_token is not None:
            request_header["Authorization"] = "Bearer {}".format(self._chat_token)

        elif service_type == "embed" and self._embed_token is not None:
            request_header["Authorization"] = "Bearer {}".format(self._embed_token)

        return request_header

    # end method definition

    def do_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        data: dict | list | None = None,
        json_data: dict | None = None,
        files: dict | None = None,
        timeout: int | None = REQUEST_TIMEOUT,
        show_error: bool = True,
        failure_message: str = "",
        success_message: str = "",
        max_retries: int = REQUEST_MAX_RETRIES,
        retry_forever: bool = False,
    ) -> dict | None:
        """Call an Content Aviator REST API in a safe way.

        Args:
            url (str):
                URL to send the request to.
            method (str, optional):
                HTTP method (GET, POST, etc.). Defaults to "GET".
            headers (dict | None, optional):
                Request headers. Defaults to None.
            data (dict | None, optional):
                Request payload. Defaults to None.
            json_data (dict | None, optional):
                Request payload for the JSON parameter. Defaults to None.
            files (dict | None, optional):
                Dictionary of {"name": file-tuple} for multipart encoding upload.
                The file-tuple can be a 2-tuple ("filename", fileobj) or a 3-tuple
                ("filename", fileobj, "content_type").
            timeout (int | None, optional):
                Timeout for the request in seconds. Defaults to REQUEST_TIMEOUT.
            show_error (bool, optional):
                Whether or not an error should be logged in case of a failed REST call.
                If False, then only a warning is logged. Defaults to True.
            failure_message (str, optional):
                Specific error message. Defaults to "".
            success_message (str, optional):
                Specific success message. Defaults to "".
            max_retries (int, optional):
                Number of retries on connection errors. Defaults to REQUEST_MAX_RETRIES.
            retry_forever (bool, optional):
                Whether to wait forever without timeout. Defaults to False.

        Returns:
            dict | None:
                Response of Content Aviator REST API or None in case of an error.

        """

        retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    data=data,
                    json=json_data,
                    files=files,
                    headers=headers,
                    timeout=timeout,
                )

                if response.ok:
                    if success_message:
                        self.logger.debug(success_message)
                    return self.parse_request_response(response)
                # Check if Session has expired - then re-authenticate and try once more
                elif response.status_code == 401 and retries == 0:
                    self.logger.debug("Session has expired - try to re-authenticate...")
                    self.authenticate_chat()
                    retries += 1
                else:
                    # Handle plain HTML responses to not pollute the logs
                    content_type = response.headers.get("content-type", None)
                    response_text = "HTML content (see debug log)" if content_type == "text/html" else response.text

                    if show_error:
                        self.logger.error(
                            "%s; status -> %s; error -> %s",
                            failure_message,
                            response.status_code,
                            response_text,
                        )
                    else:
                        self.logger.warning(
                            "%s; status -> %s; warning -> %s",
                            failure_message,
                            response.status_code,
                            response_text,
                        )

                    if content_type == "text/html":
                        self.logger.debug(
                            "%s; status -> %s; warning -> %s",
                            failure_message,
                            response.status_code,
                            response.text,
                        )

                    return None
            except requests.exceptions.Timeout:
                if retries <= max_retries:
                    self.logger.warning(
                        "Request timed out. Retrying in %s seconds...",
                        str(REQUEST_RETRY_DELAY),
                    )
                    retries += 1
                    time.sleep(REQUEST_RETRY_DELAY)  # Add a delay before retrying
                else:
                    self.logger.error(
                        "%s; timeout error.",
                        failure_message,
                    )
                    if retry_forever:
                        # If it fails after REQUEST_MAX_RETRIES retries we let it wait forever
                        self.logger.warning("Turn timeouts off and wait forever...")
                        timeout = None
                    else:
                        return None
            except requests.exceptions.ConnectionError:
                if retries <= max_retries:
                    self.logger.warning(
                        "Connection error. Retrying in %s seconds...",
                        str(REQUEST_RETRY_DELAY),
                    )
                    retries += 1
                    time.sleep(REQUEST_RETRY_DELAY)  # Add a delay before retrying
                else:
                    self.logger.error(
                        "%s; connection error.",
                        failure_message,
                    )
                    if retry_forever:
                        # If it fails after REQUEST_MAX_RETRIES retries we let it wait forever
                        self.logger.warning("Turn timeouts off and wait forever...")
                        timeout = None
                        time.sleep(REQUEST_RETRY_DELAY)  # Add a delay before retrying
                    else:
                        return None

    # end method definition

    def parse_request_response(
        self,
        response_object: requests.Response,
        additional_error_message: str = "",
        show_error: bool = True,
    ) -> list | None:
        """Convert the request response (JSon) to a Python list in a safe way that also handles exceptions.

        It first tries to load the response.text
        via json.loads() that produces a dict output. Only if response.text is
        not set or is empty it just converts the response_object to a dict using
        the vars() built-in method.

        Args:
            response_object (requests.Response):
                This is reponse object delivered by the request call.
            additional_error_message (str, optional):
                Use a more specific error message in case of an error.
            show_error (bool, optional):
                If True, write an error to the log file.
                If False, write a warning to the log file.

        Returns:
            list | None:
                The response information or None in case of an error.

        """

        if not response_object:
            return None

        try:
            list_object = json.loads(response_object.text) if response_object.text else vars(response_object)
        except json.JSONDecodeError as exception:
            if additional_error_message:
                message = "Cannot decode response as JSON. {}; error -> {}".format(
                    additional_error_message,
                    exception,
                )
            else:
                message = "Cannot decode response as JSON; error -> {}".format(
                    exception,
                )
            if show_error:
                self.logger.error(message)
            else:
                self.logger.warning(message)
            return None
        else:
            return list_object

    # end method definition

    def authenticate_chat(self) -> str | None:
        """Authenticate for Chat service at Content Aviator / CSAI.

        Returns:
            str | None:
                Authentication token or None if the authentication fails.

        """

        token = self.otcs_object.otcs_ticket() or self.otcs_object.authenticate()

        if token and "otcsticket" in token:
            # Encode the input string before hashing
            encoded_string = token["otcsticket"].encode("utf-8")

            # Create a new SHA-512 hash object
            sha512 = hashlib.sha512()

            # Update the hash object with the input string
            sha512.update(encoded_string)

            # Get the hexadecimal representation of the hash
            hashed_output = sha512.hexdigest()

            self._chat_token = hashed_output

            return self._chat_token

        return None

    # end method definition

    def authenticate_embed(self) -> str | None:
        """Authenticate as embedding service at Content Aviator / CSAI.

        Returns:
            str | None:
                Authentication token or None if the authentication fails.

        """

        url = self.config()["otdsUrl"] + "/otdsws/login"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.config()["clientId"],
            "client_secret": self.config()["clientSecret"],
        }

        result = self.do_request(url=url, method="Post", data=data)

        if result:
            self._embed_token = result["access_token"]
            return self._embed_token
        else:
            self.logger.error(
                "Authentication failed with client ID -> '%s' against -> %s", self.config()["clientId"], url
            )
            return None

    # end method definition

    def chat(self, context: str | None, messages: list, where: list) -> dict:
        r"""Process a chat interaction with Content Aviator.

        Chat requests are meant to be called as end-users.  This should involve
        passing the end-user's access token via the Authorization HTTP header.
        The chat service use OTDS's token endpoint to ensure that the token is valid.

        Args:
            context (str | None):
                Context for the current conversation
                (empty initially, returned by previous responses from POST /v1/chat).
            messages (list):
                List of messages from conversation history.
            where (list):
                Metadata name/value pairs for the query.
                Could be used to specify workspaces, documents, or other criteria in the future.
                Values need to match those passed as metadata to the embeddings API.

        Returns:
            dict: Conversation status

        Example:
        {
            'result': 'I do not know.',
            'called': [
                {
                    'name': 'breakdown_query',
                    'arguments': {},
                    'result': '```json{"input": ["Tell me about the calibration equipment"]}```',
                    'showInContext': False
                },
                {
                    'name': 'store_subqueries',
                    'arguments': {
                        '0': 'Tell me about the calibration equipment'
                    },
                    'showInContext': False
                },
                {
                    'name': 'get_next_subquery_and_reset_segment',
                    'arguments': {},
                    'result': 'Tell me about the calibration equipment',
                    'showInContext': False
                },
                {
                    'name': 'segmented_query',
                    'arguments': {},
                    'result': 'runQuery',
                    'showInContext': False
                },
                {
                    'name': 'get_context',
                    'arguments': {
                        'query': 'Tell me about the calibration equipment'
                    },
                    'result': '',
                    'showInContext': True
                },
                {
                    'name': 'check_answer',
                    'arguments': {},
                    'result': 'noAnswer',
                    'showInContext': False
                },
                {
                    'name': 'segmented_query',
                    'arguments': {},
                    'result': 'answer',
                    'showInContext': False
                },
                {
                    'name': 'get_next_subquery_and_reset_segment',
                    'arguments': {},
                    'showInContext': False
                },
                {
                    'name': 'general_prompt',
                    'arguments': {...},
                    'result': 'I do not know.',
                    'showInContext': False
                },
                {
                    'name': 'filter_references',
                    'arguments': {},
                    'result': '[]',
                    'showInContext': False
                }
            ],
            'references': [],
            'context': 'Tool "get_context" called with arguments {"query":"Tell me about the calibration equipment"} and returned:',
            'queryMetadata': {
                'originalQuery': 'Tell me about the calibration equipment',
                'usedQuery': 'Tell me about the calibration equipment'
            }
        }

        """

        request_url = self.config()["chatUrl"]
        request_header = self.request_header()

        chat_data = {
            "context": context,
            "messages": messages,
            "where": where,
            # "synonyms": self.config()["synonyms"],
            # "inlineCitation": self.config()["inlineCitation"],
        }

        return self.do_request(
            url=request_url,
            method="POST",
            headers=request_header,
            json_data=chat_data,
            timeout=None,
            failure_message="Failed to chat with Content Aviator",
        )

    # end method definition

    def search(
        self, query: str, document_ids: list, workspace_ids: list, threshold: float = 0.5, num_results: int = 10
    ) -> dict:
        """Semantic search for text chunks.

        Search requests are meant to be called as end-users.  This should involve
        passing the end-user's access token via the Authorization HTTP header.
        The chat service use OTDS's token endpoint to ensure that the token is valid.

        Args:
            query (str):
                The query.
            document_ids (list):
                List of documents (IDs) to use as scope for the query.
            workspace_ids (list):
                List of workspaces (IDs) to use as scope for the query.
            threshold (float):
                Minimum similarity score to accept a document. A value like 0.7 means
                only bring back documents that are at least 70% similar.
            num_results (int):
                Also called "top-k". Defined how many "most similar" documents to retrieve.
                Typical value: 3-20. Higher values gets broader context but risks pulling
                in less relevant documents.

        Returns:
            dict:
                Results of the search.

        Example:
        [
            {
                "pageContent": "matched chunk"
                "metadata": {
                    "documentID": 1234,
                    "workspaceID": 4711,
                    "some-id": 123
                },
                "distance": 0.13
            },
            {
                "pageContent": "matched chunk1"
                "metadata": {
                    "documentID": 5678,
                    "workspaceID": 47272
                },
                "distance": 0.22
            }
        ]

        """

        # Validations:
        if not workspace_ids and not document_ids:
            self.logger.error("Either workspace ID(s) or document ID(s) need to be provided!")
            return None

        request_url = self.config()["searchUrl"]
        request_header = self.request_header()

        search_data = {
            "query": query,
            "threshold": threshold,
            "numResults": num_results,
            "metadata": [],
        }

        for document_id in document_ids:
            search_data["metadata"].append({"documentID": str(document_id)})
        for workspace_id in workspace_ids:
            search_data["metadata"].append({"workspaceID": str(workspace_id)})

        return self.do_request(
            url=request_url,
            method="POST",
            headers=request_header,
            data=search_data,
            timeout=None,
            failure_message="Failed to to do a semantic search with query -> '{}'".format(query),
        )

    # end method definition

    def embed(
        self,
        content: str | None = None,
        operation: str = "add",
        document_id: int | None = None,
        workspace_id: int | None = None,
        additional_metadata: dict | None = None,
    ) -> dict:
        """Embed a given content.

        Requests are meant to be called as a service user. This would involve passing a service user's access token
        (token from a particular OAuth confidential client, using client credentials grant).

        Args:
            content (str | None):
                Content to be embedded. Can be empty for "delete" operations.
            operation (str):
                This can be either "add", "update" or "delete".
            document_id (int):
                The ID of the document the content originates from.
            workspace_id (int):
                The ID of the workspace the content originates from.
            additional_metadata (dict | None):
                Dictionary with additional metadata.

        Returns:
            dict: _description_

        """

        # Validations:
        if operation not in ["add", "update", "delete"]:
            self.logger.error("Illegal embed operation -> '%s'!", operation)
            return None
        if operation != "delete" and not content:
            self.logger.error("Add or update operation require content to embed!")
            return None

        request_url = self.config()["embedUrl"]
        request_header = self.request_header(service_type="embed")

        metadata = {}
        if workspace_id:
            metadata["workspaceID"] = workspace_id
        if document_id:
            metadata["documentID"] = document_id
        if additional_metadata:
            metadata.update(additional_metadata)

        embed_data = {
            "content": content,
            "operation": operation,
            "metadata": metadata,
        }

        return self.do_request(
            url=request_url,
            method="POST",
            headers=request_header,
            json_data=embed_data,
            timeout=None,
            failure_message="Failed to embed content",
        )

    # end method definition
