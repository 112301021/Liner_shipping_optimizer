import numpy as np
class ConfidenceEstimator:
    """Computes confidence of RL decisions
    """
    def compute(self,action_phase):
        if not action_probs:
            return 0.0
        
        probs = np.array(action_probs)
        #Mean probability(stable baseline) 
        confidence = float(np.mean(probs))

        return confidence 