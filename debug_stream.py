import ollama

client = ollama.Client(host='http://localhost:11434')
print('--- Streaming chunk inspection ---')

chunks = []
for chunk in client.chat(
    model='qwen3.5:4b',
    messages=[{'role': 'user', 'content': 'Say BUY or SELL for AAPL. /no_think'}],
    stream=True,
):
    msg = chunk.message
    content  = msg.content
    thinking = getattr(msg, 'thinking', None)
    chunks.append(content)

    if len(chunks) <= 10:
        print(f"chunk {len(chunks):02d}: content={repr(content):<30s} | thinking={repr(thinking)[:50]}")

print(f"\nTotal chunks: {len(chunks)}")
full = "".join(c for c in chunks if c)
print(f"Joined non-empty content: {repr(full[:300])}")
