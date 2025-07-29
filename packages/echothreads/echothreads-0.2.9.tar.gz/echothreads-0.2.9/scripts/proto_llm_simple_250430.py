import llm

model = llm.get_model("jgwill/t:latest")

response = model.prompt(
    "Why the sky is blue?",)


print(response.text)