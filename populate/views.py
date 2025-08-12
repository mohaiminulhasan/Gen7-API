import xml.etree.ElementTree as ET
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .utils import get_access_token, get_site_resources, get_documents, get_document

@api_view(['GET'])
def populate_data(request):
    if request.method == 'GET':
        access_token = get_access_token()
        if not access_token:
            return Response({"error": "Failed to obtain access token."}, status=401)
        
        site_id = "62182"
        document_type = "shift_item-sales-movement"
        resources_response = get_site_resources(site_id, document_type)

        resources_list = resources_response.get("resources", [])
        if not resources_list:
            return Response({"error": "No resources found."}, status=404)
        last_resource = resources_list[-1]

        documents_response = get_documents(last_resource)
        documents = documents_response.get("documents", [])

        item_sales_docs = [doc for doc in documents if 'item-sales' in doc.get('fileName', '')]

        ism_details_results = []
        for doc in item_sales_docs:
            xml_content = get_document(doc['path'])
            if xml_content and "<ISMDetail>" in xml_content:
                try:
                    root = ET.fromstring(xml_content)
                    for ism_elem in root.iter('ISMDetail'):
                        # Extract required fields
                        def get_text(elem, tag):
                            found = elem.find(tag)
                            return found.text if found is not None else None

                        # ISMSellPriceSummary and ISMSalesTotals are nested
                        sell_price_summary = ism_elem.find('ISMSellPriceSummary')
                        sales_totals = sell_price_summary.find('ISMSalesTotals') if sell_price_summary is not None else None

                        ism_detail = {
                            "ItemID": get_text(ism_elem, "ItemID"),
                            "Description": get_text(ism_elem, "Description"),
                            "SellingUnits": get_text(ism_elem, "SellingUnits"),
                            "ActualSalesPrice": get_text(sell_price_summary, "ActualSalesPrice") if sell_price_summary is not None else None,
                            "SalesQuantity": get_text(sales_totals, "SalesQuantity") if sales_totals is not None else None,
                            "SalesAmount": get_text(sales_totals, "SalesAmount") if sales_totals is not None else None,
                            "DiscountAmount": get_text(sales_totals, "DiscountAmount") if sales_totals is not None else None,
                            "DiscountCount": get_text(sales_totals, "DiscountCount") if sales_totals is not None else None,
                            "PromotionAmount": get_text(sales_totals, "PromotionAmount") if sales_totals is not None else None,
                            "PromotionCount": get_text(sales_totals, "PromotionCount") if sales_totals is not None else None,
                            "RefundAmount": get_text(sales_totals, "RefundAmount") if sales_totals is not None else None,
                            "RefundCount": get_text(sales_totals, "RefundCount") if sales_totals is not None else None,
                            "TransactionCount": get_text(sales_totals, "TransactionCount") if sales_totals is not None else None,
                        }
                        ism_details_results.append(ism_detail)
                except ET.ParseError:
                    continue  # skip malformed XML

        return Response(ism_details_results)