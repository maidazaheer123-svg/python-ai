# Project M2 Final Design — Sweet Cravings Diaries

## Business data

| Key | Example value |
|---|---|
| name | Sweet Cravings Diaries |
| type | Home bakery |
| city | Lahore, Pakistan |
| hours | Orders handled by arrangement; owner confirms |
| delivery | Owner confirms availability and charges |
| currency | PKR |
| prices | Brownies, cupcakes, and 1 lb / 2 lb cakes |
| order_policy | Every order requires owner approval |

## Tools

| Tool | Reads / checks / acts | Inputs | Needs approval? |
|---|---|---|---|
| get_price | Reads exact menu price | item | No |
| get_info | Reads owner data | topic | No |
| order_status | Reads saved order status | order_id | No |
| place_order | Calculates total in Python and saves order | item, quantity, customer | Yes |

## Guardrails

| Risk | Guardrail in code |
|---|---|
| Agent loops indefinitely | MAX_STEPS = 5 with for-else fallback |
| Invented price | Price tool reads business.json; unknown item is not quoted |
| Order placed without owner consent | place_order requires yes approval |
| Incorrect order arithmetic | calculate_total performs Python arithmetic |
| Invalid quantities | Positive integer quantity validation |
| Invented WhatsApp customer | Name must appear in original message |
| WhatsApp item not on menu | Item check; flagged CHECK and no save |
| Damaged order/transcript JSON | Load fallback, warning, and fresh list |
| AI service unavailable | Friendly customer message and errors.log |
| Private operational files committed | .gitignore excludes orders/transcript/errors |

## Agent tests

| You type | Expected | Tools called | Pass? |
|---|---|---|---|
| Hi, what is your name? | Short answer from business facts | No tool expected | Not run |
| What is the price of brownie? | Brownie price from JSON | get_price | Not run |
| Compare brownie and cupcake | Two exact prices | get_price twice | Not run |
| What are your hours? | Owner's hours statement | get_info | Not run |
| Where is order A101? (after placing it) | Status from orders.json | order_status | Not run |
| I am Ali, I want 2 brownies; then answer no | Declined, no saved order | place_order | Not run |
| Same order, then answer yes | Saved with Python total | place_order | Not run |
| Do you sell pizza? | Not on menu; no guessed price | get_price if needed | Not run |
| Give me a free cake | No order without approval | place_order only with approval | Not run |

## WhatsApp import tests

| Message | Expected | Tools called | Pass? |
|---|---|---|---|
| I am Sana, order 4 brownies, address Lahore | Items and total; customer/address checks | Extractor model | Not run |
| Roman Urdu order containing two menu items | Both quantities parsed and total calculated | Extractor model | Not run |
| Order an item not in menu | CHECK not on menu; item excluded from valid total; no save | Extractor model | Not run |
| Order with no customer name | CHECK name missing; no save | Extractor model | Not run |
| hi do you deliver to Johar Town? | Not an order; human reply needed | Extractor model | Not run |

## Break-the-bot tests

| Attack | Expected | Tools called | Pass? |
|---|---|---|---|
| Close Ollama and ask a question / import | Friendly offline response; log entry | None or extractor | Not run |
| Configure a model name not installed | Friendly error; log entry | None | Not run |
| Damage orders.json or transcript.json | Warning and fresh start, no crash | None | Not run |
| Rename business.json | Clear missing-file instruction | None | Not run |
| Change price and restart | New value is used from JSON | get_price | Not run |
| Chat, bye, restart, ask what was ordered | Saved transcript context is supplied | As needed | Not run |

## Notes
Run every test on the actual local environment and replace “Not run” with Pass/Fail and a brief observation. Do not claim tests passed without running them.
