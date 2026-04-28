import ollama

response = ollama.chat(
    model='mistral',
    messages=[
        {'role': 'user', 'content': 'What is ECU in automotive?'}
    ]
)

print(response['message']['content'])