from typing import Any, List, Callable
from dataclasses import dataclass, field, InitVar

# Default policy point constants
POINTS_LOW = 1
POINTS_MEDIUM = 3
POINTS_HIGH = 9


@dataclass
class EvaluatedPolicy:
    """Detailed information about a policy evaluation."""

    name: str
    points: int
    failed: bool
    qualified: bool
    check_results: dict[str, bool] = field(default_factory=dict)
    qualifier_results: dict[str, bool] = field(default_factory=dict)


def evaluate_checks(obj: Any, checks: list[Callable[[Any], bool]]) -> tuple[bool, dict[str, bool]]:
    success = True
    results = {}
    for check in checks:
        result = check(obj)
        success = success and result
        results[getattr(check, "__name__", str(check))] = result
    return success, results


@dataclass
class Policy:
    """A policy with qualifiers and checks for evaluation."""

    name: str
    points: int
    checks: list[Callable[[Any], bool]]
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def __post_init__(self):
        if not self.checks:
            raise ValueError("Policy must have at least one check")
        if self.points <= 0:
            raise ValueError("Points must be positive")

    def get_points(self, obj: Any) -> int:
        """Get points if all checks pass, 0 otherwise."""
        return self.points if all(check(obj) for check in self.checks) else 0

    def evaluate(self, obj_to_evaluate: Any) -> EvaluatedPolicy:
        # Check if policy qualifies
        qualified, qualifier_results = evaluate_checks(obj_to_evaluate, self.qualifiers)

        all_checks_pass, check_results = evaluate_checks(obj_to_evaluate, self.checks)

        # Determine if policy failed (qualified but checks didn't all pass)
        failed = qualified and not all_checks_pass

        return EvaluatedPolicy(
            name=self.name,
            points=self.points,
            failed=failed,
            qualified=qualified,
            check_results=check_results,
            qualifier_results=qualifier_results,
        )


@dataclass
class GroupResult:
    name: str
    score: int
    max_score: int
    qualified: bool


@dataclass
class PolicyGroupResult(GroupResult):
    """Results of evaluating a PolicyGroup."""

    points_max: int
    points_sum: int
    evaluated_policies: List[EvaluatedPolicy] = field(default_factory=list)


def calculate_score(points_sum: int, points_max: int, calculation_factor: float = 100) -> float:
    """Calculate percentage score, handling edge cases."""
    return (points_sum / points_max) * calculation_factor if points_max > 0 else 0


@dataclass
class PolicyGroup:
    policies: list[Policy]
    name: str
    description: str = ""
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def evaluate(self, obj_to_evaluate: Any, weight_coefficient: float = 1) -> PolicyGroupResult:
        evaluated_policies = []
        points_max = 0
        points_sum = 0
        max_score = round(100 * weight_coefficient)

        qualified, qualifier_results = evaluate_checks(obj_to_evaluate, self.qualifiers)

        if qualified:
            for policy in self.policies:
                evaluated_policy = policy.evaluate(obj_to_evaluate)

                if evaluated_policy.qualified:  # Add to totals if qualified
                    points_max += policy.points
                    points_sum += evaluated_policy.points if not evaluated_policy.failed else 0

                evaluated_policies.append(evaluated_policy)

            calculation_factor = max_score / points_max if points_max > 0 else 0

            score = round(points_sum * calculation_factor)
        else:
            score = 0

        return PolicyGroupResult(
            points_max=points_max,
            points_sum=points_sum,
            score=score,
            max_score=max_score,
            evaluated_policies=evaluated_policies,
            name=self.name,
            qualified=qualified,
        )


@dataclass
class TierResult:
    """Holds the evaluation result for a single tier."""

    tier: int
    points_effective: int
    points_max: int
    points_sum: int
    score: int
    max_score: int
    evaluated_policies: List[EvaluatedPolicy] = field(default_factory=list)


@dataclass
class TieredPolicyGroupResult(GroupResult):
    """Results of evaluating a TieredPolicySet."""

    tier_results: dict[int, TierResult] = field(default_factory=dict)

    def points_max(self) -> int:
        return sum(r.points_max for r in self.tier_results.values())

    def points_effective(self) -> int:
        return sum(r.points_effective for r in self.tier_results.values())


