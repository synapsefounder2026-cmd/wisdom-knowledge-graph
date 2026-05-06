#!/bin/bash
mkdir -p backups
docker run --rm \
  -v wisdom-knowledge-graph_neo4j_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/neo4j_$(date +%Y%m%d_%H%M).tar.gz -C /data .

docker run --rm \
  -v wisdom-knowledge-graph_qdrant_data:/qdrant/storage \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/qdrant_$(date +%Y%m%d_%H%M).tar.gz -C /qdrant/storage .

echo "Backup xong: $(ls -lh backups/*.tar.gz | tail -2)"
