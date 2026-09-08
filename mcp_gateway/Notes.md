MCP Gateway
This is where the actual fake travel database/tools live.

The agents don't directly import these functions.

That distinction is important.

WRONG

Flight Agent
   |
   +--> import search_flights()

RIGHT

Flight Agent
   |
   +--> MCP Client
            |
            v
       MCP Gateway
            |
            v
       flight_search()
