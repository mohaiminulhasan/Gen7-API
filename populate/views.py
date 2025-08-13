import xml.etree.ElementTree as ET, tempfile, zipfile, os, json, io
from rest_framework.decorators import api_view
from rest_framework.response import Response

from populate.serializers import ISMDetailSerializer, ItemizedInventorySerializer

from common.utils import get_access_token, get_site_resources, get_documents, get_document
from .models import ISMDetail, ItemizedInventory
from datetime import datetime

@api_view(['GET'])
def populate_data(request, siteid, date):
    if request.method == 'GET':
        access_token = get_access_token()
        if not access_token:
            return Response({"error": "Failed to obtain access token."}, status=401)
        
        site_id = siteid
        document_type = "shift_item-sales-movement"
        resources_response = get_site_resources(site_id, document_type)

        resources_list = resources_response.get("resources", [])
        if not resources_list:
            return Response({"error": "No resources found."}, status=404)
        
        # Find the resource that contains the date
        resource_for_date = next((res for res in resources_list if date in res), None)
        if not resource_for_date:
            return Response({"error": f"No resource found for date {date}."}, status=404)

        documents_response = get_documents(resource_for_date)
        documents = documents_response.get("documents", [])

        item_sales_docs = [doc for doc in documents if 'item-sales' in doc.get('fileName', '')]

        created = 0
        skipped = 0

        for doc in item_sales_docs:
            response = get_document(doc['path'])
            if response is not None:
                xml_content = response.text
                if "<ISMDetail>" in xml_content:
                    try:
                        root = ET.fromstring(xml_content)
                        # Find BeginDate once per document
                        begin_date = None
                        begin_date_elem = root.find('.//BeginDate')
                        if begin_date_elem is not None:
                            begin_date = begin_date_elem.text

                        # Parse date string to date object if possible
                        parsed_date = None
                        if begin_date:
                            try:
                                parsed_date = datetime.strptime(begin_date, "%Y-%m-%d").date()
                            except Exception:
                                parsed_date = None

                        for ism_elem in root.iter('ISMDetail'):
                            def get_text(elem, tag):
                                found = elem.find(tag)
                                return found.text if found is not None else None

                            sell_price_summary = ism_elem.find('ISMSellPriceSummary')
                            sales_totals = sell_price_summary.find('ISMSalesTotals') if sell_price_summary is not None else None

                            item_id = get_text(ism_elem, "ItemID")
                            description = get_text(ism_elem, "Description")
                            merchandise_code = get_text(ism_elem, "MerchandiseCode")
                            selling_units = get_text(ism_elem, "SellingUnits")
                            actual_sales_price = get_text(sell_price_summary, "ActualSalesPrice") if sell_price_summary is not None else None
                            sales_quantity = get_text(sales_totals, "SalesQuantity") if sales_totals is not None else None
                            sales_amount = get_text(sales_totals, "SalesAmount") if sales_totals is not None else None
                            discount_amount = get_text(sales_totals, "DiscountAmount") if sales_totals is not None else None
                            discount_count = get_text(sales_totals, "DiscountCount") if sales_totals is not None else None
                            promotion_amount = get_text(sales_totals, "PromotionAmount") if sales_totals is not None else None
                            promotion_count = get_text(sales_totals, "PromotionCount") if sales_totals is not None else None
                            refund_amount = get_text(sales_totals, "RefundAmount") if sales_totals is not None else None
                            refund_count = get_text(sales_totals, "RefundCount") if sales_totals is not None else None
                            transaction_count = get_text(sales_totals, "TransactionCount") if sales_totals is not None else None

                            # Check if entry exists
                            exists = ISMDetail.objects.filter(
                                site_id=site_id,
                                date=parsed_date,
                                item_id=item_id
                            ).exists()

                            if exists:
                                skipped += 1
                            else:
                                ISMDetail.objects.create(
                                    site_id=site_id,
                                    date=parsed_date,
                                    item_id=item_id,
                                    description=description,
                                    merchandise_code=merchandise_code,
                                    selling_units=int(selling_units) if selling_units is not None else 0,
                                    actual_sales_price=actual_sales_price or 0,
                                    sales_quantity=int(sales_quantity) if sales_quantity is not None else 0,
                                    sales_amount=sales_amount or 0,
                                    discount_amount=discount_amount or 0,
                                    discount_count=int(discount_count) if discount_count is not None else 0,
                                    promotion_amount=promotion_amount or 0,
                                    promotion_count=int(promotion_count) if promotion_count is not None else 0,
                                    refund_amount=refund_amount or 0,
                                    refund_count=int(refund_count) if refund_count is not None else 0,
                                    transaction_count=int(transaction_count) if transaction_count is not None else 0,
                                )
                                created += 1
                    except ET.ParseError:
                        continue  # skip malformed

        return Response({"created": created, "skipped": skipped})

