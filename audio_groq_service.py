from groq import Groq

api_key = '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'
client = Groq(api_key=api_key)

def groq_execute(prompt):
    completion = client.chat.completions.create(
        model="llama2-70b-4096",
        messages=[
        {
            "role": "user",
            "content": "Can you answer it briefly without code, 30 words only: " + prompt
        }
        ],
        temperature=1,
        max_tokens=1670,
        top_p=1,
        stream=True,
        stop=None,
    )
    response = ''
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response

if __name__ == "__main__":
    groq_execute("tell me a joke")