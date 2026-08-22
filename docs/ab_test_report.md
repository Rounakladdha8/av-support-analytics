# A/B Test Report: Legacy Manual Triage vs. Auto-Routing

Sample sizes: legacy_manual n=17,222, auto_routing n=17,486

## 1. Resolution Time (hours) — Welch's t-test
- Legacy mean: 18.68 hrs (sd=17.95)
- Auto-routing mean: 14.95 hrs (sd=14.73)
- t=-21.101, p=3.45e-98
- Cohen's d=-0.227
- Relative change: -19.9%

## 2. First Response Time (hours) — Welch's t-test
- Legacy mean: 4.67 hrs
- Auto-routing mean: 3.74 hrs
- t=-19.976, p=2.92e-88

## 3. Escalation Rate — Chi-square test of independence
- Legacy escalation rate: 16.9%
- Auto-routing escalation rate: 11.3%
- chi2=230.800, p=3.99e-52

## 4. CSAT Score — Mann-Whitney U test (ordinal outcome)
- Legacy median CSAT: 3.0 (mean=3.30)
- Auto-routing median CSAT: 4.0 (mean=3.54)
- U=173160975.5, p=1.20e-148

## Sample Size / Power Note
- With n≈17,222 per group and pooled SD≈16.5 hrs, the minimum detectable effect at ~80% power / alpha=0.05 is roughly 0.35 hrs — well below the observed difference, so the result is not simply an underpowered fluke.

## Interpretation
Auto-routing shows a statistically significant reduction in resolution time and first response time, a significantly lower escalation rate, and higher CSAT, with a small-to-moderate effect size. This is a simulated experiment (see README for methodology and limitations), structured the way a real support-workflow A/B test would be designed, run, and reported.
