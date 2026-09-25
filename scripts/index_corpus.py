import logging
from app.db.session import SessionLocal
from app.services.vector_indexing import index_policy_corpus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Connecting to database...")
    db = SessionLocal()
    try:
        logger.info("Indexing policy corpus into pgvector...")
        num_indexed = index_policy_corpus(db)
        logger.info(f"Successfully indexed {num_indexed} policy chunks.")
    except Exception as e:
        logger.error(f"Failed to index corpus: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
