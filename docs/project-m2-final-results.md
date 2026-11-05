# AI Quality Test Results — Sweet Cravings Diaries

## Test records (complete after running)

| Test input | AI mistake / near miss observed | What the code checks | Outcome |
|---|---|---|---|
| WhatsApp order with a name absent from message | Extractor may infer a customer name | Extracted name must appear in source message | Pending live test |
| WhatsApp order containing an unlisted product | Extractor may add an unknown menu item | Menu membership check; item flagged and order not saved | Pending live test |
| User asks for a product price not in menu | Model may try to guess | `get_price` returns “not on the menu” and no quote | Pending live test |
| User asks to place order and declines approval | Agent might continue as if accepted | `place_order` saves only when owner types `yes` | Pending live test |

## Improvement / added check
The WhatsApp importer checks that the extracted customer name is present in the original message, verifies each item against `business.json`, validates positive quantities, and only saves when there are no checks and the owner approves. Python calculates the total from the configured menu prices.

## Honest testing note
These are test scenarios and expected checks, not claimed execution results. Run them locally with Ollama and fill in observed results before submission.
