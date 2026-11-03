# Project M2 CP1: Design (AI Content Studio)

Replace the Sweet Crumbs example with your own business if it is different.

## Facts

| Key | Value |
|-----|-------|
| name | Sweet Crumbs |
| type | bakery |
| city | Lahore |
| hours | 9 am to 10 pm, every day |
| delivery | 200 PKR, free for orders from 3000 PKR |
| prices | mango tart 0 (coming soon), chocolate cake 1,500 PKR, cupcake 250 PKR, brownie 300 PKR |

## Tones

| Tone | Description sent to the AI |
|------|----------------------------|
| fun | playful and full of energy, short sentences |
| premium | elegant and calm, focused on quality |
| urgent | exciting, limited-time feel, tells people to order today |

## Which model for which job

| Job | Model and temperature | Why |
|-----|-----------------------|-----|
| Menu descriptions (/menu) | creative, 0.8 | Marketing text should be varied |
| Social media posts (/post) | creative, 0.8, streamed | Posts need creativity, and streaming shows the answer start at once |
| Customer chat | precise, 0.2 | Answers must be focused and stick to the facts |
| Prices (/price) | no AI, dictionary lookup | Free, instant and can never be invented |
| Coming-soon items in /menu | no AI, skipped with continue | Nothing to describe, so no tokens spent |

## Feature tests

Run every row, then fill in the "Pass?" column honestly (Yes / No + note).

| You type | Expected | Pass? |
|----------|----------|-------|
| /menu | Price-0 item skipped, numbered menu, prices with commas | |
| /post with each of your tones (fun, premium, urgent) | Post streams word by word, in a different style each time | |
| /post pirate | Default tone (fun) used, no KeyError | |
| /price CUPCAKE (real item in capitals) | Correct price | |
| /price mango tart (price-0 item) | "Coming soon" | |
| /price pizza (not on the menu) | "Not on our menu", no crash | |
| My name is Ali, then What is my name? | Remembers the name | |
| /reset, then What is my name? | Does not know | |
| Press Enter with no text | Asks again | |
| BYE | Goodbye + session report with all numbers | |