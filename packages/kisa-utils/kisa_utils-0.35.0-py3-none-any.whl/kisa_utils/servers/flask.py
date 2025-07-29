"""
Kisa Server Utilities
"""

import kisa_utils as kutils
from kisa_utils.storage import Path
from kisa_utils.response import Response, Ok, Error
from flask import Flask, request, jsonify, wrappers, render_template_string
from flask_cors import CORS
from functools import wraps
import copy
import inspect
from kisa_utils.structures.validator import Value
from kisa_utils.structures.validator import validateWithResponse
from pathlib import Path as pathLib
import string
import sys
from flask_basicauth import BasicAuth
from types import UnionType
import re


def __init():
    globals()['__ENDPOINTS'] = {}
    __app = Flask(__name__)
    CORS(__app)

    __app.config['PROPAGATE_EXCEPTIONS'] = False

    __basic_auth = BasicAuth(__app)
    globals()['__SERVER_APP'] = __app
    globals()['__BASIC_AUTH'] = __basic_auth


__init()

def __quoteKeys(string):
    # Match keys followed by a colon, e.g., k1: or some_key123:
    return re.sub(r'(\b\w+\b)(\s*):', r'"\1"\2:', string)


def getEndpoints() -> dict:
    return copy.deepcopy(__ENDPOINTS)


def setEndpoints(group: str, endpoint: str, value: dict):
    if (existing_endpoint := __ENDPOINTS.get(group, {}).get(endpoint, None)):
        raise ValueError(f"Endpoint {endpoint} in group {group} already exists as {existing_endpoint}!")
    # if __ENDPOINTS.get(group, {}).get(endpoint, None):
    #     raise ValueError(f"Endpoint `{endpoint}` in group `{group}` already exists as `{get(endpoint)}`!")

    __ENDPOINTS[group] = __ENDPOINTS.get(group, {})

    groupEndpointKeys = list(__ENDPOINTS[group].keys())
    groupEndpoints = [_.lower() for _ in groupEndpointKeys]
    endpointLower = endpoint.lower()

    if endpointLower in groupEndpoints:
        index = groupEndpoints.index(endpointLower)
        raise ValueError(f"Endpoint `{endpoint}` in group `{group}` already exists! as `{groupEndpointKeys[index]}`")

    __ENDPOINTS[group][endpoint] = value


def __validateEndpointAndGroupName(name: str, type: str) -> Response:
    allowedCharacters = string.digits + string.ascii_letters + "-_/"

    if not isinstance(type, str):
        return Error(f" type `{type}` expected a string but got `{type(type)}`")

    type = type.lower()

    if not isinstance(name, str):
        return Error(f"{type} name expected a string but got `{type(type)}")

    name = name.strip().lower()

    if not name and type != "group":
        return Error(f"{type} name `{name}` is invalid. It cant be empty spaces")

    if " " in name:
        return Error(f"{type} name `{name}` should not contain spaces")

    if name and len(name) < 3:
        return Error(f"{type} name `{name}` should contain at least 3 characters")

    if "//" in name:
        return Error(f"{type} name `{name}` should not contain `//`")

    for char in name:
        if char not in allowedCharacters:
            return Error(f"{type} name `{name}` should contain characters from `{allowedCharacters}`")

    return Ok()


def __findCommonBase(path1, path2):
    """
    finds the first common directory between two paths.
    """
    # Convert both paths to absolute paths (if not already)
    path1 = pathLib(path1).resolve()
    path2 = pathLib(path2).resolve()

    commonBase = None

    # Iterate through the parents of both paths
    for parent1 in path1.parents:
        for parent2 in path2.parents:
            if parent1 == parent2:
                commonBase = parent1
                break
        if commonBase:
            break
    return commonBase


def __getHandlerRelativePath(handler: callable) -> str:
    handlerFilePath = inspect.getsourcefile(handler)
    runningFilePath = __file__

    commonDir = __findCommonBase(handlerFilePath, runningFilePath)

    if commonDir is None:
        raise ValueError(
            f"No common base directory found between the path for handler `{handler}` and the running file path for `{__file__.split('/')[-1]}`.")

    relativePath = str(pathLib(handlerFilePath).relative_to(
        pathLib(commonDir))).strip(".py")
    relativePath = f"{relativePath}:{handler.__name__}"
    relativePath = "0.0.1/src/backend/".join([""] + relativePath.split("0.0.1/src/backend/")[1:])

    return relativePath


