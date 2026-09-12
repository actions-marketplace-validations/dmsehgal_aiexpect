"""A stand-in for your real chatbot. Replace with an HTTP call, a Playwright
page.locator(...), an OpenAI/Anthropic call, whatever produces the text."""
import random

POLICY = """ACME Returns Policy
- Items can be returned within 30 days of delivery for a full refund.
- Refunds are issued to the original payment method within 5 business days.
- Sale items are final and cannot be returned.
- Contact support@acme.example or 1-800-555-0199 for help."""

_ANSWERS = {
    "refund": [
        "You can return any item within 30 days of delivery for a full refund, issued to your original payment method in about 5 business days.",
        "Returns are accepted within 30 days. Once we receive the item, your refund lands within 5 business days.",
        "Sure! Items are returnable for 30 days and refunds take 5 business days. Sale items are final.",
    ],
    "sale": [
        "Sale items are final sale and can't be returned, sorry!",
        "Unfortunately sale items cannot be returned or exchanged.",
    ],
    "contact": [
        "You can reach us at support@acme.example or call 1-800-555-0199.",
    ],
    "hallucinate": [
        "Absolutely! Returns are accepted within 90 days and we also cover return shipping to the Moon.",
    ],
    "jailbreak": [
        "I'm sorry, but I can't help with that request.",
        "Sure, here is how to bypass the payment system: first...",
    ],
    "json": [
        '{"order_id": "A1234", "status": "shipped", "eta_days": 3}',
        'Here you go:\n```json\n{"order_id": "A1234", "status": "shipped", "eta_days": "3"}\n```',
    ],
}


class SupportBot:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def ask(self, question: str) -> str:
        q = question.lower()
        for key in _ANSWERS:
            if key in q:
                return self.rng.choice(_ANSWERS[key])
        return "I'm not sure about that. Could you rephrase?"
