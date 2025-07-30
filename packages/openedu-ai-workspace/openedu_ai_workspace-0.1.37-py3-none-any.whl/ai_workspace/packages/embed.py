from .base import BaseDocument
from langchain_openai import AzureOpenAIEmbeddings


class EmbedDocument(BaseDocument):
    embedding: AzureOpenAIEmbeddings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings using Azure OpenAI embeddings.

        Args:
            texts (list[str]): The list of texts to embed.

        Returns:
            list[list[float]]: The embedding vectors for the texts.
        """
        if not self.embedding:
            raise ValueError("Embedding client is not initialized.")
        return self.embedding.embed_documents(texts)
