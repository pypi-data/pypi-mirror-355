# Quake API Python SDK

A Python client for interacting with the Quake API (quake.360.net).

## Features

-   Easy-to-use client for all Quake API v3 endpoints.
-   Handles API authentication and common request parameters.
-   Custom exceptions for specific API errors.
-   Session management for efficient requests.

## Installation

```bash
pip install quake-sdk
```

或指定版本：

```bash
pip install quake-sdk==0.3.0
```

You can also install directly from the repository (once it's public):
```bash
pip install git+https://github.com/Explorer1092/quake_sdk.git#subdirectory=quake_sdk_py
```

## Prerequisites

-   Python 3.11+
-   A Quake API Key. You can obtain one from your [Quake User Center](https://quake.360.net/quake/#/user/info) (replace with actual link if different).

## Usage

The SDK now uses Pydantic models for request parameters and response data, providing type hinting and validation.

```python
from quake_sdk import (
    QuakeClient,
    QuakeAPIException,
    RealtimeSearchQuery,
    ScrollSearchQuery,
    AggregationQuery,
    FaviconSimilarityQuery
)

# Replace 'YOUR_API_KEY' with your actual Quake API key
api_key = "YOUR_API_KEY"

try:
    # Using the client as a context manager ensures the session is closed
    with QuakeClient(api_key=api_key) as client:
        # Get User Info
        user_info_response = client.get_user_info()
        if user_info_response.data:
            print("User Info (Username):", user_info_response.data.user.username)
            print("User Credit:", user_info_response.data.credit)

        # Search Service Data
        service_query_params = RealtimeSearchQuery(
            query="port: 80 AND country_cn: \"中国\"",
            size=2,
            latest=True
        )
        service_search_response = client.search_service_data(query_params=service_query_params)
        print(f"\nService Search Results (first {service_query_params.size} for '{service_query_params.query}'):")
        if service_search_response.data:
            for item in service_search_response.data:
                title = item.service.http.title if item.service and item.service.http else "N/A"
                print(f"- IP: {item.ip}, Port: {item.port}, Title: {title}")
        if service_search_response.meta and service_search_response.meta.pagination:
             print(f"Total service results: {service_search_response.meta.pagination.total}")


        # Scroll Service Data (Deep Pagination)
        print("\nScrolling service data...")
        scroll_query_params_page1 = ScrollSearchQuery(
            query="app:\"Apache Tomcat\"",
            size=1
        )
        page1_response = client.scroll_service_data(query_params=scroll_query_params_page1)
        if page1_response.data:
            print("Page 1 Data Count:", len(page1_response.data))
        
        pagination_id = page1_response.meta.pagination_id if page1_response.meta else None

        if pagination_id:
            scroll_query_params_page2 = ScrollSearchQuery(
                query="app:\"Apache Tomcat\"", # Query must remain the same for subsequent scroll requests
                size=1,
                pagination_id=pagination_id
            )
            page2_response = client.scroll_service_data(query_params=scroll_query_params_page2)
            if page2_response.data:
                print("Page 2 Data Count:", len(page2_response.data))
            # Continue scrolling as needed...

        # Search Host Data
        host_query_params = RealtimeSearchQuery(
            query="os: \"Linux\" AND country_cn: \"美国\"",
            size=2
        )
        host_search_response = client.search_host_data(query_params=host_query_params)
        print(f"\nHost Search Results (first {host_query_params.size} for '{host_query_params.query}'):")
        if host_search_response.data:
            for item in host_search_response.data:
                location_cn = item.location.country_cn if item.location else "N/A"
                print(f"- IP: {item.ip}, OS: {item.os_name}, Location: {location_cn}")

        # Aggregate Service Data
        agg_query_params = AggregationQuery(
            query="country_cn: \"中国\"",
            aggregation_list=["service.name", "port"],
            size=3
        )
        agg_response = client.aggregate_service_data(query_params=agg_query_params)
        print(f"\nService Aggregation for '{agg_query_params.query}' (top {agg_query_params.size} for each):")
        if agg_response.data:
            for field, buckets in agg_response.data.items():
                print(f"  Field: {field}")
                for bucket in buckets:
                    print(f"    - {bucket.key}: {bucket.doc_count}")

        # Favicon Similarity Search
        favicon_query_params = FaviconSimilarityQuery(
            favicon_hash="0488faca4c19046b94d07c3ee83cf9d6", # Example hash
            similar=0.95,
            size=2
        )
        similar_icons_response = client.query_similar_icons(query_params=favicon_query_params)
        print(f"\nSimilar Favicons to '{favicon_query_params.favicon_hash}':")
        if similar_icons_response.data:
            for item in similar_icons_response.data:
                print(f"- Hash: {item.key}, Count: {item.doc_count}")

except QuakeAPIException as e:
    print(f"An API error occurred: {e}")
except ValueError as e: # Can be raised by Pydantic validation or API key check
    print(f"A value or validation error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

## API Endpoints Covered

The SDK provides methods for the following Quake API v3 endpoints:

**User:**
*   `/user/info`

**Service Data:**
*   `/filterable/field/quake_service`
*   `/search/quake_service`
*   `/scroll/quake_service`
*   `/aggregation/quake_service` (GET for fields, POST for query)

**Host Data:**
*   `/filterable/field/quake_host`
*   `/search/quake_host`
*   `/scroll/quake_host`
*   `/aggregation/quake_host` (GET for fields, POST for query)

**Favicon:**
*   `/query/similar_icon/aggregation`

Refer to the [official Quake API documentation](https://quake.360.net/quake/#/help?id=5f9f9b9b3b9b3b9b3b9b3b9b) for detailed information on query syntax and parameters. (Replace with the correct link from `vendor/sdk.md` if different).

## Error Handling

The SDK defines custom exceptions that inherit from `QuakeAPIException`:
*   `QuakeAuthException`: For authentication issues (e.g., invalid API key).
*   `QuakeRateLimitException`: When API rate limits are exceeded.
*   `QuakeInvalidRequestException`: For errors in the request (e.g., bad parameters, syntax errors).
*   `QuakeServerException`: For server-side errors on Quake's end.

These can be caught specifically to handle different error scenarios.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue.
(You might want to add more specific contribution guidelines later).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
(Ensure you add a LICENSE file if you choose MIT or another license).
