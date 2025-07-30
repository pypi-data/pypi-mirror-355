"""
    Vault HTTP API

    The VGS Vault HTTP API is used for storing, retrieving, and managing sensitive data (aka Tokenization) within a VGS Vault.  The VGS API is organized around REST. Our API is built with a predictable resource-oriented structure, uses JSON-encoded requests and responses, follows standard HTTP verbs/responses, and uses industry standard authentication.  ## What is VGS  Storing sensitive data on your company’s infrastructure often comes with a heavy compliance burden. For instance, storing payments data yourself greatly increases the amount of work needed to become PCI compliant. It also increases your security risk in general. To combat this, companies will minimize the amount of sensitive information they have to handle or store.  VGS provides multiple methods for minimizing the sensitive information that needs to be stored which allows customers to secure any type of data for any use-case.  **Tokenization** is a method that focuses on securing the storage of data. This is the quickest way to get started and is free. [Get started with Tokenization](https://www.verygoodsecurity.com/docs/tokenization/getting-started).  **Zero Data** is a unique method invented by VGS in 2016 that securely stores data like Tokenization, however it also removes the customer’s environment from PCI scope completely providing maximum security, and minimum compliance scope. [Get started with Zero Data](https://www.verygoodsecurity.com/docs/getting-started/before-you-start).  Additionally, for scenarios where neither technology is a complete solution, for instance with legacy systems, VGS provides a compliance product which guarantees customers are able to meet their compliance needs no matter what may happen. [Get started with Control](https://www.verygoodsecurity.com/docs/control).  ## Learn about Tokenization  - [Create an Account for Free Tokenization](https://dashboard.verygoodsecurity.com/tokenization) - [Try a Tokenization Demo](https://www.verygoodsecurity.com/docs/tokenization/getting-started) - [Install a Tokenization SDK](https://www.verygoodsecurity.com/docs/tokenization/client-libraries)  ## Introduction  ### Alias-Formats | Format                          | Description                                                                               | |---------------------------------|-------------------------------------------------------------------------------------------| | UUID                            | Generic - VGS Alias (Default) - tok_sandbox_xxxxxxxxxxxxxxxxxxxxxxxxx                     | | NUM_LENGTH_PRESERVING           | Generic - Numeric Length Preserving - xxxxxxxxxxxxxxxx                                    | | FPE_SIX_T_FOUR                  | Payment Card - Format Preserving, Luhn Valid (6T4) - <first_six>xxxxxx<last_four>         | | FPE_T_FOUR                      | Payment Card - Format Preserving, Luhn Valid (T4) - xxxxxxxxxxxx<last_four>               | | PFPT                            | Payment Card - Prefixed, Luhn Valid, 19 Digits Fixed Length - xxxxxxxxxxxxxxxxxxx         | | NON_LUHN_FPE_ALPHANUMERIC       | Payment Card - Format Preserving - Non Luhn Valid - xxxxxxxxxxxxxxxx                      | | FPE_SSN_T_FOUR                  | SSN - Format Preserving (A4) - xxx-xx-<last_four>                                         | | FPE_ACC_NUM_T_FOUR              | Account Number - Numeric Length Preserving (A4) - xxxxxxxxxxxx<last_four>                 | | FPE_ALPHANUMERIC_ACC_NUM_T_FOUR | Account Number - Alphanumeric Length Preserving (A4) - xxxxxxxxxxxx<last_four>            | | GENERIC_T_FOUR                  | Generic - VGS Alias Last Four (T4) - tok_sandbox_xxxxxxxxxxxxxxxxxxxxxxxxx_<last_four>    | | RAW_UUID                        | Generic - UUID - xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                                     | | ALPHANUMERIC_SIX_T_FOUR         | Numeric - Include Alphanumeric, 19 symbols length (6T4) - <first_six>xxxxxxxxx<last_four> | | VGS_FIXED_LEN_GENERIC           | Generic - VGS Alphanumeric Fixed Length, 29 characters - vgsxxxxxxxxxxxxxxxxxxxxxxxxxx    |   ## Authentication  This API uses `Basic` authentication and is implemented using industry best practices to ensure the security of the connection. Read more about [Identity and Access Management at VGS](https://www.verygoodsecurity.com/docs/vault/the-platform/iam)  Credentials to access the API can be generated on the [dashboard](https://dashboard.verygoodsecurity.com) by going to the Settings section of the vault of your choosing.  [Docs » Guides » Access credentials](https://www.verygoodsecurity.com/docs/settings/access-credentials)  ## Resource Limits  ### Data Limits  This API allows storing data up to 32MB in size.  ### Rate Limiting  The API allows up to 3,000 requests per minute. Requests are associated with the vault, regardless of the access credentials used to authenticate the request.  Your current rate limit is included as HTTP headers in every API response:  | Header Name             | Description                                              | |-------------------------|----------------------------------------------------------| | `x-ratelimit-remaining` | The number of requests remaining in the 1-minute window. |  If you exceed the rate limit, the API will reject the request with HTTP [429 Too Many Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429).  ### Errors  The API uses standard HTTP status codes to indicate whether the request succeeded or not.  In case of failure, the response body will be JSON in a predefined format. For example, trying to create too many aliases at once results in the following response:  ```json {     \"errors\": [         {             \"status\": 400,             \"title\": \"Bad request\",             \"detail\": \"Too many values (limit: 20)\",             \"href\": \"https://api.sandbox.verygoodvault.com/aliases\"         }     ] } ```   # noqa: E501

    The version of the OpenAPI document: 1.0.0
    Contact: support@verygoodsecurity.com
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from vgs_api_client.api_client import ApiClient, Endpoint as _Endpoint
from vgs_api_client.model_utils import (  # noqa: F401
    check_allowed_values,
    check_validations,
    date,
    datetime,
    file_type,
    none_type,
    validate_and_convert_types
)
from vgs_api_client.model.batch_aliases_request import BatchAliasesRequest
from vgs_api_client.model.create_aliases_request import CreateAliasesRequest
from vgs_api_client.model.inline_response200 import InlineResponse200
from vgs_api_client.model.inline_response2001 import InlineResponse2001
from vgs_api_client.model.inline_response201 import InlineResponse201
from vgs_api_client.model.inline_response_default import InlineResponseDefault
from vgs_api_client.model.update_alias_request import UpdateAliasRequest


class AliasesApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client
        self.create_aliases_endpoint = _Endpoint(
            settings={
                'response_type': (InlineResponse201,),
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases',
                'operation_id': 'create_aliases',
                'http_method': 'POST',
                'servers': None,
            },
            params_map={
                'all': [
                    'create_aliases_request',
                ],
                'required': [],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'create_aliases_request':
                        (CreateAliasesRequest,),
                },
                'attribute_map': {
                },
                'location_map': {
                    'create_aliases_request': 'body',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [
                    'application/json'
                ]
            },
            api_client=api_client
        )
        self.delete_alias_endpoint = _Endpoint(
            settings={
                'response_type': None,
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases/{alias}',
                'operation_id': 'delete_alias',
                'http_method': 'DELETE',
                'servers': None,
            },
            params_map={
                'all': [
                    'alias',
                    'storage',
                ],
                'required': [
                    'alias',
                ],
                'nullable': [
                ],
                'enum': [
                    'storage',
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                    ('storage',): {

                        "PERSISTENT": "PERSISTENT",
                        "VOLATILE": "VOLATILE"
                    },
                },
                'openapi_types': {
                    'alias':
                        (str,),
                    'storage':
                        (str,),
                },
                'attribute_map': {
                    'alias': 'alias',
                    'storage': 'storage',
                },
                'location_map': {
                    'alias': 'path',
                    'storage': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client
        )
        self.delete_aliases_endpoint = _Endpoint(
            settings={
                'response_type': None,
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases/delete',
                'operation_id': 'delete_aliases',
                'http_method': 'POST',
                'servers': None,
            },
            params_map={
                'all': [
                    'batch_aliases_request',
                ],
                'required': [
                    'batch_aliases_request',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'batch_aliases_request':
                        (BatchAliasesRequest,),
                },
                'attribute_map': {
                },
                'location_map': {
                    'batch_aliases_request': 'body',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [],
                'content_type': [
                    'application/json'
                ]
            },
            api_client=api_client
        )
        self.reveal_alias_endpoint = _Endpoint(
            settings={
                'response_type': (InlineResponse2001,),
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases/{alias}',
                'operation_id': 'reveal_alias',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'alias',
                    'storage',
                ],
                'required': [
                    'alias',
                ],
                'nullable': [
                ],
                'enum': [
                    'storage',
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                    ('storage',): {

                        "PERSISTENT": "PERSISTENT",
                        "VOLATILE": "VOLATILE"
                    },
                },
                'openapi_types': {
                    'alias':
                        (str,),
                    'storage':
                        (str,),
                },
                'attribute_map': {
                    'alias': 'alias',
                    'storage': 'storage',
                },
                'location_map': {
                    'alias': 'path',
                    'storage': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client
        )
        self.reveal_multiple_aliases_endpoint = _Endpoint(
            settings={
                'response_type': (InlineResponse200,),
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases',
                'operation_id': 'reveal_multiple_aliases',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'aliases',
                    'storage',
                ],
                'required': [
                    'aliases',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'aliases':
                        (str,),
                    'storage':
                        (str,),
                },
                'attribute_map': {
                    'aliases': 'aliases',
                    'storage': 'storage',
                },
                'location_map': {
                    'aliases': 'query',
                    'storage': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client
        )
        self.update_alias_endpoint = _Endpoint(
            settings={
                'response_type': None,
                'auth': [
                    'basicAuth'
                ],
                'endpoint_path': '/aliases/{alias}',
                'operation_id': 'update_alias',
                'http_method': 'PUT',
                'servers': None,
            },
            params_map={
                'all': [
                    'alias',
                    'storage',
                    'update_alias_request',
                ],
                'required': [
                    'alias',
                ],
                'nullable': [
                ],
                'enum': [
                    'storage',
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                    ('storage',): {

                        "PERSISTENT": "PERSISTENT",
                        "VOLATILE": "VOLATILE"
                    },
                },
                'openapi_types': {
                    'alias':
                        (str,),
                    'storage':
                        (str,),
                    'update_alias_request':
                        (UpdateAliasRequest,),
                },
                'attribute_map': {
                    'alias': 'alias',
                    'storage': 'storage',
                },
                'location_map': {
                    'alias': 'path',
                    'storage': 'query',
                    'update_alias_request': 'body',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [
                    'application/json'
                ]
            },
            api_client=api_client
        )

    def create_aliases(
        self,
        **kwargs
    ):
        """Create aliases  # noqa: E501

        Stores multiple values at once & returns their aliases.  Alternatively, this endpoint may be used to associate additional (i.e. secondary) aliases with the same underlying data as the reference alias specified in the request body.  **NOTE:** You cannot reference the same alias more than once in a single request.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_aliases(async_req=True)
        >>> result = thread.get()


        Keyword Args:
            create_aliases_request (CreateAliasesRequest): [optional]
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            InlineResponse201
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        return self.create_aliases_endpoint.call_with_http_info(**kwargs)

    def delete_alias(
        self,
        alias,
        **kwargs
    ):
        """Delete alias  # noqa: E501

        Removes a single alias.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_alias(alias, async_req=True)
        >>> result = thread.get()

        Args:
            alias (str): Alias to operate on.

        Keyword Args:
            storage (str): [optional] if omitted the server will use the default value of "PERSISTENT"
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            None
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['alias'] = \
            alias
        return self.delete_alias_endpoint.call_with_http_info(**kwargs)

    def delete_aliases(
        self,
        batch_aliases_request,
        **kwargs
    ):
        """Batch Delete Aliases  # noqa: E501

        Deletes multiple aliases.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.delete_aliases(batch_aliases_request, async_req=True)
        >>> result = thread.get()

        Args:
            batch_aliases_request (BatchAliasesRequest):

        Keyword Args:
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            None
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['batch_aliases_request'] = \
            batch_aliases_request
        return self.delete_aliases_endpoint.call_with_http_info(**kwargs)

    def reveal_alias(
        self,
        alias,
        **kwargs
    ):
        """Reveal single alias  # noqa: E501

        Retrieves a stored value along with its aliases.  **NOTE:** This endpoint may expose sensitive data. Therefore, it is disabled by default. To enable it, please contact your VGS account manager or drop us a line at [support@verygoodsecurity.com](mailto:support@verygoodsecurity.com).   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.reveal_alias(alias, async_req=True)
        >>> result = thread.get()

        Args:
            alias (str): Alias to operate on.

        Keyword Args:
            storage (str): [optional] if omitted the server will use the default value of "PERSISTENT"
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            InlineResponse2001
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['alias'] = \
            alias
        return self.reveal_alias_endpoint.call_with_http_info(**kwargs)

    def reveal_multiple_aliases(
        self,
        aliases,
        **kwargs
    ):
        """Reveal multiple aliases  # noqa: E501

        Given a list of aliases, retrieves all associated values stored in the vault.  **NOTE:** This endpoint may expose sensitive data. Therefore, it is disabled by default. To enable it, please contact your VGS account manager or drop us a line at [support@verygoodsecurity.com](mailto:support@verygoodsecurity.com).   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.reveal_multiple_aliases(aliases, async_req=True)
        >>> result = thread.get()

        Args:
            aliases (str): Comma-separated list of aliases to reveal.

        Keyword Args:
            storage (str): PERSISTENT or VOLATILE storage. [optional]
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            InlineResponse200
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['aliases'] = \
            aliases
        return self.reveal_multiple_aliases_endpoint.call_with_http_info(**kwargs)

    def update_alias(
        self,
        alias,
        **kwargs
    ):
        """Update data classifiers  # noqa: E501

        Apply new classifiers to the value that the specified alias is associated with.   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.update_alias(alias, async_req=True)
        >>> result = thread.get()

        Args:
            alias (str): Alias to operate on.

        Keyword Args:
            storage (str): [optional] if omitted the server will use the default value of "PERSISTENT"
            update_alias_request (UpdateAliasRequest): [optional]
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            None
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['alias'] = \
            alias
        return self.update_alias_endpoint.call_with_http_info(**kwargs)