@api_view(['GET'])
def ism_data(request, siteid, date):
    if request.method == 'GET':
        data = ISMDetail.objects.filter(site_id=siteid, date=date)
        serializer = ISMDetailSerializer(data, many=True)
        return Response(serializer.data)
    return Response({"error": "Invalid request method."}, status=405)

@api_view(['GET'])
def populate_report_exported(request, siteid, date):
    if request.method == 'GET':
        access_token = get_access_token()
        if not access_token:
            return Response({"error": "Failed to obtain access token."}, status=401)

        site_id = siteid
        document_type = "report-exported"
        resources_response = get_site_resources(site_id, document_type)

        resources_list = resources_response.get("resources", [])
        if not resources_list:
            return Response({"error": "No resources found."}, status=404)

        # Find the resource that contains the date
        resource_for_date = next((res for res in resources_list if date in res), None)
        if not resource_for_date:
            return Response({"error": f"No resource found for date {date}."}, status=404)

        documents_response = get_documents(resource_for_date)
        documents = documents_response.get("documents", [])

        # Assume the first document is the .zip file you want
        zip_doc = next((doc for doc in documents if doc.get('fileName', '').endswith('.zip')), None)
        if not zip_doc:
            return Response({"error": "No .zip document found."}, status=404)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/gzip"
        }
        # Get the zip file content (should be bytes)
        zip_content = get_document(zip_doc['path'], headers=headers)  # This should return bytes, not text
        print(zip_content)

        # If get_document returns a requests.Response, use .content; if bytes, use as is
        if zip_content is not None:
            zip_bytes = zip_content.content
        else:
            return Response({"error": "Could not retrieve zip file content."}, status=500)

        # Extract the zip to a temp directory and find the JSON file
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = os.path.join(tmpdirname, "file.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_bytes)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
                # Find the first .json file
                json_file = next((name for name in zip_ref.namelist() if name.endswith('.json')), None)
                if not json_file:
                    return Response({"error": "No JSON file found in zip."}, status=404)
                json_path = os.path.join(tmpdirname, json_file)
                with open(json_path, 'r', encoding='utf-8') as jf:
                    json_data = json.load(jf)
        
        created = 0
        skipped = 0

        for item in json_data:
            # Parse last_sold_date if present
            last_sold_date = item.get("last_sold_date")
            if last_sold_date:
                try:
                    last_sold_date = datetime.strptime(last_sold_date, "%Y-%m-%d").date()
                except Exception:
                    last_sold_date = None
            else:
                last_sold_date = None

            # Parse date from URL parameter
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
                    "category": item.get("category", ""),
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

        return Response({"created": created, "skipped": skipped})

@api_view(['GET'])
def itemized_inventory(request, siteid, date):
    if request.method == 'GET':
        data = ItemizedInventory.objects.filter(site_id=siteid, date=date)
        serializer = ItemizedInventorySerializer(data, many=True)
        return Response(serializer.data)
    pass