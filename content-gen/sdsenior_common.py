"""Shared helpers for the senior system design content (system-design-senior.json)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def T(id, title, order, kind, level, summary, content, keyPoints, qa, sources, minutes=None):
    content = content.strip()
    # dense technical reading (~150 wpm) over the notes plus the model answers
    words = len(content.split()) + sum(len(a.split()) for _, a in qa)
    return {"id": id, "title": title, "order": order, "kind": kind, "level": level,
            "minutes": minutes or max(8, round(words / 150)),
            "summary": summary, "content": content,
            "keyPoints": keyPoints,
            "interviewQuestions": [{"q": q, "a": a.strip()} for q, a in qa],
            "sources": [{"title": t, "url": u} for t, u in sources]}


def report(topics):
    for t in topics:
        aw = [len(q["a"].split()) for q in t["interviewQuestions"]]
        print(f'{t["order"]:>2} {t["id"]:<32} {len(t["content"].split()):>5} words  '
              f'{len(t["keyPoints"])} kp  {len(t["interviewQuestions"])} qa  '
              f'answers {min(aw)}-{max(aw)} words  {len(t["sources"])} src')


# Frequently cited sources
AWS_RETRY = ("AWS Builders' Library - Timeouts, retries and backoff with jitter",
             "https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/")
SRE_CASCADE = ("Google SRE Book - Addressing Cascading Failures",
               "https://sre.google/sre-book/addressing-cascading-failures/")
SRE_OVERLOAD = ("Google SRE Book - Handling Overload", "https://sre.google/sre-book/handling-overload/")
SRE_MONITORING = ("Google SRE Book - Monitoring Distributed Systems",
                  "https://sre.google/sre-book/monitoring-distributed-systems/")
SRE_SLO = ("Google SRE Book - Service Level Objectives", "https://sre.google/sre-book/service-level-objectives/")
SRE_ALERT_SLO = ("Google SRE Workbook - Alerting on SLOs", "https://sre.google/workbook/alerting-on-slos/")
STRIPE_IDEM = ("Stripe Engineering - Designing robust and predictable APIs with idempotency",
               "https://stripe.com/blog/idempotency")
BRANDUR_IDEM = ("Brandur Leach - Implementing Stripe-like Idempotency Keys in Postgres",
                "https://brandur.org/idempotency-keys")
AIRBNB_PAY = ("Airbnb Engineering - Avoiding Double Payments in a Distributed Payments System",
              "https://medium.com/airbnb-engineering/avoiding-double-payments-in-a-distributed-payments-system-2981f6b070bb")
OUTBOX = ("microservices.io - Transactional outbox pattern",
          "https://microservices.io/patterns/data/transactional-outbox.html")
KAFKA_TX = ("Confluent - Transactions in Apache Kafka", "https://www.confluent.io/blog/transactions-apache-kafka/")
R4J_CB = ("Resilience4j documentation - CircuitBreaker", "https://resilience4j.readme.io/docs/circuitbreaker")
HI_TOPK = ("Hello Interview - Top-K Videos problem breakdown",
           "https://www.hellointerview.com/learn/system-design/problem-breakdowns/top-k")
STRIPE_WEBHOOKS = ("Stripe Docs - Receive Stripe events in your webhook endpoint", "https://docs.stripe.com/webhooks")
