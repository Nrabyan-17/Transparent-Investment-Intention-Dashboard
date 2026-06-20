# Knowledge-Based System Rules Documentation

**Total: 15 rules dalam 5 kategori**

Threshold values di-derive dari statistik dataset (Q25/Q75) untuk grounded decision boundaries.

## Kategori 1: Capacity Assessment (4 rules)

Berdasarkan **MiFID II Article 25** (Suitability Assessment) dan **Modern Portfolio Theory**.

| Rule ID | Trigger Condition | Implication |
|---------|------------------|-------------|
| R1.1 | investmentCapacity = CAP_LT30K | Profil Conservative/Income |
| R1.2 | investmentCapacity = CAP_GT300K | Profil Aggressive |
| R1.3 | investmentCapacity = 30K-300K | Profil Balanced/Income |
| R1.4 | has_questionnaire = 0 | Risk profile dengan reliabilitas terbatas |

## Kategori 2: Trading Behavior (4 rules)

Berdasarkan **Behavioral Finance** literature (Shefrin & Statman, Kahneman & Tversky).

| Rule ID | Trigger Condition | Implication |
|---------|------------------|-------------|
| R2.1 | buy_ratio > 0.65 | Long-term accumulator → Aggressive/Balanced |
| R2.2 | buy_ratio < 0.40 | Profit-taker → Income/Conservative |
| R2.3 | sell_to_buy_value_ratio > 1.5 | Net seller behavior |
| R2.4 | total_invested > 18.853 EUR | High exposure → Aggressive/Balanced |

## Kategori 3: Portfolio Diversification (3 rules)

Berdasarkan **Modern Portfolio Theory** (Markowitz, 1952).

| Rule ID | Trigger Condition | Implication |
|---------|------------------|-------------|
| R3.1 | unique_stocks_traded >= 5 | Mature diversification |
| R3.2 | unique_stocks_traded = 1 | High idiosyncratic risk |
| R3.3 | unique_sectors_traded >= 3 | Cross-sectoral diversification |

## Kategori 4: Temporal Pattern (2 rules)

Berdasarkan **Lifecycle Investment Theory** dan **Behavioral Finance**.

| Rule ID | Trigger Condition | Implication |
|---------|------------------|-------------|
| R4.1 | investment_period_days > 1583 | Long-term investor consistency |
| R4.2 | avg_days_between_transactions < 39.7 | Active high-frequency trader |

## Kategori 5: Channel & Segment (2 rules)

Berdasarkan **Diffusion of Innovation Theory** (Rogers, 2003) dan MiFID II Client Categorization.

| Rule ID | Trigger Condition | Implication |
|---------|------------------|-------------|
| R5.1 | digital_ratio > 0.75 | Tech-savvy investor (Aggressive correlation) |
| R5.2 | customerType = Premium | High net worth client |

## References

1. Markowitz, H. (1952). Portfolio Selection. *Journal of Finance*, 7(1), 77-91.
2. Shefrin, H., & Statman, M. (1985). The Disposition to Sell Winners Too Early. *Journal of Finance*, 40(3).
3. Kahneman, D., & Tversky, A. (1979). Prospect Theory. *Econometrica*, 47(2).
4. Barber, B. M., & Odean, T. (2001). Boys Will Be Boys: Gender, Overconfidence. *Quarterly Journal of Economics*.
5. Rogers, E. M. (2003). *Diffusion of Innovations* (5th ed.). Free Press.
6. European Commission. (2014). MiFID II Directive 2014/65/EU.