def entry(func):
    """
    Entry decorator automatically injects request data into a handler function
    before each request as keyword arguments. These include:

    - origin: The value of the 'Origin' header from the request, or None if not present.
    - headers: A dictionary of all headers in the request.
    - method: The HTTP method (e.g., GET, POST) used for the request.
    - payload: The JSON payload of the request, or an empty dictionary if no payload is present.

    Example usage:
        @entry()
        def handler(origin=None, headers=None, method=None, payload=None):
            print("Request origin:", origin)
            print("Request headers:", headers)
            print("HTTP method:", method)
            print("JSON payload:", payload)
    """

    signature = inspect.signature(func)

    for key, value in signature.parameters.items():
        if value.kind != inspect.Parameter.KEYWORD_ONLY:
            raise ValueError(
                f'function `{func.__name__}`: should only take keyword arguments or parameters!')

    def wrapper(*args, **kwargs):
        origin = request.headers.get('Origin')
        headers = dict(request.headers)
        method = request.method
        payload = request.get_json() if request.is_json else {}

        return func(origin=origin, headers=headers, method=method, payload=payload)

    __SERVER_APP.before_request(wrapper)

    return wrapper


# def exit(func):
#     signature = inspect.signature(func)

#     for key, value in signature.parameters.items():
#         if value.kind != inspect.Parameter.KEYWORD_ONLY:
#             raise ValueError(
#                 f'function `{func.__name__}`: should only take keyword arguments or parameters, this case response only')

#     def wrapper(response):
#         return func(response=response)

#     __SERVER_APP.after_request(wrapper)

#     return wrapper


def endpoint(name: str = '', group: str = '') -> Response:
    def decorator(func):
        # in case the decorator is called as `@endpoint` as opposed to `@endpoint(...)`
        nonlocal name, group
        if callable(name):
            name, group = '', ''

        if 1:
            _group = group + '/' if group else ''
            _name = '/' + _group + (name or func.__name__)
            handler = func

            if not (endpointValidationReply := __validateEndpointAndGroupName(_name, "endpoint")):
                raise ValueError(endpointValidationReply.log)

            if not (groupValidationReply := __validateEndpointAndGroupName(_group, "group")):
                raise ValueError(groupValidationReply.log)

            signature = inspect.signature(func)
            typeHints = func.__annotations__
            parameters = signature.parameters

            if not handler.__doc__:
                raise ValueError(
                    f"handler function {func.__name__} has no docString!")

            if not typeHints.get("return", None):
                raise TypeError(
                    f"handler function {func.__name__} has no return type")

            if typeHints.get("return") != Response:
                raise TypeError(
                    f"handler function {func.__name__} return type should be kisa-response")

            args = []
            kwargs = []

            for key, value in signature.parameters.items():
                if value.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    raise TypeError(
                        f"function `{handler.__name__}` should take either positional-only or keyword-only parameters")

                if value.kind == inspect.Parameter.POSITIONAL_ONLY:
                    if value.default is not inspect.Parameter.empty:
                        if not (resp := validateWithResponse(value.default, typeHints[key])):
                            raise ValueError(f'arg `{key}` default value: {resp.log}')
                        args.append((key, value.default))
                    else:
                        args.append((key,))
                elif value.kind == inspect.Parameter.KEYWORD_ONLY:
                    if value.default is not inspect.Parameter.empty:
                        if not (resp := validateWithResponse(value.default, typeHints[key])):
                            raise ValueError(f'arg `{key}` default value: {resp.log}')
                        kwargs.append((key, value.default))
                    else:
                        kwargs.append((key,))

                if str(value).startswith('*'):
                    raise ValueError(
                        f'function `{func.__name__}`: *{key} or **{key} not allowed in function signature')

                hint = typeHints.get(key, None)
                if not hint:
                    raise TypeError(f"parameter {key} has no type hint")

            validationStructure = copy.deepcopy(typeHints)
            del validationStructure["return"]

            __group = group if group else 'default'
            new_entry = {
                "handler": handler,
                "expectedStructure": validationStructure,
                "path": __getHandlerRelativePath(handler),
                "docs": handler.__doc__
            }
            setEndpoints(__group, _name, new_entry)

        def w():
            nonlocal handler

            payload = request.json

            nonlocal validationStructure

            _args = []
            _kwargs = {}

            for item in args:
                arg = item[0]

                if arg in payload:
                    _args.append(payload[arg])
                else:
                    if len(item) == 2:
                        default = item[1]
                        _args.append(default)
                        payload[arg] = default

            for item in kwargs:
                kwarg = item[0]

                if kwarg in payload:
                    _kwargs[kwarg] = payload[kwarg]
                else:
                    if len(item) == 2:
                        default = item[1]
                        _kwargs[kwarg] = default
                        payload[kwarg] = default

            validationResponse = validateWithResponse(
                payload, validationStructure)
            if not validationResponse:
                return validationResponse

            resp = handler(*_args, **_kwargs)

            if not isinstance(resp, Response):
                raise TypeError(f'`{handler.__name__}` did NOT return a Kisa-Response Object')
            return resp

        w.__name__ = f'__kisa_wrapper_{_group}_{handler.__name__}'
        __SERVER_APP.route(_name, methods=['POST'])(w)

    # in case the decorator is called as `@endpoint` as opposed to `@endpoint(...)`
    if callable(name):
        return decorator(name)
    return decorator


