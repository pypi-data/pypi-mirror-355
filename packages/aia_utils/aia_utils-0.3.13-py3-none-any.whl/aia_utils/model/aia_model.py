from dataclasses import dataclass
from typing import Dict
from datetime import datetime, timezone
from typing import List, Dict
import dataclasses

@dataclass
class AIAMessageHeader:
	producer: str
	creationDate: datetime
	version: str

@dataclass
class AIABreadcrumb:
	name: str
	creationDate: datetime

@dataclass
class AIABase:
	head: AIAMessageHeader
	breadcrumb: List[AIABreadcrumb]

	def dict(self):
		return {k: v for k, v in dataclasses.asdict(self).items()}
    
@dataclass
class AIASemanticGraphNode:
	originalText: str
	tag: str
	index: int
	relationType: str
	parent: Dict
	semanticNodeTree: str



@dataclass
class AIASemanticGraph(AIABase):
	semanticTree: str
	dotFormat: str
	formattedText: str
	sentence: str	
	aiaMessageId: str
	nodes: List[AIASemanticGraphNode]
	classification: str
	type: str
