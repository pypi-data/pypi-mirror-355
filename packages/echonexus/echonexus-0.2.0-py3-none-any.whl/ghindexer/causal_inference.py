from causalnex.structure import StructureModel
from causalnex.structure.notears import from_pandas
from causalnex.network import BayesianNetwork
import pandas as pd
import logging


class CausalInference:
    def __init__(self, data):
        self.data = data
        self.structure_model = None
        self.bayesian_network = None
        self.subkey_activations = []
        self.arc_evolutions = []

    def build_structure_model(self):
        self.structure_model = from_pandas(self.data)
        return self.structure_model

    def build_bayesian_network(self):
        if self.structure_model is None:
            raise ValueError("Structure model not built yet.")
        self.bayesian_network = BayesianNetwork(self.structure_model)
        self.bayesian_network.fit_node_states(self.data)
        self.bayesian_network.fit_cpds(self.data)
        return self.bayesian_network

    def predict_outcome(self, evidence):
        if self.bayesian_network is None:
            raise ValueError("Bayesian network not built yet.")
        return self.bayesian_network.predict(evidence)

    def update_data(self, new_data):
        self.data = pd.concat([self.data, new_data], ignore_index=True)
        self.build_structure_model()
        self.build_bayesian_network()

    def ensure_decision_consistency(self, past_decisions, new_decision):
        # Placeholder for decision consistency check
        return True

    def align_with_past_resolutions(self, past_resolutions, new_resolution):
        # Placeholder for alignment check
        return True

    def highlight_decision_inconsistencies(self, past_decisions, new_decision):
        inconsistencies = []
        for past_decision in past_decisions:
            if not self.ensure_decision_consistency(past_decision, new_decision):
                inconsistencies.append(past_decision)
        return inconsistencies

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
