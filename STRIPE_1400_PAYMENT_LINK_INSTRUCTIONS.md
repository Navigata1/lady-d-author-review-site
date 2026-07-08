# Lady D Corrected Stripe Payment Link Instructions

Generated: 2026-07-08

## Correct payment facts

- Customer: Susan "Lady D" Damon
- Email: 1ladysd23@gmail.com
- Current package total: $2,000
- Paid to date: $600 ($200 prior payment + $400 check)
- Remaining balance: $1,400
- Juan Damon testimony/autobiography book: separate future scope, not part of this checkout

## Current Stripe status

The local package points to `stripe-payment-link-pending-1400.html` until a real live Stripe Payment Link exists.

Attempted live CLI creation was blocked because the configured live restricted key lacks permission to create Stripe Prices/Payment Links. Use the Stripe Dashboard with an owner/admin session, or provide a live key with the required Product, Price, and Payment Link creation permissions.

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

## After the link is created

Update `PAYMENT_LINK` near the top of `scripts/build_lady_d_hub.py` from `stripe-payment-link-pending-1400.html` to the new live Stripe URL, then rerun:

```bash
python3 scripts/build_lady_d_hub.py
npm run build
```

Then verify:

```bash
rg -n "\$2,300|\$2,500|buy\.stripe|Pay \$2,300" susan-damon-publishing-proposal.html public/susan-damon-publishing-proposal.html
```

If the real live Stripe URL intentionally begins with `https://buy.stripe.com/`, the `buy\.stripe` check should return the new corrected link only, not the retired checkout.
