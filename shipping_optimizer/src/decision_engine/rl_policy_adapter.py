import numpy as np
from src.optimization.fallback_ga import Chromosome 


class RLPolicyAdapter:
    """
    Wraps RL policy to match optimizer
    interface
    """
    def _init_(self,policy,env_class):
        self.policy = policy
        self.env_class = env_class 

    def predict(self,problem):
        env = self.env_classs(problem)
        obs,_ = env.reset()

        selected = []
        action_probs = []

        done = False 

        while not done:
            action,log_prob,_ = self.policy.select_action(
                obs,
                selected,
                deterministic=True 
            )
            action_probs.append(float(np.exp(log_prob)))
            obs,_,done,_,_=env.step(action) 
        #convert to chromosome 
        services = [0]*len(problem.services)
        frequencies = [0]*len(problem.services)

        for s in selected:
            services[s] = 1
            frequencies[s] = 1 

        return Chromosome(services,frequencies),action_probs 