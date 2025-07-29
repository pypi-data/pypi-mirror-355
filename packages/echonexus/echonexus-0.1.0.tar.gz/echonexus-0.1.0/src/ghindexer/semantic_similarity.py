import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging


class SemanticSimilarity:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.index = None
        self.issues = []
        self.embeddings = None
        self.subkey_activations = []
        self.arc_evolutions = []

    def load_issues(self, issues):
        self.issues = issues
        self.embeddings = self.model.encode(
            [issue['body'] for issue in issues])
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def calculate_similarity(self, query):
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding, k=5)
        similar_issues = [self.issues[idx] for idx in indices[0]]
        return similar_issues

    def cluster_related_discussions(self):
        n_clusters = 5
        kmeans = faiss.Kmeans(d=self.embeddings.shape[1], k=n_clusters)
        kmeans.train(self.embeddings)
        _, cluster_indices = kmeans.index.search(self.embeddings, 1)
        clusters = {i: [] for i in range(n_clusters)}
        for idx, cluster_idx in enumerate(cluster_indices):
            clusters[cluster_idx[0]].append(self.issues[idx])
        return clusters

    def dynamic_memory_mapping(self, issues):
        memory_map = {}
        for issue in issues:
            key_anchor = f"issues:jgwill/EchoNexus:{issue['id']}:agent:unknown"
            memory_map[key_anchor] = {
                "status": issue["state"],
                "agent": "unknown",
                "started_at": issue["created_at"],
                "notes": issue["body"],
                "ripple_refs": [],
                "next_steps": []
            }
        return memory_map

    def activate_subkey(self, subkey):
        self.subkey_activations.append(subkey)
        self.log_subkey_activation(subkey)

    def evolve_arc(self, arc):
        self.arc_evolutions.append(arc)
        self.log_arc_evolution(arc)

    def log_subkey_activation(self, subkey):
        logging.info(f"Subkey Activated: {subkey}")

    def log_arc_evolution(self, arc):
        logging.info(f"Arc Evolved: {arc}")

    def combine_signals_into_actionable_insight_models(self, stagnation_scores, contradiction_scores, urgency_scores):
        actionable_insights = []
        for issue in self.issues:
            stagnation_score = next((score['stagnation_score'] for score in stagnation_scores if score['id'] == issue['id']), 0)
            contradiction_score = next((score['contradiction_score'] for score in contradiction_scores if score['issue_id'] == issue['id']), 0)
            urgency_score = next((score['urgency_score'] for score in urgency_scores if score['id'] == issue['id']), 0)
            actionable_insight = {
                "id": issue['id'],
                "stagnation_score": stagnation_score,
                "contradiction_score": contradiction_score,
                "urgency_score": urgency_score,
                "combined_score": stagnation_score + contradiction_score + urgency_score
            }
            actionable_insights.append(actionable_insight)
        return actionable_insights

    def highlight_low_similarity_targets(self, similarity_threshold=0.5):
        low_similarity_targets = []
        for issue in self.issues:
            similar_issues = self.calculate_similarity(issue['body'])
            if all(similarity['similarity_score'] < similarity_threshold for similarity in similar_issues):
                low_similarity_targets.append(issue)
        return low_similarity_targets
