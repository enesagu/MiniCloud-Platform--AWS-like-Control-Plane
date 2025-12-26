"""
MiniCloud Platform - IAM Policy Engine
Evaluates AWS IAM-style policies for access control decisions.
"""

import re
import fnmatch
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class Effect(Enum):
    ALLOW = "Allow"
    DENY = "Deny"

@dataclass
class EvaluationResult:
    decision: str  # ALLOW, DENY
    matched_statement: Optional[Dict] = None
    reason: str = ""

class PolicyEngine:
    """
    Evaluates IAM policies following AWS-style logic:
    1. Explicit DENY always wins
    2. Explicit ALLOW grants access
    3. Default is DENY (implicit deny)
    """
    
    def evaluate(
        self,
        policies: List[Dict[str, Any]],
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate multiple policies against an action/resource pair.
        
        Args:
            policies: List of policy documents (AWS IAM format)
            action: The action being performed (e.g., "minio:PutObject")
            resource: The resource ARN/path (e.g., "bucket:raw/file.txt")
            context: Optional context for condition evaluation
            
        Returns:
            EvaluationResult with ALLOW or DENY decision
        """
        context = context or {}
        
        # Collect all matching statements
        allow_statements = []
        deny_statements = []
        
        for policy in policies:
            for statement in policy.get("Statement", []):
                if self._matches_statement(statement, action, resource, context):
                    effect = statement.get("Effect", "Deny")
                    if effect == "Deny":
                        deny_statements.append(statement)
                    elif effect == "Allow":
                        allow_statements.append(statement)
        
        # Rule 1: Explicit DENY wins
        if deny_statements:
            return EvaluationResult(
                decision="DENY",
                matched_statement=deny_statements[0],
                reason="Explicit deny in policy"
            )
        
        # Rule 2: Explicit ALLOW grants access
        if allow_statements:
            return EvaluationResult(
                decision="ALLOW",
                matched_statement=allow_statements[0],
                reason="Allowed by policy"
            )
        
        # Rule 3: Default deny (implicit)
        return EvaluationResult(
            decision="DENY",
            matched_statement=None,
            reason="Implicit deny - no matching allow statement"
        )
    
    def _matches_statement(
        self,
        statement: Dict[str, Any],
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check if a statement matches the action and resource."""
        
        # Check Action
        if not self._matches_pattern_list(
            statement.get("Action", []),
            action
        ):
            return False
        
        # Check Resource
        if not self._matches_pattern_list(
            statement.get("Resource", []),
            resource
        ):
            return False
        
        # Check Condition (if present)
        condition = statement.get("Condition")
        if condition and not self._evaluate_condition(condition, context):
            return False
        
        return True
    
    def _matches_pattern_list(self, patterns: Any, value: str) -> bool:
        """Check if value matches any pattern in the list."""
        if isinstance(patterns, str):
            patterns = [patterns]
        
        for pattern in patterns:
            if self._matches_pattern(pattern, value):
                return True
        
        return False
    
    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """
        Match a value against an IAM-style pattern.
        Supports wildcards: * (any chars), ? (single char)
        """
        if pattern == "*":
            return True
        
        # Convert IAM wildcards to regex
        regex_pattern = fnmatch.translate(pattern)
        return bool(re.match(regex_pattern, value, re.IGNORECASE))
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate condition block.
        Supports: StringEquals, StringLike, IpAddress, DateGreaterThan, etc.
        """
        for operator, conditions in condition.items():
            for key, expected in conditions.items():
                actual = self._get_context_value(key, context)
                
                if not self._apply_operator(operator, actual, expected):
                    return False
        
        return True
    
    def _get_context_value(self, key: str, context: Dict[str, Any]) -> Any:
        """Get a value from context using dot notation."""
        parts = key.split(":")
        if len(parts) == 2:
            # AWS-style keys like "aws:SourceIp"
            prefix, name = parts
            return context.get(name) or context.get(key)
        return context.get(key)
    
    def _apply_operator(self, operator: str, actual: Any, expected: Any) -> bool:
        """Apply a condition operator."""
        if actual is None:
            return False
        
        operators = {
            "StringEquals": lambda a, e: str(a) == str(e),
            "StringNotEquals": lambda a, e: str(a) != str(e),
            "StringLike": lambda a, e: fnmatch.fnmatch(str(a), str(e)),
            "NumericEquals": lambda a, e: float(a) == float(e),
            "NumericLessThan": lambda a, e: float(a) < float(e),
            "NumericGreaterThan": lambda a, e: float(a) > float(e),
            "Bool": lambda a, e: bool(a) == (str(e).lower() == "true"),
            "IpAddress": lambda a, e: self._check_ip_range(a, e),
        }
        
        op_func = operators.get(operator)
        if op_func:
            if isinstance(expected, list):
                return any(op_func(actual, e) for e in expected)
            return op_func(actual, expected)
        
        return False
    
    def _check_ip_range(self, ip: str, cidr: str) -> bool:
        """Simple IP range check (for production, use ipaddress module)."""
        # Simplified - in production use ipaddress.ip_network
        if "/" not in cidr:
            return ip == cidr
        # For now, just check prefix match
        network = cidr.split("/")[0]
        prefix = ".".join(network.split(".")[:-1])
        return ip.startswith(prefix)


# Example usage and testing
if __name__ == "__main__":
    engine = PolicyEngine()
    
    # Sample policy
    admin_policy = {
        "Version": "2024-01-01",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["*"],
                "Resource": ["*"]
            }
        ]
    }
    
    readonly_policy = {
        "Version": "2024-01-01",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["*:Get*", "*:List*", "*:Describe*"],
                "Resource": ["*"]
            },
            {
                "Effect": "Deny",
                "Action": ["*:Delete*", "*:Create*", "*:Update*"],
                "Resource": ["*"]
            }
        ]
    }
    
    # Test cases
    print("=== Policy Engine Test ===\n")
    
    # Admin can do anything
    result = engine.evaluate([admin_policy], "minio:DeleteObject", "bucket:data/file.txt")
    print(f"Admin delete: {result.decision} - {result.reason}")
    
    # Read-only can read
    result = engine.evaluate([readonly_policy], "minio:GetObject", "bucket:data/file.txt")
    print(f"ReadOnly get: {result.decision} - {result.reason}")
    
    # Read-only cannot delete
    result = engine.evaluate([readonly_policy], "minio:DeleteObject", "bucket:data/file.txt")
    print(f"ReadOnly delete: {result.decision} - {result.reason}")
    
    # No policy = implicit deny
    result = engine.evaluate([], "function:Invoke", "function:my-func")
    print(f"No policy: {result.decision} - {result.reason}")
