import os
import logging

from discord import Embed, User
from discord.bot import Bot
from discord.commands import ApplicationContext, Option, OptionChoice
from utils.embed import create_match_history_embed
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM

from llm.embedding import E5Embeddings

logging.basicConfig(format='%(levelname)s %(name)s %(asctime)s: %(message)s', level=logging.INFO)
logger = logging.getLogger("c/rpg")

INDEX_DIR = "/app/resources/vectorstore"
EMBEDD_MODEL_NAME = os.getenv("EMBEDD_MODEL_NAME")
GENERATE_MODEL_NAME = os.getenv("GENERATE_MODEL_NAME")

embeddings = E5Embeddings(OllamaEmbeddings(model=EMBEDD_MODEL_NAME, base_url="http://ollama:11434"))

def register_rpg_commands(bot: Bot):
    @bot.slash_command(name="rpg", description="Quantifica as vitorias de cada jogador")
    async def rpg(
            ctx: ApplicationContext,
            question: Option(str, "Pergunta sobre Arkham RPG", name="pergunta", required=True)
    ):
        await ctx.response.defer()

        db = Chroma(
            persist_directory=INDEX_DIR,
            embedding_function=embeddings
        )

        llm = OllamaLLM(model=GENERATE_MODEL_NAME, base_url="http://ollama:11434", num_thread=4)

        template = """       
        Você é um especialista no RPG Arkham Horror. 
        Todo o seu conhecimento deve vir exclusivamente do contexto a seguir, que foi extraído do livro de regras oficial (em inglês):
        
        {context}
        
        Pergunta: {question}
        
        Instruções de resposta:
        1. Traduza e interprete a pergunta se necessário, mas use apenas o contexto fornecido (em inglês) para responder. 
        2. Sempre responda em português.
        3. Se a informação não estiver clara ou não existir no contexto, diga: "Não encontrei essa informação no manual fornecido."
        4. Seja direto, claro e objetivo, sem inventar regras ou termos não presentes no contexto.
        5. Se possível, cite a página ou seção mencionada no contexto.
        """

        prompt = PromptTemplate(template=template, input_variables=["question", "context"])

        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=db.as_retriever(search_kwargs={"score_threshold": 0.6,  "k": 3}),
            chain_type_kwargs={"prompt": prompt, "document_variable_name": "context"}
        )

        result = await qa_chain.ainvoke({"query": question})

        logger.info(result)

        await ctx.followup.send(result["result"])

    @bot.slash_command(name="teste", description="Teste de indexação")
    async def teste(
            ctx: ApplicationContext,
            question: Option(str, "Pergunta sobre Arkham RPG", name="pergunta", required=True)
    ):
        await ctx.response.defer()

        try:
            # Carrega o índice
            db = Chroma(
                persist_directory=INDEX_DIR,
                embedding_function=embeddings
            )

            # Verifica metadados disponíveis
            available_metadata = db._collection.get(include=["metadatas"])["metadatas"]
            has_source_file = available_metadata and "source_file" in available_metadata[0]

            # Configura o filtro
            search_filter = {"source_file": {"$ne": None}} if has_source_file else None

            # Busca documentos com filtro seguro
            docs = db.similarity_search_with_score(
                question,
                k=5,
                filter=search_filter  # Filtro corrigido aqui
            )

            # Processa os resultados
            if not docs:
                await ctx.send("Não encontrei documentos relevantes para sua pergunta.")
                return

            # Formata a resposta
            response = ["🔍 **Resultados da Busca:**"]
            for i, (doc, score) in enumerate(docs[:3]):  # Limita a 3 melhores
                source = doc.metadata.get("source_file", "Desconhecido")
                response.append(
                    f"\n📄 **{source}** (Relevância: {score:.2f})\n"
                    f"{doc.page_content[:300]}..."
                )

            await ctx.followup.send("\n".join(response))
            await ctx.send()

        except Exception as e:
            await ctx.send(f"⚠ Erro ao processar pergunta: {str(e)}")