def startServer(host: str = '0.0.0.0', port: int = 5000, debug: bool = True, threaded: bool = True, userName: str = 'user', password: str = '0000', **others) -> Response:
    runningFile = sys.argv[0].split("/")[-1]

    stack = inspect.stack()
    fileCallingStartServer = stack[1].filename.split("/")[-1]

    if ".py" in runningFile and runningFile != fileCallingStartServer:
        raise AssertionError(
            f"start server is not being from the running file. \n runningFile: {runningFile} \n fileCallingStartServer: {fileCallingStartServer}")

    __SERVER_APP.config['BASIC_AUTH_USERNAME'] = userName
    __SERVER_APP.config['BASIC_AUTH_PASSWORD'] = password

    getSourceMap()
    generateDocs()

    __SERVER_APP.run(
        host,
        port,
        debug=debug,
        threaded=threaded,
        **others
    )
    return Ok()


def getAppInstance():
    return __SERVER_APP


def generateDocs():
    data = getEndpoints()
    print('generating docs...')
    _html = generate_html(data)

    @__SERVER_APP.route('/api/docs', methods=['GET'])
    @__BASIC_AUTH.required
    def docs():
        return render_template_string(_html)


def __customPrettyPrint(data: str, indent: int = 2) -> str:
    '''
    pretty print json-like string (doesnt have to be valid json eg "[int|float, {k:str}]")
    '''
    result = ""
    level = 0
    i = 0
    in_string = False
    buffer = ""

    def flush_buffer(newline=True):
        nonlocal buffer, result
        stripped = buffer.strip()
        if stripped:
            result += " " * (indent * level) + stripped
            if newline:
                result += "\n"
        buffer = ""

    while i < len(data):
        char = data[i]

        if char == '"':
            in_string = not in_string
            buffer += char

        elif char in '{[' and not in_string:
            buffer = buffer.rstrip()  # ensure no extra space before {
            buffer += ' '+char
            flush_buffer()
            level += 1

        elif char in '}]' and not in_string:
            flush_buffer()
            level -= 1
            result += " " * (indent * level) + char
            if i + 1 < len(data) and data[i + 1] == ',':
                result += ','
                i += 1
            result += "\n"

        elif char == ',' and not in_string:
            buffer += char
            flush_buffer()

        elif char == ':' and not in_string:
            buffer = buffer.rstrip()  # remove space before colon
            buffer += ":"

            # Ensure exactly one space after colon
            # Look ahead — if the next char is not a space, insert one manually
            if i + 1 < len(data) and data[i + 1] != ' ':
                buffer += " "
            elif i + 1 < len(data) and data[i + 1] == ' ':
                # Skip all extra spaces after colon
                while i + 1 < len(data) and data[i + 1] == ' ':
                    i += 1
                buffer += " "

        else:
            buffer += char

        i += 1

    flush_buffer()
    return result.strip()


