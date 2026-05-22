# GDPR Compliance Framework: Alvitur.is

## 1. Data Inventory (ROPA)
- Allar gagnaflæðisleiðir eru skráðar í `audit_chain`.
- Persónuupplýsingar (PII) eru dulkóðaðar í hvíld (At-rest).

## 2. Crypto-Shredding Policy
- Við eyðum ekki dulkóðuðu keðjunni (audit integrity).
- Við eyðum dulkóðunarlyklum fyrir einstaka notendur (Crypto-shredding) þegar eyðingarkrafa berst.

## 3. Sub-processor List
- OpenRouter (LLM routing).
- Mojeek (Search context).
- Stripe (Billing).
