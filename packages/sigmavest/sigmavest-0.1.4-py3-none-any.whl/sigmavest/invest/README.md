
## Layers

```mermaid
flowchart TD
    CLI -->|Service Request, Service Response| Service
    Service -->|Domain Models| Domain
    Repository -->|Domain Models| Domain
    Service -->|Persistence| Repository
```


## CLI

* invest
  * portfolio
    * list
    * create
    * update
    * holdings
  * security
    * buy
    * sell
    * dividend
  * data
    * import
    * export
  