from typing import Tuple
from src.optimization.data import Problem
from src.optimization.fallback_ga import FallbackGA
from src.optimization.hub_milp import HubMILP
from src.decision_engine.confidence_estimator import ConfidenceEstimator
from src.decision_engine.rl_policy_adapter import RLPolicyAdapter
from src.utils.logger import logger


class DecisionEngine:
    def __init__(self, rl_policy, env_class):
        self.rl_adapter = RLPolicyAdapter(rl_policy, env_class)
        self.confidence_estimator = ConfidenceEstimator()
        

def solve(self, problem: Problem):
    rl_solution , action_probs = self.rl_adapter.predict(problem)
    
    confidence = self.confidence_estimator.compute(action_probs)
    
    logger.info(
        "decision_rl_evaluated",
        confidence = confidence 
    )
    
    #-- Decision --
    if confidence >= 0.6:
        logger.info("decision_using_rl")
        solution = rl_solution
        method = "RL"
        
    else:
        logger.info("decision_fallback_ga")
        
        ga = FallbackGA(problem)
        solution = ga.solve(warm_start=rl_solution)
        method = "GA"
        
    #--MILP Refinement ---
    milp = HubMILP(problem, solution)
    refined = milp.solve()
    
    logger.info(
        "decision_complete",
        method=method,
        profit=refined.get("profit", 0)
    )
    
    return solution