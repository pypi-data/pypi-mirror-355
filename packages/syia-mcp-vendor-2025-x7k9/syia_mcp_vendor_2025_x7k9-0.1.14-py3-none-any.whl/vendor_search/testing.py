from typing import Dict, Any, List, Union
from databases import TypesenseClient
import mcp.types as types
import json
import logging

logger = logging.getLogger(__name__)

def get_vendor_contact_info(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
        """
        Handle Typesense get contact info tool
        
        """
        typesense_client = TypesenseClient()
        collection = "vendor4"

        if not collection:
            raise ValueError("Collection name is required")
        
        try:
            include_fields = "address, contactEmail, contactNumber, vendorName"
            query = {
                "q": arguments['vendorName'],
                "query_by": "vendorName",
                "include_fields": include_fields
            }

            results = typesense_client.collections[collection].documents.search(query)
            
            # Format the results
            formatted_results = {
                "found": results.get("found", 0),
                "out_of": results.get("out_of", 0),
                "page": results.get("page", 1),
                "hits": [hit.get("document") for hit in results.get("hits", [])]
            }
            
            # Convert the results to JSON string
            formatted_text = json.dumps(formatted_results, indent=2)
            # Create TextContent with all required fields in correct structure
            content = types.TextContent(
                type="text",                # Required field
                text=formatted_text,        # The actual text content
                title=f"Search results for '{collection}'",
                format="json"
            )
            
            # Log the content for debugging
            logger.log(f"Created search results TextContent: {type(content)}")
            
            return [content]
        except Exception as e:
            logger.error(f"Error searching collection {collection}", e)
            raise ValueError(f"Error searching collection: {str(e)}")
        
if __name__ == "__main__":
    get_vendor_contact_info({"vendorName": "Wartsila"})