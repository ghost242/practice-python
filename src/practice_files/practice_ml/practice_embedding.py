from litellm import embedding


model = "text-embedding-3-small"

embedding(
    model=model,
    input="Hello, world!",
)
