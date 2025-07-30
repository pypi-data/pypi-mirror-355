# AIGuardrail: AI Content Guardrails

**AIGuardrail** is a comprehensive Python library designed to evaluate and safeguard AI-generated content. It provides robust checks for safety, factual consistency, readability, privacy, token efficiency, and protection against malicious content.

---

## 🚀 Features

- **Output Moderation**: Detect toxic, offensive, or inappropriate language.
- **Factual Consistency & Hallucination Detection**: Prevent AI-generated inaccuracies or hallucinated information.
- **PII Redaction**: Identify and flag personally identifiable information (PII).
- **Prompt Injection Protection**: Detect potential prompt injection attacks.
- **Token Management**: Optimize content length based on token limits.
- **Response Quality Checks**: Evaluate readability, verbosity, and bias in AI outputs.

---

## 📦 Installation

Install `aiguardrail` via pip:

```bash
pip install aiguardrail
```

## 🛠️ Usage
Evaluate text quickly against all available guardrails:

```python
from aiguardrail.guardrails import evaluate_guardrails

text = "According to the source, this event took place in March."

results_df, final_score = evaluate_guardrails(text)

print(results_df)
print(f"Overall Guardrail Score: {final_score}")

```

## Evaluate specific guardrails only:

```python
specific_guardrails = ["GR-S-001", "GR-Q-005", "GR-C-002"]

results_df, final_score = evaluate_guardrails(text, selected_guardrail_ids=specific_guardrails)

print(results_df)
print(f"Overall Guardrail Score: {final_score}")

```

## 📚 Available Guardrails
Retrieve metadata about all guardrails easily:

```python
from aiguardrail.guardrails import list_available_guardrails

guardrails = list_available_guardrails()
for gr in guardrails:
    print(f"{gr['id']} - {gr['name']} [{gr['area']}]")

```

Example output:
```css
GR-S-001 - Output Moderation [Security]
GR-Q-001 - Hallucination Detection [Quality]
GR-S-005 - PII Redaction [Security]
...

```


## 📜 License
Guardrails-Eval is licensed under the MIT License. See LICENSE for details.

## ‍💻 Author
### SHUBHAM GANESH MHASKE

### Email: mhaskeshubham1200@gmail.com



⭐ Enjoy using aiguardrail !
