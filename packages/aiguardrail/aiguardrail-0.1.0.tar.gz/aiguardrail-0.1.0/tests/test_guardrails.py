import unittest
from aiguardrail import evaluate_guardrails

class TestGuardrails(unittest.TestCase):

    def test_evaluate_guardrails(self):
        text = "Safe and factual AI content."
        df, score = evaluate_guardrails(text)
        self.assertGreater(score, 80)

if __name__ == "__main__":
    unittest.main()