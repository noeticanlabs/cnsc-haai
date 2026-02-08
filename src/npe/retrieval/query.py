"""
Structured Query Construction.

Builds structured queries for corpus and receipt retrieval.
"""

from typing import Any, Dict, List, Optional


class QueryBuilder:
    """Builder for structured retrieval queries."""
    
    def __init__(self):
        self._keywords: List[str] = []
        self._tags: List[str] = []
        self._filters: Dict[str, Any] = {}
        self._limit: int = 100
        self._offset: int = 0
        self._source_types: List[str] = []
        self._must_match_all: bool = False  # AND vs OR semantics
    
    def keyword(self, term: str) -> "QueryBuilder":
        """Add a keyword search term.
        
        Args:
            term: Search term
            
        Returns:
            Self for chaining
        """
        self._keywords.append(term)
        return self
    
    def keywords(self, terms: List[str]) -> "QueryBuilder":
        """Add multiple keyword search terms.
        
        Args:
            terms: List of search terms
            
        Returns:
            Self for chaining
        """
        self._keywords.extend(terms)
        return self
    
    def tag(self, tag: str) -> "QueryBuilder":
        """Add a tag filter.
        
        Args:
            tag: Tag to match
            
        Returns:
            Self for chaining
        """
        self._tags.append(tag)
        return self
    
    def tags(self, tags: List[str]) -> "QueryBuilder":
        """Add multiple tag filters.
        
        Args:
            tags: List of tags to match
            
        Returns:
            Self for chaining
        """
        self._tags.extend(tags)
        return self
    
    def filter(self, field: str, value: Any) -> "QueryBuilder":
        """Add a filter on a specific field.
        
        Args:
            field: Field name
            value: Value to filter on
            
        Returns:
            Self for chaining
        """
        self._filters[field] = value
        return self
    
    def source_type(self, source_type: str) -> "QueryBuilder":
        """Filter by source type.
        
        Args:
            source_type: Source type to match
            
        Returns:
            Self for chaining
        """
        self._source_types.append(source_type)
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Set result limit.
        
        Args:
            n: Maximum results
            
        Returns:
            Self for chaining
        """
        self._limit = n
        return self
    
    def offset(self, n: int) -> "QueryBuilder":
        """Set result offset.
        
        Args:
            n: Offset for pagination
            
        Returns:
            Self for chaining
        """
        self._offset = n
        return self
    
    def must_match_all(self, value: bool = True) -> "QueryBuilder":
        """Set whether all keywords must match (AND semantics).
        
        Args:
            value: True for AND, False for OR
            
        Returns:
            Self for chaining
        """
        self._must_match_all = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the query structure.
        
        Returns:
            Query dict for retrieval
        """
        query = {
            "keywords": self._keywords,
            "tags": self._tags,
            "filters": self._filters,
            "source_types": self._source_types,
            "limit": self._limit,
            "offset": self._offset,
            "must_match_all": self._must_match_all,
        }
        return query
    
    def build_corpus_query(self) -> Dict[str, Any]:
        """Build a query optimized for corpus search.
        
        Returns:
            Corpus search query
        """
        query = self.build()
        query["type"] = "corpus"
        return query
    
    def build_receipt_query(self) -> Dict[str, Any]:
        """Build a query optimized for receipt search.
        
        Returns:
            Receipt search query
        """
        query = self.build()
        query["type"] = "receipt"
        return query


def build_query(**kwargs) -> Dict[str, Any]:
    """Build a query from keyword arguments.
    
    Args:
        **kwargs: Query parameters
        
    Returns:
        Query dict
    """
    builder = QueryBuilder()
    
    if "keywords" in kwargs:
        builder.keywords(kwargs["keywords"])
    if "tags" in kwargs:
        builder.tags(kwargs["tags"])
    if "limit" in kwargs:
        builder.limit(kwargs["limit"])
    if "offset" in kwargs:
        builder.offset(kwargs["offset"])
    
    return builder.build()


class EvidenceQuery:
    """High-level evidence query builder."""
    
    def __init__(self, context: Dict[str, Any]):
        """Initialize with execution context.
        
        Args:
            context: Execution context
        """
        self._context = context
        self._query = QueryBuilder()
    
    def for_goal(self, goal_type: str, **goal_params) -> "EvidenceQuery":
        """Build query for a specific goal.
        
        Args:
            goal_type: Type of goal
            **goal_params: Goal-specific parameters
            
        Returns:
            Self for chaining
        """
        # Add goal-related keywords
        self._query.keyword(goal_type)
        
        for key, value in goal_params.items():
            if isinstance(value, str):
                self._query.keyword(value)
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, str):
                        self._query.keyword(v)
        
        return self
    
    def with_scenario(self, scenario_id: str) -> "EvidenceQuery":
        """Filter by scenario.
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            Self for chaining
        """
        self._query.filter("scenario_id", scenario_id)
        return self
    
    def with_time_bounds(
        self,
        after: Optional[int] = None,
        before: Optional[int] = None,
    ) -> "EvidenceQuery":
        """Set time bounds.
        
        Args:
            after: Timestamp after which evidence is valid
            before: Timestamp before which evidence is valid
            
        Returns:
            Self for chaining
        """
        time_scope = {}
        if after is not None:
            time_scope["after"] = after
        if before is not None:
            time_scope["before"] = before
        
        if time_scope:
            self._query.filter("time_scope", time_scope)
        
        return self
    
    def limited_to_sources(self, sources: List[str]) -> "EvidenceQuery":
        """Limit to specific source types.
        
        Args:
            sources: List of allowed source types
            
        Returns:
            Self for chaining
        """
        for source in sources:
            self._query.source_type(source)
        return self
    
    def with_limit(self, limit: int) -> "EvidenceQuery":
        """Set result limit.
        
        Args:
            limit: Maximum results
            
        Returns:
            Self for chaining
        """
        self._query.limit(limit)
        return self
    
    def execute(self, retrieval_system: Any) -> List[Dict[str, Any]]:
        """Execute the query against a retrieval system.
        
        Args:
            retrieval_system: The retrieval system to query
            
        Returns:
            List of evidence items
        """
        query = self._query.build()
        
        # Execute based on query type
        if query["keywords"]:
            results = retrieval_system.search(
                query=query["keywords"][0] if len(query["keywords"]) == 1 else query["keywords"],
                filters=query["filters"],
                limit=query["limit"],
            )
        else:
            results = []
        
        return results
