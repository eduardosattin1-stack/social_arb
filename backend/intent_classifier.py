import re

INTENT_PATTERNS = {
    "purchased": [
        r"just bought", r"just purchased", r"got mine", r"received my",
        r"finally got", r"picked up", r"ordered", r"arrived",
    ],
    "intends_to_purchase": [
        r"want to buy", r"thinking about", r"planning to get", r"looking at",
        r"considering", r"should i buy", r"worth buying", r"might get",
    ],
    "switching_to": [
        r"switching to", r"moved to", r"replaced.*with", r"better than.*",
        r"finally switched", r"no more.*going with",
    ],
    "switching_from": [
        r"switching from", r"leaving", r"done with", r"cancelled my",
        r"unsubscribed", r"no longer using", r"ditched",
    ],
    "recommends": [
        r"highly recommend", r"must have", r"love this", r"game changer",
        r"best purchase", r"changed my life", r"you need this",
    ],
    "complains": [
        r"hate", r"terrible", r"worst", r"broken", r"doesn't work",
        r"disappointed", r"refund", r"scam", r"waste of money",
    ],
    "sold_out_unavailable": [
        r"sold out", r"out of stock", r"can't find", r"everywhere",
        r"impossible to get", r"waitlist", r"backordered",
    ],
    "aspirational": [
        r"one day", r"someday", r"dream", r"goal", r"wish i could",
        r"saving up for", r"when i can afford",
    ],
}


def classify_intent(text: str) -> tuple[str, float]:
    text_lower = text.lower()
    scores = {}

    for intent, patterns in INTENT_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches > 0:
            scores[intent] = matches

    if scores:
        best_intent = max(scores, key=scores.get)
        confidence = min(0.5 + scores[best_intent] * 0.15, 0.95)
        return best_intent, round(confidence, 2)

    return "neutral", 0.5


if __name__ == "__main__":
    tests = [
        "Just bought the new Crocs, they sold out everywhere",
        "Thinking about switching from Peloton to Apple Fitness",
        "This is the worst customer service I've ever experienced",
        "Highly recommend the YETI tumbler, game changer!",
        "Can't find the Celsius drink anywhere, sold out at all stores",
    ]
    for t in tests:
        intent, score = classify_intent(t)
        print(f"[{intent} ({score})] {t[:60]}...")
