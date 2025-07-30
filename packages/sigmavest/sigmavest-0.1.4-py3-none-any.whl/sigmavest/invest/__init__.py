"""

```mermaid
flowchart TD
    CLI -->|Service Request, Service Response| Service
    Service -->|Domain Models| Domain
    Repository -->|Domain Models| Domain
    Service -->|Persistence| Repository
```

"""
