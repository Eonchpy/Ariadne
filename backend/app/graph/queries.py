CREATE_TABLE_NODE = """
MERGE (t:Table {id: $id})
SET t.name = $name,
    t.schema_name = $schema_name,
    t.qualified_name = $qualified_name,
    t.source_id = $source_id
"""

CREATE_FIELD_NODE = """
MERGE (f:Field {id: $id})
SET f.name = $name,
    f.data_type = $data_type,
    f.table_id = $table_id
"""

DELETE_TABLE_NODE = """
MATCH (t:Table {id: $id}) DETACH DELETE t
"""

DELETE_FIELD_NODE = """
MATCH (f:Field {id: $id}) DETACH DELETE f
"""

DELETE_FIELDS_BY_TABLE = """
MATCH (f:Field {table_id: $table_id}) DETACH DELETE f
"""
CREATE_TABLE_CONSTRAINT = """
CREATE CONSTRAINT table_id IF NOT EXISTS
FOR (t:Table)
REQUIRE t.id IS UNIQUE
"""

CREATE_FIELD_CONSTRAINT = """
CREATE CONSTRAINT field_id IF NOT EXISTS
FOR (f:Field)
REQUIRE f.id IS UNIQUE
"""

CREATE_TABLE_LINEAGE = """
MATCH (s:Table {id: $source_id}), (t:Table {id: $target_id})
MERGE (s)-[r:FEEDS_INTO]->(t)
SET r.lineage_source = $lineage_source,
    r.transformation_type = $transformation_type,
    r.transformation_logic = $transformation_logic,
    r.confidence = $confidence
RETURN id(r) AS rel_id
"""

CREATE_FIELD_LINEAGE = """
MATCH (s:Field {id: $source_id}), (t:Field {id: $target_id})
MERGE (s)-[r:DERIVES_FROM]->(t)
SET r.lineage_source = $lineage_source,
    r.transformation_logic = $transformation_logic,
    r.confidence = $confidence
RETURN id(r) AS rel_id
"""

DELETE_LINEAGE = """
MATCH ()-[r]-() WHERE id(r) = $rel_id
WITH r
DELETE r
RETURN count(r) AS deleted_count
"""

GET_GRAPH = """
MATCH (root:Table {id: $table_id})
CALL apoc.path.expandConfig(root, {relationshipFilter:$rel_filter, minLevel:1, maxLevel:$depth, bfs:true, filterStartNode:false}) YIELD path
WITH root,
     apoc.coll.toSet(apoc.coll.flatten(collect(nodes(path)) + [root])) AS table_nodes,
     apoc.coll.toSet(apoc.coll.flatten(collect(relationships(path)))) AS table_rels
WITH root, table_nodes, table_rels, [t IN table_nodes | t.id] AS table_ids
OPTIONAL MATCH (f1:Field)-[fr:DERIVES_FROM]->(f2:Field)
WHERE f1.table_id IN table_ids AND f2.table_id IN table_ids
WITH root, table_nodes, table_rels, collect(DISTINCT fr) AS field_rels, table_ids,
     apoc.coll.toSet(collect(DISTINCT startNode(fr)) + collect(DISTINCT endNode(fr))) AS field_nodes
OPTIONAL MATCH (ff:Field)
WHERE ff.table_id IN table_ids
WITH root, table_nodes, table_rels, field_rels, field_nodes, table_ids, collect(DISTINCT ff) AS all_fields
WITH root, table_nodes, table_rels, field_rels,
     apoc.coll.toSet(field_nodes + all_fields) AS field_nodes
WITH root,
     apoc.coll.toSet(table_nodes + field_nodes) AS nodes,
     apoc.coll.toSet(table_rels + field_rels) AS rel_objs
WITH root, nodes,
     [r IN rel_objs |
        { id: id(r),
          from: startNode(r).id,
          to: endNode(r).id,
          lineage_source: r.lineage_source,
          confidence: r.confidence,
          rel_type: type(r)
        }
     ] AS rels
RETURN root.id AS root_id, nodes, rels
"""

TRACE_FIELD_UPSTREAM = """
MATCH path = (f:Field {id: $field_id})<-[:DERIVES_FROM*]-(up:Field)
WHERE length(path) >= 1 AND length(path) <= $depth
WITH up, path
RETURN up.id AS field_id,
       up.name AS field_name,
       up.table_id AS table_id,
       length(path) AS distance
ORDER BY distance ASC
"""

TRACE_FIELD_DOWNSTREAM = """
MATCH path = (f:Field {id: $field_id})-[:DERIVES_FROM*]->(down:Field)
WHERE length(path) >= 1 AND length(path) <= $depth
WITH down, path
RETURN down.id AS field_id,
       down.name AS field_name,
       down.table_id AS table_id,
       length(path) AS distance
ORDER BY distance ASC
"""

ALL_PATHS = """
// Find all simple paths (up to max_depth) between arbitrary nodes (Table or Field)
MATCH (startNode {id: $start_id}), (endNode {id: $end_id})
CALL apoc.algo.allSimplePaths(startNode, endNode, 'FEEDS_INTO|DERIVES_FROM>', $max_depth) YIELD path
RETURN path
"""

SHORTEST_PATHS = """
// Shortest paths between arbitrary nodes (Table or Field)
MATCH (startNode {id: $start_id}), (endNode {id: $end_id})
CALL apoc.algo.dijkstra(startNode, endNode, 'FEEDS_INTO|DERIVES_FROM>', 'weight', 1) YIELD path AS path, weight
RETURN path
"""

CYCLES_BY_TABLE = """
// Find cycles reachable from a given table (or all if table_id is null)
MATCH (t:Table)
WHERE $table_id IS NULL OR t.id = $table_id
CALL apoc.algo.allSimplePaths(t, t, 'FEEDS_INTO>', $max_depth) YIELD path
RETURN path
"""
