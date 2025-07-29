# DSPy

DSPy (Declarative Self-improving Language Programs) is a framework from Stanford NLP for algorithmically optimizing Language Model (LM) prompts and weights, especially when LMs are used in complex pipelines (e.g., multi-step reasoning, retrieval-augmented generation). Instead of manually tuning prompts, DSPy allows you to define a high-level program structure and then use optimizers (called "teleprompters") to find the best prompts or even fine-tune LM weights for your specific task and metric.

## Core Components

DSPy programs are built from a few key components:

1.  **Signatures (`dspy.Signature`)**:
    *   A declarative specification of what a DSPy module needs to do. It defines the input and output fields of a transformation.
    *   It doesn't specify *how* to do it (e.g., what prompt to use), only what the inputs and outputs are.
    *   *Example:*
        ```python
        class BasicQA(dspy.Signature):
            """Answer questions with short factoid answers."""
            question = dspy.InputField()
            answer = dspy.OutputField(desc="often between 1 and 5 words")
        ```

2.  **Modules (`dspy.Module`)**:
    *   These are the building blocks of your LM programs. DSPy provides several built-in modules, and you can create custom ones.
    *   Modules take a signature (or sometimes just use LM primitives directly) and implement the transformation.
    *   Common built-in modules:
        *   `dspy.Predict`: Given a signature, it generates a prompt (or uses a user-provided one) and calls the LM.
        *   `dspy.ChainOfThought`: Takes a signature and prompts the LM to produce step-by-step reasoning before the final answer.
        *   `dspy.ReAct`: Implements the ReAct algorithm, allowing an LM to use tools (like a search engine) to answer questions.
        *   `dspy.MultiChainComparison`: Generates multiple reasoning chains and then compares them to produce a better answer.
    *   You compose modules to build more complex pipelines.
    *   *Example (using `dspy.Predict`):*
        ```python
        # Define a simple question answering module
        qa_module = dspy.Predict(BasicQA)
        # Later, you would call it:
        # response = qa_module(question="What is the capital of France?")
        # print(response.answer)
        ```

3.  **Optimizers (Teleprompters)**:
    *   These are algorithms that tune your DSPy program. They take your program (composed of modules), a metric to optimize, and training data.
    *   They explore different prompts or even fine-tune model weights to maximize the given metric.
    *   Examples of teleprompters:
        *   `BootstrapFewShot`: Creates few-shot examples from your data.
        *   `MIPRO`: Bayesian optimization for complex pipelines.
        *   `BootstrapFinetune`: Can fine-tune smaller LMs.
    *   The optimization process is what makes DSPy "self-improving."

## Basic DSPy Program Structure (Illustrative)

Here's a conceptual idea of how you might structure a simple DSPy program:

```python
import dspy

# 1. Configure your Language Model (e.g., OpenAI, Cohere, Llama)
# This usually involves setting the model name and API key.
# Example (replace with your actual LM setup):
# turbo = dspy.OpenAI(model='gpt-3.5-turbo', api_key='YOUR_API_KEY')
# dspy.settings.configure(lm=turbo)

# 2. Define your Signature(s)
class EmailSignature(dspy.Signature):
    """Generate a polite follow-up email to a customer query."""
    customer_query = dspy.InputField(desc="The original query from the customer.")
    product_name = dspy.InputField(desc="The product the customer is asking about.")
    email_body = dspy.OutputField(desc="The generated email body.")

# 3. Define your DSPy Module(s)
class FollowUpEmailGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        # Using ChainOfThought to encourage more structured email generation
        self.generate_email = dspy.ChainOfThought(EmailSignature)

    def forward(self, customer_query, product_name):
        result = self.generate_email(customer_query=customer_query, product_name=product_name)
        return dspy.Prediction(email_body=result.email_body)

# 4. (Optional but Recommended) Prepare Data
# Typically a list of `dspy.Example` objects
# trainset = [
#     dspy.Example(customer_query="...", product_name="...", email_body="...").with_inputs("customer_query", "product_name"),
#     # ... more examples
# ]

# 5. (Optional but Recommended) Define a Metric
# def email_metric(gold, pred, trace=None):
#     # True if the predicted email is polite and addresses the query
#     # This would be a more complex function in reality
#     gold_email = gold.email_body.lower()
#     pred_email = pred.email_body.lower()
#     return "polite" in pred_email and "customer" in pred_email and len(pred_email) > 20

# 6. (Optional but Recommended) Compile/Optimize your program
# from dspy.teleprompters import BootstrapFewShot
# config = dict(max_bootstrapped_demos=4, max_labeled_demos=4)
# teleprompter = BootstrapFewShot(metric=email_metric, **config)
# optimized_email_generator = teleprompter.compile(FollowUpEmailGenerator(), trainset=trainset)

# 7. Run your program (either the original or the optimized one)
# To use the non-optimized version:
# email_gen = FollowUpEmailGenerator()
# response = email_gen(customer_query="I can't find the user manual.", product_name="WidgetPro")
# print(response.email_body)

# To use an optimized version (after compiling):
# response = optimized_email_generator(customer_query="I can't find the user manual.", product_name="WidgetPro")
# print(response.email_body)
```

## Installation

You typically install DSPy via pip:
```bash
pip install dspy-ai
```
You might also need to install specific LM client libraries (e.g., `openai`, `cohere`).

## Relevance to this Project

DSPy can be invaluable if this project involves:
- Building complex LLM applications where prompt engineering is becoming difficult.
- Requiring high reliability or performance on specific LLM tasks.
- Automating the process of prompt improvement and adaptation.
- Creating systems that can reason, use tools, or require multi-step interactions with an LM.

By defining tasks using DSPy signatures and modules, and then applying teleprompters, you can systematically improve the LLM components of this project.
```
