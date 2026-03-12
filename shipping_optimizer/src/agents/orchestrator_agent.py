from typing import Dict, Any, List 
from src.agents.base import BaseAgent
from src.agents.regional_agent import RegionalAgent
from src.decomposition.port_clustering import PortClustering
from src.decomposition.regional_splitter import RegionalSplitter
from src.optimization.data import Problem
from src.utils.config import Config
from src.utils.logger import logger

class OrchestratorAgent(BaseAgent):
    def __init__(self, name:str = "orchestrator", model:str = None):
        if model is None:
            model = Config.ORCHESTRATOR_MODEL
            
        super().__init__(
            name=name,
            role="Master Orchestrator",
            model=model
        )
        
        self.regional_agents = [
            RegionalAgent("regional_asia", "Asia", Config.REGIONAL_MODEL),
            RegionalAgent("regional_europe", "Europe", Config.REGIONAL_MODEL),
            RegionalAgent("regional_americas", "Americas", Config.REGIONAL_MODEL)
        ]


    ##System Prompt
    def get_system_prompt(self)-> str:
        return """
    You are the Master Orchestrator of a global shipping network optimization system.

    Your role:
    - Analyze optimization problems
    - Decide how to decompose them
    - Coordinate regional agents
    - Produce executive summaries

    Focus on scalability, efficiency, and business value."""
    
    
    ##Problem Analysis
    def analyze_problem(self, problem:Problem)-> str:
        total_demand = sum(d.weekly_teu for d in problem.demands)
        analysis_prompt = f"""
        We need to optimize a shipping network.

        Ports: {len(problem.ports)}
        Services: {len(problem.services)}
        Demand lanes: {len(problem.demands)}
        Total weekly demand: {total_demand:,.0f} TEU

        Classify this problem size and describe challenges in 2 sentences."""
        
        try:
            return self.call_llm(analysis_prompt, temperature=0.3)
        except Exception:
            return "LLM analysis unavailable."
        
        
        ##Delegate work
    def run_regional_agents(self, problem: Problem) -> List[Dict]:
        results = []
        for agent in self.regional_agents:
            try:
                logger.info(
                    "delegating_to_agent",
                    agent=agent.name
                )
                
                result = agent.process({"problem" : problem})
                results.append(result)
                
            except Exception as e:
                logger.error(
                    "regional_agent_failed",
                    agent = agent.name,
                    error=str(e)
                )
        return results
    
    ##Aggregate Results
    def aggregate_results(self, regional_results):
        """
        Aggregate results from regional agents
        """

        total_services = 0
        total_profit = 0
        total_cost = 0
        total_coverage = 0
        count = 0

        for r in regional_results:

            total_services += r.get("services_selected", 0)
            total_profit += r.get("weekly_profit", 0)
            total_cost += r.get("operating_cost", 0)
            total_coverage += r.get("coverage_percent", 0)

            count += 1

        avg_coverage = total_coverage / count if count > 0 else 0

        return {
            "total_services": total_services,
            "weekly_profit": total_profit,
            "annual_profit": total_profit * 52,
            "coverage": avg_coverage,
            "cost": total_cost
        }
                
## Main process
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("orchestrator_started")
        problem: Problem = input_data["problem"]
        
        analysis = self.analyze_problem(problem)
        logger.info("probelm_analysis_complete")
        
        regional_results = []
        
        # --------------------------------
        # Decompose network
        # --------------------------------

        clustering = PortClustering(n_clusters=len(self.regional_agents))

        clusters = clustering.cluster_ports(problem.ports)

        splitter = RegionalSplitter(problem)

        regional_problems = splitter.split(clusters)

        regional_results = []

        regional_results = []

        for i, agent in enumerate(self.regional_agents):

            regional_problem = regional_problems.get(i)

            if regional_problem is None:
                continue

            result = agent.process({"problem": regional_problem})

            regional_results.append(result)
                
        metrics = self.aggregate_results(regional_results)
        
        summary_prompt = f"""
        Optimization complete.

        Services deployed: {metrics['total_services']}
        Weekly profit: ${float(metrics['weekly_profit']):,.0f}
        Demand coverage: {float(metrics['coverage']):.1f}%
        Operating cost: ${float(metrics['cost']):,.0f}

        Provide a 3 sentence executive summary."""
        
        try:
            executive_summary = self.call_llm(summary_prompt, temperature=0.4)
        except Exception:
            executive_summary = "Executive summary unavailable."
            
        logger.info("orchestrator_complete")
        
        return {
             "orchestrator": self.name,
            "status": "complete",
            "problem_analysis": analysis,
            "regional_results": regional_results,
            "executive_summary": executive_summary,
            "summary_metrics": metrics     
        }
            
        
            
    
        