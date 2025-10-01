"""Autopilot AI simulation engine for Monte Carlo financial simulations."""

import random
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class AutopilotEngine:
    """Monte Carlo simulation engine for financial scenarios."""

    def __init__(self):
        self.iterations = 1000  # Monte Carlo iterations

    def run_simulation(
        self, user_data: Dict, scenario: str, mode: str, duration_months: int = 12
    ) -> Dict:
        """
        Run Monte Carlo simulation for a given scenario.

        Args:
            user_data: User's financial data (income, expenses, balance, goals)
            scenario: Type of scenario (job_loss, market_dip, big_purchase, windfall)
            mode: Autopilot mode (conservative, balanced, experimental)
            duration_months: Simulation duration in months

        Returns:
            Simulation results with recommended actions
        """
        results = []

        for i in range(self.iterations):
            sim_result = self._simulate_single_iteration(
                user_data, scenario, mode, duration_months
            )
            results.append(sim_result)

        # Aggregate results
        final_balances = [r["final_balance"] for r in results]
        goal_completions = [r["goal_completion"] for r in results]

        # Calculate percentiles
        sorted_balances = sorted(final_balances)
        p10_index = int(0.10 * len(sorted_balances))
        p50_index = int(0.50 * len(sorted_balances))
        p90_index = int(0.90 * len(sorted_balances))

        median_balance = sorted_balances[p50_index]
        worst_case_balance = sorted_balances[p10_index]
        best_case_balance = sorted_balances[p90_index]

        # Generate recommended actions based on mode and scenario
        recommended_actions = self._generate_recommendations(
            user_data, scenario, mode, median_balance, goal_completions
        )

        # Create scenario outcomes
        scenarios = [
            {
                "outcome": "Worst Case (10th Percentile)",
                "probability": 0.10,
                "recommended_actions": [
                    a for a in recommended_actions if "emergency" in a.lower() or "protect" in a.lower()
                ],
                "final_balance": worst_case_balance,
                "goal_completion_rate": min(goal_completions) if goal_completions else 0.0,
            },
            {
                "outcome": "Expected Case (Median)",
                "probability": 0.50,
                "recommended_actions": recommended_actions[:3],
                "final_balance": median_balance,
                "goal_completion_rate": sum(goal_completions) / len(goal_completions)
                if goal_completions
                else 0.0,
            },
            {
                "outcome": "Best Case (90th Percentile)",
                "probability": 0.10,
                "recommended_actions": [
                    a for a in recommended_actions if "invest" in a.lower() or "grow" in a.lower()
                ],
                "final_balance": best_case_balance,
                "goal_completion_rate": max(goal_completions) if goal_completions else 0.0,
            },
        ]

        return {
            "scenarios": scenarios,
            "median_final_balance": median_balance,
            "worst_case_balance": worst_case_balance,
            "best_case_balance": best_case_balance,
            "recommended_rules": self._generate_rules(user_data, mode, recommended_actions),
        }

    def _simulate_single_iteration(
        self, user_data: Dict, scenario: str, mode: str, duration_months: int
    ) -> Dict:
        """Simulate a single Monte Carlo iteration."""
        starting_balance = user_data.get("current_balance", 0)
        avg_income = user_data.get("avg_monthly_income", 0)
        avg_expenses = user_data.get("avg_monthly_expenses", 0)
        goals = user_data.get("goals", [])

        balance = starting_balance
        goal_progress = {g["id"]: g.get("current_amount", 0) for g in goals}

        for month in range(duration_months):
            # Add noise to income and expenses (±15% variability)
            income = self._perturb(avg_income, 0.15)
            expenses = self._perturb(avg_expenses, 0.15)

            # Apply scenario effects
            income, expenses = self._apply_scenario(scenario, month, income, expenses)

            # Apply autopilot rules based on mode
            income, expenses, savings = self._apply_autopilot_rules(
                mode, income, expenses, balance, goal_progress
            )

            # Update balance
            balance += income - expenses

            # Update goal progress with savings
            if savings > 0 and goals:
                # Distribute savings to goals
                savings_per_goal = savings / len(goals)
                for goal_id in goal_progress:
                    goal_progress[goal_id] += savings_per_goal

            # Prevent negative balance (overdraft limit)
            if balance < -1000:
                balance = -1000

        # Calculate goal completion rate
        goal_completion = 0
        if goals:
            for goal in goals:
                target = goal.get("target_amount", 1)
                current = goal_progress.get(goal["id"], 0)
                goal_completion += min(current / target, 1.0)
            goal_completion /= len(goals)

        return {"final_balance": balance, "goal_completion": goal_completion}

    def _perturb(self, value: float, noise_factor: float) -> float:
        """Add random noise to a value."""
        noise = random.uniform(-noise_factor, noise_factor)
        return value * (1 + noise)

    def _apply_scenario(
        self, scenario: str, month: int, income: float, expenses: float
    ) -> Tuple[float, float]:
        """Apply scenario effects to income and expenses."""
        if scenario == "job_loss":
            # Job loss at month 3, income drops to 0 for 3 months
            if 3 <= month < 6:
                income = 0

        elif scenario == "market_dip":
            # Market dip increases anxiety spending by 20%
            if 2 <= month < 8:
                expenses *= 1.20

        elif scenario == "big_purchase":
            # Big purchase at month 6
            if month == 6:
                expenses += income * 1.5  # 1.5x monthly income expense

        elif scenario == "windfall":
            # Windfall at month 4
            if month == 4:
                income += income * 3  # 3x income bonus

        return income, expenses

    def _apply_autopilot_rules(
        self, mode: str, income: float, expenses: float, balance: float, goal_progress: Dict
    ) -> Tuple[float, float, float]:
        """Apply autopilot rules based on mode."""
        savings = 0

        if mode == "conservative":
            # Save 20% of income automatically
            savings = income * 0.20
            expenses -= savings

        elif mode == "balanced":
            # Save 15% of income, invest 10% if surplus exists
            if income > expenses:
                surplus = income - expenses
                savings = surplus * 0.25

        elif mode == "experimental":
            # Aggressive: save 10%, invest 15%, dynamic budget reallocation
            savings = income * 0.25
            # Round up transactions (simulated as 5% extra savings)
            savings += expenses * 0.05

        return income, expenses, max(savings, 0)

    def _generate_recommendations(
        self,
        user_data: Dict,
        scenario: str,
        mode: str,
        median_balance: float,
        goal_completions: List[float],
    ) -> List[str]:
        """Generate recommended actions based on simulation results."""
        recommendations = []

        avg_income = user_data.get("avg_monthly_income", 0)

        # Scenario-specific recommendations
        if scenario == "job_loss":
            recommendations.append(
                f"Build emergency fund to cover 6 months of expenses (${avg_income * 0.7 * 6:.0f})"
            )
            recommendations.append("Auto-pause non-essential subscriptions if income drops below threshold")

        elif scenario == "market_dip":
            recommendations.append("Auto-invest surplus during market dips for long-term gains")
            recommendations.append("Set spending alerts to avoid panic purchases")

        elif scenario == "big_purchase":
            recommendations.append("Create sinking fund goal for planned big purchases")
            recommendations.append("Auto-transfer bonus/windfall income to purchase fund")

        elif scenario == "windfall":
            recommendations.append("Auto-allocate 50% of windfalls to emergency fund")
            recommendations.append("Auto-invest 30% of windfalls into index funds")

        # Mode-specific recommendations
        if mode == "conservative":
            recommendations.append("Sweep paycheck surplus into Emergency Goal until target reached")
            recommendations.append("Alert if discretionary spending exceeds 15% of income")

        elif mode == "balanced":
            recommendations.append("Round up transactions to nearest $10, invest difference")
            recommendations.append("Auto-contribute 10% of bonuses to retirement goal")

        elif mode == "experimental":
            recommendations.append("Dynamic budget reallocation: shift unused budgets to investments")
            recommendations.append("Auto-submit bill negotiation requests for recurring services")

        # Goal-based recommendations
        if goal_completions and sum(goal_completions) / len(goal_completions) < 0.5:
            recommendations.append("Increase automatic goal contributions by 5% monthly")

        return recommendations[:5]  # Return top 5

    def _generate_rules(self, user_data: Dict, mode: str, recommendations: List[str]) -> List[Dict]:
        """Generate executable Autopilot rules from recommendations."""
        rules = []

        avg_income = user_data.get("avg_monthly_income", 0)

        # Example rule 1: Paycheck surplus sweep
        if mode in ["conservative", "balanced"]:
            rules.append({
                "rule_name": "Paycheck Surplus Sweep",
                "condition": {
                    "type": "paycheck_surplus",
                    "threshold": avg_income * 1.1,
                },
                "action": {
                    "type": "sweep_to_goal",
                    "target": "emergency_fund",
                    "percentage": 80,
                },
                "mode": mode,
            })

        # Example rule 2: Round-up investing
        if mode in ["balanced", "experimental"]:
            rules.append({
                "rule_name": "Round-Up Micro-Investing",
                "condition": {
                    "type": "transaction_complete",
                    "category": "discretionary",
                },
                "action": {
                    "type": "round_up_invest",
                    "round_to": 10,
                    "target_account": "investment",
                },
                "mode": mode,
            })

        # Example rule 3: Spending spike alert/freeze
        if mode == "conservative":
            rules.append({
                "rule_name": "Spending Spike Protection",
                "condition": {
                    "type": "spending_spike",
                    "threshold": 130,  # 30% increase
                },
                "action": {
                    "type": "freeze_subscription",
                    "duration_days": 14,
                },
                "mode": mode,
            })

        return rules