@dataclass
class TieredPolicyGroup:
    """Evaluates policies in tiers where failure in one tier affects subsequent tiers."""

    name: str
    description: str = ""
    _tiered_policies: dict[int, list[Policy]] = field(default_factory=dict)
    tiered_policies: InitVar[dict[int, list[Policy]] | None] = None
    qualifiers: list[Callable[[Any], bool]] = field(default_factory=list)

    def __post_init__(self, tiered_policies):
        if tiered_policies:
            self.add_tiers(tiered_policies)

    def add_tier(self, tier: int, policies: list[Policy]):
        if tier < 1:
            raise ValueError("Tier must be 1 or higher")
        if tier in self._tiered_policies:
            raise ValueError(f"Tier {tier} already exists")
        if self._tiered_policies and tier != max(self._tiered_policies.keys()) + 1:
            raise ValueError("Tier must increment by one from the previous highest tier")
        self._tiered_policies[tier] = policies

    def add_tiers(self, tiered_policies: dict[int, list[Policy]]):
        """Add multiple tiers at once."""
        if not tiered_policies:
            raise ValueError("Tiered policies cannot be empty")

        sorted_tiers = sorted(tiered_policies.keys())
        if sorted_tiers != list(range(1, len(sorted_tiers) + 1)):
            raise ValueError("Tier keys must form a complete sequence starting from 1 (e.g., 1, 2, 3)")

        for tier, policies in tiered_policies.items():
            self.add_tier(tier, policies)

    def evaluate(self, obj_to_evaluate: Any, weight_coefficient: float = 1) -> TieredPolicyGroupResult:
        """Evaluate tiers, where failure in one tier affects subsequent tiers."""
        results = {}
        tier_failed = False
        max_score = round(100 * weight_coefficient)

        policy_group_qualified, qualifier_results = evaluate_checks(obj_to_evaluate, self.qualifiers)

        if not policy_group_qualified:
            return TieredPolicyGroupResult(
                name=self.name,
                score=max_score,
                max_score=max_score,
                tier_results=results,
                qualified=policy_group_qualified,
            )

        # First pass: calculate total qualifying points across all tiers
        total_qualifying_points = 0
        tier_qualifying_points = {}

        for tier_num in sorted(self._tiered_policies.keys()):
            policies = self._tiered_policies[tier_num]
            tier_max_points = 0

            # Calculate max points for policies that qualify in this tier
            for policy in policies:
                qualified, _ = evaluate_checks(obj_to_evaluate, policy.qualifiers)
                if qualified:
                    tier_max_points += policy.points

            tier_qualifying_points[tier_num] = tier_max_points
            total_qualifying_points += tier_max_points

        # Second pass: evaluate each tier with proportional max_score
        for tier_num in sorted(self._tiered_policies.keys()):
            # Calculate proportional max_score for this tier
            tier_max_points = tier_qualifying_points[tier_num]
            tier_weigh_coefficient = (
                (tier_max_points / total_qualifying_points) * weight_coefficient if total_qualifying_points > 0 else 0
            )

            policy_set = PolicyGroup(name="temp", policies=self._tiered_policies[tier_num])
            policy_set_result = policy_set.evaluate(obj_to_evaluate, tier_weigh_coefficient)

            # Determine effective points based on tier status
            if tier_failed or policy_set_result.points_max == 0:
                points_effective = 0
                tier_score = 0
            else:
                points_effective = policy_set_result.points_sum
                tier_score = policy_set_result.score
                # Mark subsequent tiers as failed if this tier didn't achieve max points
                if policy_set_result.points_sum < policy_set_result.points_max:
                    tier_failed = True

            results[tier_num] = TierResult(
                tier=tier_num,
                points_effective=points_effective,
                points_max=policy_set_result.points_max,
                points_sum=policy_set_result.points_sum,
                score=tier_score,
                max_score=policy_set_result.max_score,
                evaluated_policies=policy_set_result.evaluated_policies,
            )

        # Calculate overall score by summing tier scores
        overall_score = sum(r.score for r in results.values())

        return TieredPolicyGroupResult(
            name=self.name,
            score=overall_score,
            max_score=max_score,
            tier_results=results,
            qualified=policy_group_qualified,
        )
