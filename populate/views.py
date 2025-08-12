import xml.etree.ElementTree as ET
from rest_framework.decorators import api_view
from rest_framework.response import Response

from populate.serializers import ISMDetailSerializer

from .utils import get_access_token, get_site_resources, get_documents, get_document
from .models import ISMDetail
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
            xml_content = get_document(doc['path'])
            if xml_content and "<ISMDetail>" in xml_content:
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