from app.llm import get_llm

llm = get_llm()

response = llm.invoke(
    "Explain in one sentence what contract liability means."
)

print(response.content)