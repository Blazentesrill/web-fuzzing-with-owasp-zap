# Web Application Fuzzing with OWASP ZAP

## Overview
Used OWASP ZAP and a custom Python script to perform input fuzzing against a live web application, discovering a hidden secret string stored in a database. This was a controlled security lab exercise completed as part of CS 4683 (Secure Software Development and Analysis) at UTSA.

## What is Fuzzing?
Fuzzing is a security testing technique where large numbers of automatically generated inputs are sent to an application to discover unexpected behavior or hidden information. It is widely used in penetration testing and bug bounty hunting to find vulnerabilities that manual testing would miss.

In this case, the target was a web form with two fields — a student ID and a secret string. The goal was to identify the correct secret string through systematic fuzzing without using SQL injection or other exploit techniques.

## Target
- A controlled web application hosted for the course
- Form accepted two inputs: student ID and a secret string
- Correct combination returned a "SUCCESS" message

## Understanding the Search Space
The assignment provided two clues about the secret string format:
- Starts with a two-digit integer (00–99): 100 possibilities
- Followed by two lowercase letters (aa–zz): 26 × 26 = 676 possibilities
- **Total search space: 100 × 676 = 67,600 possible combinations**

Knowing the format before starting allowed me to build a targeted wordlist rather than fuzzing blindly, which is a critical first step in any efficient fuzzing engagement.

## Approach 1: OWASP ZAP Built-in Fuzzer

### Setup
- Configured ZAP to intercept traffic between my browser and the target form
- Used ZAP's built-in fuzzer to inject payloads into the secret field
- Generated a wordlist covering the full search space (two digits + two lowercase letters)

### Identifying the Correct Response
ZAP sends each payload and records the server's response. I filtered results by:
- **HTTP status code** — a successful match returned a different status than failed attempts
- **Response length** — the "SUCCESS" response was a different length than the standard failure response, making it easy to identify in ZAP's results table

### Limitation
ZAP's built-in fuzzer was functional but slow when working through a search space of 67,600 combinations. Given that the correct answer was well into the search space alphabetically, the process was taking too long to complete in a reasonable timeframe.

## Approach 2: Custom Python Script

To speed up the process, I wrote a Python script that automated the same attack more efficiently.

### How It Worked
- Generated every possible combination of two digits + two lowercase letters programmatically
- Sent each combination as an HTTP POST request directly to the form
- Parsed the server's response for the "SUCCESS" message
- Printed the correct secret string to the terminal when found

```python
import requests
import itertools
import string

url = "http://[target]/fuzzme/"
student_id = "your_abc123"

digits = [f"{i:02d}" for i in range(100)]
letters = [''.join(c) for c in itertools.product(string.ascii_lowercase, repeat=2)]

for d in digits:
    for l in letters:
        secret = d + l
        response = requests.post(url, data={"abc123": student_id, "secret": secret})
        if "SUCCESS" in response.text:
            print(f"Found secret: {secret}")
            break
```

### Iterative Development
The script went through several iterations in response to real problems encountered during testing — adding multithreading for speed, scaling back workers after hitting rate limits, handling CSRF tokens extracted from the HTML form, and adding progress tracking. See the full development history in the repository.

### Result
The script identified the correct secret string by detecting the "SUCCESS" message in the HTTP response, confirming the answer much faster than waiting for ZAP to complete its full scan.

## Key Takeaways

**Why brute forcing is expensive even on small inputs:** 67,600 combinations sounds manageable, but sending each as an individual HTTP request — waiting for a server response each time — adds up quickly. This illustrates why rate limiting and account lockout policies are critical defenses against fuzzing attacks on real applications.

**Targeted fuzzing beats blind fuzzing:** Knowing the format of the secret string before starting reduced the search space from millions of possibilities to 67,600. In real penetration testing, information gathering before fuzzing dramatically improves efficiency.

**Response differentiation is key:** Identifying how a successful response differs from a failed one (status code, response length, or message content) is the core skill in fuzzing. Without a clear signal to look for, results are meaningless.

**Tool selection matters:** OWASP ZAP is a powerful industry-standard tool, but for high-volume repetitive requests, a custom script can be significantly faster and more flexible.

## Tools Used
- OWASP ZAP (intercepting proxy and built-in fuzzer)
- Python (requests, itertools, string libraries)
- Windows command prompt

## Disclaimer
This fuzzing exercise was performed against a controlled web server set up specifically for this course assignment. All testing was authorized. These techniques should only ever be used against systems you have explicit permission to test.
