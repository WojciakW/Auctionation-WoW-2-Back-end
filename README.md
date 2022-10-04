# AuctioNation-WoW 2 **Back-end**
**Work in progress**
## About AuctioNation Project:
*To check out the first version's source go to:
https://github.com/WojciakW/Auctionation-WoW*

*All data is provided by Blizzard's WoW Classic API.
Item data thanks to **wow-classic-items** https://github.com/nexus-devs/wow-classic-items*

It is a social web app for World of Warcraft Classic live auction house statistics created using the following:
-   **First version (AuctioNation-WoW 1)**:
    - Python,
    - Django,
    - Django REST Framework,
    - PostgreSQL Database,
    - Bootstrap CSS,
    - Vanilla JS + Chart.js (graphs)
-   **Second version (AuctioNation-WoW 2)**:
    - **Back-end**:
        - Python,
        - PostgreSQL Database
        - Custom reads/writes controller using *psycopg2*, *numpy* and *multiprocessing* (**in progress**),
        - API request/response handling using FastAPI (**TODO**),
        - Linux cron job scheduler (**TODO**)
    - Front-end:
        - A front-end framework (currently not decided, possibly React **TODO**)

### About:
 Controller's job is to cyclically fetch official WoW auction data (about 1.5M entries) **and** handle all database writes and reads on each realm. When a single API HTTP request is made, a new *ItemReadHandler* or *AuctionReadHandler* class instance is born, most willingly using as much multiprocessing power as possible.

 **Overall back-end diagram:**
 ![](https://github.com/WojciakW/Auctionation-WoW-2-Back-end/blob/master/imgs/diagram2.png?raw=true)


### AuctioNation project Key features:
- Automated 1-hour-cycle database handling:
  - fetching live World of Warcraft auctions data from official Blizzard API,
  - computing various statistics,
  - archiving data.
- Possibility to view every single item data on every official realm, faction side, that is:
  - auctions count,
  - lowest buyout,
  - mean buyout,
  - median buyout,
- Data presented in form of graphs,
- User account base,
- Support for comments on any item stats,
- Various UX, like:
    - one field for item OR auction search,
    - dynamic page rewriting,
    - user Observed items list,
