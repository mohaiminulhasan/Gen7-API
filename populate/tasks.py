from celery import shared_task
from .models import ItemizedInventory
from datetime import datetime
import tempfile, zipfile, os, json

from common.utils import get_access_token, get_site_resources, get_documents, get_document

@shared_task
def process_report_exported(siteid, date):
    access_token = get_access_token()
    site_id = siteid
    document_type = "report-exported"
    resources_response = get_site_resources(site_id, document_type)
    resources_list = resources_response.get("resources", [])
    resource_for_date = next((res for res in resources_list if date in res), None)
    if not resource_for_date:
        return {"error": f"No resource found for date {date}."}

    documents_response = get_documents(resource_for_date)
    documents = documents_response.get("documents", [])
    zip_doc = next((doc for doc in documents if doc.get('fileName', '').endswith('.zip')), None)
    if not zip_doc:
        return {"error": "No .zip document found."}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/gzip"
    }
    zip_content = get_document(zip_doc['path'], headers=headers)
    if zip_content is not None:
        zip_bytes = zip_content.content
    else:
        return {"error": "Could not retrieve zip file content."}

    created = 0
    skipped = 0

    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, "file.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)
            json_file = next((name for name in zip_ref.namelist() if name.endswith('.json')), None)
            if not json_file:
                return {"error": "No JSON file found in zip."}
            json_path = os.path.join(tmpdirname, json_file)
            with open(json_path, 'r', encoding='utf-8') as jf:
                json_data = json.load(jf)

    for item in json_data:
        last_sold_date = item.get("last_sold_date")
        if last_sold_date:
            try:
                last_sold_date = datetime.strptime(last_sold_date, "%Y-%m-%d").date()
            except Exception:
                last_sold_date = None
        else:
            last_sold_date = None

        try:
            entry_date = datetime.strptime(date, "%Y%m%d").date()
        except Exception:
            entry_date = None

        obj, was_created = ItemizedInventory.objects.get_or_create(
            site_id=siteid,
            date=entry_date,
            upc=item.get("upc", ""),
            defaults={
                "name": item.get("name", ""),
                "category": item.get("category") if item.get("category") is not None else "null",
                "size": item.get("size", ""),
                "quantity": item.get("quantity", 0),
                "price": item.get("price", 0) / 100 if isinstance(item.get("price"), int) else item.get("price", 0),
                "external_id": item.get("external_id"),
                "image_url": item.get("image_url", ""),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "brand": item.get("brand", ""),
                "unit_count": item.get("unit_count", 0),
                "active": item.get("active", True),
                "last_sold_date": last_sold_date,
            }
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}