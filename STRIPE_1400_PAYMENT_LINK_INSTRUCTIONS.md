# Lady D Corrected Stripe Payment Link Instructions

Updated: 2026-08-30

## Correct payment facts

- Customer: Susan "Lady D" Damon
- Email: 1ladysd23@gmail.com
- Current package total: $2,000
- Paid to date: $600 ($200 prior payment + $400 check)
- Remaining balance: $1,400
- Juan Damon testimony/autobiography book: separate future scope, not part of this checkout

## Current Stripe status

- Status: active and verified in the live Island Development Crew Stripe account
- Checkout: https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a
- Payment Link ID: plink_1UANGWQQMWQl4qqGNcSEzJwR
- Created: 2026-08-30
- Automatic tax: off
- Adjustable quantity: off
- Post-payment invoice fee: off

## Dashboard fields

- Product name: Susan Damon - Corrected Publishing Package Remaining Balance
- Amount: $1,400.00 USD
- Description: Remaining balance for current Lady D publishing package: 3 devotional books, 3 companion journals, 31-day visual devotional, author review hub, dashboard, KDP/digital preparation. Juan Damon testimony separated from current package.
- Metadata:
  - client=Susan Damon
  - project=Lady D publishing package
  - package_total=2000
  - paid_credit=600
  - remaining_balance=1400
  - testimony_scope=separate

## Regeneration

The verified checkout is the `PAYMENT_LINK` source of truth in `scripts/build_lady_d_hub.py`. After changing proposal or hub content, rerun:

```bash
python3 scripts/build_lady_d_hub.py
npm run build
```

Then verify:

```bash
rg -n "\$2,300|\$2,500|buy\.stripe|Pay \$2,300" susan-damon-publishing-proposal.html public/susan-damon-publishing-proposal.html
```

The `buy\.stripe` check should return only the verified corrected link, never the retired checkout.
