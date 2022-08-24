# AuctioNation-WoW 2 **Back-end**
## About AuctioNation Project:
*To check out the first version's source go to:
https://github.com/WojciakW/Auctionation-WoW*

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
        - Custom back-end handling driver using psycopg2,
        - PostgreSQL Database,
        - FastAPI (**TODO**),
        - Linux cron (**TODO**)
    - Front-end:
        - A front-end framework (currently not decided, **TODO**)

### Key features:
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
