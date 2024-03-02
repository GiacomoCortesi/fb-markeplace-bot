# Facebook Marketplace Telegram bot

Python implementation of a telegram bot that allows
monitoring desired products from the facebook marketplace
and receive notifications whenever hot deals are found.

Since facebook does not expose a REST API for dealing with marketplace products,
this implementation use a combination of beautiful soup and splinter to crawl the marketplace html
data and fetch products information.

It allows monitoring multiple independently configurable products.

Supported commands:  
**/show** - display all configured monitoring products  
**/selected** - display currently selected product for editing  
**/select** <product-name> - select specified product for editing  
**/add** <product-name> - add a new product  
**/delete** <product-name> - delete specified product  
**/keywords** <keywords> - setup search keywords for the selected products  
**/location** <postal_code> <country_code> - setup location for restricting product research  
**/price** <min> <max> - setup (optional) price range for restricting product research  
**/radius** <km> - setup (optional) km radius for restricting product research  
**/interval** <seconds> - setup (optional) the facebook marketplace crawling interval (default 60 seconds)