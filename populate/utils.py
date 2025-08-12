import os, requests

def get_access_token():
    url = 'https://device-gateway-api.petrosoft.cloud/v1/auth/token'
    payload = {
        "login": os.environ.get("CSO_API_LOGIN"),
        "password": os.environ.get("CSO_API_PASSWORD")
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 and 'access_token' in response.json():
        return response.json().get('access_token')
    return None

def get_site_resources(site, document):
    url = f"https://business-documents-api.petrosoft.cloud/business-unit-level-resources?documentType={document}&businessUnitId={site}"
    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_documents(resource, start=0, limit=15):
    url = f'https://business-documents-api.petrosoft.cloud/business-documents?resource={resource}&start={start}&limit={limit}'
    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_document(path):
    url = f'https://business-documents-api.petrosoft.cloud/business-document?path={path}'
    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def ism_detail_to_dict(ism_elem):
    """Convert an ISMDetail XML element to a Python dict."""
    def elem_to_dict(elem):
        d = {}
        for child in elem:
            # If the child has children, recurse
            if list(child):
                d[child.tag] = elem_to_dict(child)
            else:
                # If the element has attributes, include them
                if child.attrib:
                    d[child.tag] = {"_value": child.text, **child.attrib}
                else:
                    d[child.tag] = child.text
        # Also include attributes of the main element if present
        if elem.attrib:
            d["_attrib"] = elem.attrib
        return d
    return elem_to_dict(ism_elem)