# semantif

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**What if semantic checks were as simple as a boolean `if`?**

`semantif` is a minimalist Python library that hides all the LLM complexity behind a single, dead-simple function for semantic judgment.

## Why This Exists

LLMs are incredibly powerful, but using them for a simple yes/no question? You end up writing tons of boilerplate for prompt engineering, API calls, response parsing, error handling... ugh 😩

semantif lets developers ask straightforward questions without getting lost in the weeds. Because sometimes you just want to know if a user is angry, not become a prompt engineer.


## Key Features

* **Zero Boilerplate:** One `judge()` function. That's it.  
* **Actually Pythonic:** Made specifically for if statements. Your code reads like English.
* **Lightweight:** No weird dependencies cluttering your project.

## Getting Started

### Installation

```bash
pip install semantif
```

### Quickstart

Before using semantif, you need to set up your LLM provider's API key. For security, it is highly recommended to manage API keys using environment variables rather than embedding them directly in your code.

Please store your OpenAI API key in an environment variable named OPENAI_API_KEY.


```python
from semantif import judge

import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
# Note: Replace "your-api-key-here" with your actual API key

# Language understanding - detect user emotions
user_feedback = "Yeah, right, right. Sure, sure, sure, whatever you say."
if judge("user is angry", user_feedback):
    escalate_to_manager()

# Semantic equality - understand different representations of the same concept
number = "cinco"
if judge("equal five", number):
    skip_queue()

# Content validation - intelligent pattern recognition
user_input = 'fakemail@thisisatest.com'
if judge("does it look like a real email?", user_input):
    send_verification()
```

#### Why semantif.judge()?
Traditional if/else statements are precise but become a maintenance nightmare when conditions get complex. With the advancement of LLMs that can now reliably output reasonable responses, semantif.judge() leverages this capability to make your conditions more natural and significantly more flexible.
#### Perfect for Rapid Prototyping: 
As LLMs have become stable and reliable, using semantic judgment can dramatically accelerate your proof-of-concept (POC) development. Instead of spending hours crafting complex logic, you can express your intent in plain language and get immediate results.


Traditional if/else (verbose and incomplete):

```python
# Imagine writing all this just to detect anger... 😵
if ("terrible" in text.lower() or 
    "awful" in text.lower() or 
    "worst" in text.lower() or 
    "hate" in text.lower() or 
    "sucks" in text.lower() or
    "horrible" in text.lower() or
    "disappointed" in text.lower() or
    # ... and hundreds of other variations
    # Plus you'd need to handle typos, different languages, etc.
    ):
    escalate_to_manager()
    # And this still won't catch everything! 🤷‍♂️
```
With semantif (simple and comprehensive):

```python
if judge("user is angry", user_message):
    escalate_to_manager()
```

## License

MIT License.

✅ Roadmap

- [ ] Multi-Provider Support
- [ ] Integrate on-device models via llama.cpp. This will feature a first-use, automatic model downloader for a true zero-configuration experience. 
- [ ] Add async support by implementing a semantif.async_judge() function.