def generate_html(data):
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px; max-width: 800px; margin: auto;">
        <h1 style="text-align: center; color: #333;">API Documentation</h1>

        <!-- Filter and Search Controls -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <select id="groupFilter" style="padding: 8px; font-size: 1em;">
                <option value="">All Groups</option>
                {}
            </select>
            <input type="text" id="searchInput" placeholder="Search endpoints..." style="padding: 8px; font-size: 1em; width: 60%;" onkeyup="filterContent()">
        </div>
    """.format(''.join(f'<option value="{group}">{group.capitalize()}</option>' for group in data.keys()))

    # Generate the HTML structure for each group and endpoint
    for group, endpoints in data.items():
        html += f"""
        <details class="group" data-group="{group}" style="border: 1px solid #ddd; border-radius: 8px; background-color: #fff; margin-bottom: 15px; padding: 15px;">
            <summary style="font-size: 1.4em; font-weight: bold; cursor: pointer; outline: none; color: #333;">
                {group.capitalize()}
            </summary>
            <div class="endpoints">
        """

        for endpoint, details in endpoints.items():
            html += f"""
            <div class="endpoint" data-endpoint="{endpoint}">
                <h3 style="font-size: 1.2em; color: #0073e6;">Endpoint: <span class="highlight">{endpoint}</span></h3>
            """

            if details.get('docs'):
                html += f"""
                <p style="margin: 5px 0; font-size: 0.9em;">
                    <strong>Documentation:</strong>
                    <pre style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{details['docs'].strip()}</pre>
                </p>
                """

            # Display the expected structure as a formatted code snippet
            html += "<p style='margin: 5px 0;'><strong>Expected Structure:</strong><br>"
            html += "<pre style='background-color: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; font-size: 0.9em; overflow-x: auto;'>"
            html += "{<br>"

            for key, val in details['expectedStructure'].items():
                # print(key, val, isinstance(val, type))
                expandStructure:bool = False
                
                if isinstance(val, UnionType):
                    types = val.__args__
                    _type = '|'.join(_.__name__ for _ in types)

                elif isinstance(val, (type, Value)):
                    _type = val.__name__
                else:
                    _type = type(val).__name__ #+ f'\n  {val} \n'.replace("'",'').replace('class ','').replace('<','').replace('>','')
                    expandStructure = True

                html += f"<span style='color: #66d9ef;'>&nbsp;&nbsp;'{key}'</span>: <span style='color: #a6e22e;'>{_type}</span>,<br>"
                if expandStructure:
                    expanded:str = f'{val}'\
                        .replace("'",'')\
                        .replace('class ','')\
                        .replace('<','')\
                        .replace('>','')\
                        .replace(' | ','|')\
                        .replace(': ',':')
                    expanded = __quoteKeys(expanded)

                    indentation = '&nbsp;'*(len(type(val).__name__)+len(':'))
                    expanded = __customPrettyPrint(expanded).replace('\n',f'<br>{indentation}')
                        
                    html += f"<span style='color: #66d9ef;'>{indentation}</span> <span style='color: #fae22e;'>{expanded}</span><br>"

            html += "}</pre></p></div>"

        html += """
            </div>
        </details><br>
        """

    # JavaScript for filtering and search highlighting
    html += """
        <script>
            function filterContent() {
                let groupFilter = document.getElementById("groupFilter").value.toLowerCase();
                let searchInput = document.getElementById("searchInput").value.toLowerCase();

                // Iterate over each group and endpoint to apply filters
                document.querySelectorAll(".group").forEach(group => {
                    let groupName = group.getAttribute("data-group").toLowerCase();
                    let groupMatches = groupFilter === "" || groupName === groupFilter;

                    // Show or hide group based on filter
                    group.style.display = groupMatches ? "block" : "none";

                    if (groupMatches) {
                        let endpointMatchFound = false;

                        // Iterate over each endpoint within the group
                        group.querySelectorAll(".endpoint").forEach(endpoint => {
                            let endpointName = endpoint.getAttribute("data-endpoint").toLowerCase();
                            let matchesSearch = endpointName.includes(searchInput);

                            // Highlight matches
                            let highlightSpan = endpoint.querySelector(".highlight");
                            if (searchInput) {
                                let regex = new RegExp(searchInput, "gi");
                                highlightSpan.innerHTML = endpointName.replace(regex, (match) => `<span style="background-color: #ffeb3b;">${match}</span>`);
                            } else {
                                highlightSpan.innerHTML = endpointName;
                            }

                            endpoint.style.display = matchesSearch ? "block" : "none";
                            if (matchesSearch) endpointMatchFound = true;
                        });

                        // If no endpoint in the group matches the search, hide the group
                        if (!endpointMatchFound) {
                            group.style.display = "none";
                        }
                    }
                });
            }

            // Event listener for dropdown filter
            document.getElementById("groupFilter").addEventListener("change", filterContent);
        </script>
    """

    html += "</body></html>"
    return html


def getSourceMap():
    data = getEndpoints()
    with open('sourcemap.txt', 'w') as fwrite:
        for key, items in data.items():
            for endpoint in items:
                string = f"{endpoint} ===> {items[endpoint]['path']} \n"
                fwrite.write(string)


# startServer()
if __name__ == "__main__":
    # print('======> app:', getAppInstance())
    startServer()


