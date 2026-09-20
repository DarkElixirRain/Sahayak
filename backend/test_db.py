import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://morphik:morphik@localhost:5432/morphik')
    docs = await conn.fetch("SELECT filename, system_metadata FROM documents")
    embeds = await conn.fetchval("SELECT COUNT(*) FROM vector_embeddings")
    print(f"Embeddings: {embeds}")
    for doc in docs:
        print(doc['filename'], doc['system_metadata'])
    await conn.close()

asyncio.run(main())
