from rq import Queue
from redis import Redis
from .crud import settle_transaction

redis_conn = Redis(host='redis', port=6379)

q = Queue(connection=redis_conn)

def process_transaction(tx_id: int):
    # Simulate async processing
    settle_transaction(tx_id)  # Update status to SETTLED, update balance