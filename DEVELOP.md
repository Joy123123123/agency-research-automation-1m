# DEVELOP Branch — Agency Research Automation

এই ব্রাঞ্চ হলো **ডেভেলপমেন্ট ইন্টিগ্রেশন ব্রাঞ্চ**।

## এই ব্রাঞ্চের নিয়ম

- সব `feature/*` ব্রাঞ্চ এখানে merge হবে
- `main`-এ merge করার আগে এখানে সব ফিচার টেস্ট হবে
- কখনো directly `main`-এ push করবেন না

## ওয়ার্কফ্লো

```
feature/xyz → develop → staging → main
```

## ডেভেলপমেন্ট নোটস

- Python 3.10+ required
- সব টেস্ট পাস করতে হবে: `pytest tests/ -v`
- Code review required before merge to staging
