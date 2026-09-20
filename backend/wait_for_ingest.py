import asyncio
import asyncpg
import time

async def main():
    conn = await asyncpg.connect('postgresql://morphik:morphik@localhost:5432/morphik')
    print("Waiting for documents to complete processing...")
    while True:
        docs = await conn.fetch("SELECT filename, status FROM documents")
        all_done = True
        counts = {'completed': 0, 'failed': 0, 'processing': 0}
        for doc in docs:
            # The status is inside system_metadata but we can extract it or parse it
            # wait, status is exposed if we fetch it from system_metadata
            pass
        
        # actually let's just count vector_embeddings
        embeds = await conn.fetchval("SELECT COUNT(*) FROM vector_embeddings")
        print(f"Embeddings: {embeds}", flush=True)
        
        system_meta = await conn.fetch("SELECT system_metadata FROM documents")
        done = 0
        processing = 0
        for m in system_meta:
            import json
            meta = json.loads(m['system_metadata'])
            if meta.get('status') == 'completed':
                done += 1
            elif meta.get('status') == 'processing':
                processing += 1
        print(f"Done: {done}, Processing: {processing}", flush=True)
        if processing == 0 and done > 0:
            break
        await asyncio.sleep(10)
    await conn.close()

asyncio.run(main())
