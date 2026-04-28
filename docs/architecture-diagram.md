# Architecture & Data Flow Diagram

```mermaid
flowchart TD
    A[👤 Internal User] -->|Uploads Salesforce CSV/Excel| B[Streamlit Application\nSnowflake Product]
    B -->|Company name search queries| C[DuckDuckGo\nPublic Web Search]
    C -->|Publicly available firmographic data| B
    B -->|Company name + public web snippets\nHTTPS/TLS Encrypted| D[Azure OpenAI API\nGPT-4o-mini]
    D -->|Structured firmographic output\nHTTPS/TLS Encrypted| B
    B -->|Enrichment results displayed for review| A
    A -->|Manual CSV export if required| E[📄 CSV Output\nNo system write-back]

    style A fill:#f0f0f0,stroke:#333
    style B fill:#1a9cd8,color:#fff,stroke:#0e7ab5
    style C fill:#f5a623,color:#fff,stroke:#d4891a
    style D fill:#107c41,color:#fff,stroke:#0a5c30
    style E fill:#f0f0f0,stroke:#333
```

## Notes
- All communication with Azure OpenAI is encrypted in transit via HTTPS/TLS
- The API key is stored as a secured environment variable
- No data is written back to any internal system
- DuckDuckGo receives company names only as search queries
- No PII or sensitive data is transmitted at any point
