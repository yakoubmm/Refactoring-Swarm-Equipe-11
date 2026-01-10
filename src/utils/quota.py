"""
API Quota Monitoring System
Tracks Gemini API usage and warns when running low.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any


class QuotaMonitor:
    """Monitor and track API quota usage"""
    
    QUOTA_FILE = "logs/quota_usage.json"
    
    # Google Gemini API limits (free tier)
    DAILY_LIMIT = 60  # requests per minute (conservative estimate)
    LOW_QUOTA_THRESHOLD = 5  # warn when this many calls remain
    
    def __init__(self):
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> Dict[str, Any]:
        """Load quota usage from file"""
        if os.path.exists(self.QUOTA_FILE):
            try:
                with open(self.QUOTA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self._init_usage()
        return self._init_usage()
    
    def _init_usage(self) -> Dict[str, Any]:
        """Initialize new usage tracking"""
        return {
            "date": datetime.now().isoformat(),
            "calls_today": 0,
            "calls_by_agent": {
                "Auditor": 0,
                "Fixer": 0,
                "Generator": 0,
                "Judge": 0
            },
            "last_reset": datetime.now().isoformat(),
            "warnings": []
        }
    
    def _save_usage(self):
        """Save quota usage to file"""
        os.makedirs(os.path.dirname(self.QUOTA_FILE), exist_ok=True)
        with open(self.QUOTA_FILE, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def _check_reset(self):
        """Check if quota should reset (daily)"""
        last_reset = datetime.fromisoformat(self.usage_data.get("last_reset", datetime.now().isoformat()))
        if datetime.now() - last_reset > timedelta(days=1):
            # Reset quota
            self.usage_data = self._init_usage()
            print("📊 Daily quota reset\n")
    
    def log_api_call(self, agent_name: str) -> Dict[str, Any]:
        """
        Log an API call and return quota status
        
        Args:
            agent_name (str): Name of agent making the call
            
        Returns:
            Dict with quota info:
                - calls_remaining
                - calls_today
                - is_low_quota
                - warning_message
        """
        self._check_reset()
        
        # Increment counters
        self.usage_data["calls_today"] += 1
        self.usage_data["calls_by_agent"][agent_name] = \
            self.usage_data["calls_by_agent"].get(agent_name, 0) + 1
        
        # Calculate remaining
        calls_remaining = max(0, self.DAILY_LIMIT - self.usage_data["calls_today"])
        is_low_quota = calls_remaining <= self.LOW_QUOTA_THRESHOLD
        
        warning = None
        if is_low_quota:
            warning = f"⚠️  LOW QUOTA WARNING: Only {calls_remaining} API calls remaining today!"
            self.usage_data["warnings"].append({
                "timestamp": datetime.now().isoformat(),
                "message": warning
            })
        
        # Save updated usage
        self._save_usage()
        
        return {
            "calls_remaining": calls_remaining,
            "calls_today": self.usage_data["calls_today"],
            "is_low_quota": is_low_quota,
            "warning_message": warning,
            "agent_calls": self.usage_data["calls_by_agent"][agent_name]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        self._check_reset()
        
        calls_remaining = max(0, self.DAILY_LIMIT - self.usage_data["calls_today"])
        is_low_quota = calls_remaining <= self.LOW_QUOTA_THRESHOLD
        
        return {
            "calls_today": self.usage_data["calls_today"],
            "calls_remaining": calls_remaining,
            "daily_limit": self.DAILY_LIMIT,
            "is_low_quota": is_low_quota,
            "calls_by_agent": self.usage_data["calls_by_agent"],
            "last_reset": self.usage_data.get("last_reset"),
            "warnings_today": len(self.usage_data.get("warnings", []))
        }
    
    def print_status(self):
        """Print formatted quota status"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("📊 API QUOTA STATUS")
        print("="*60)
        print(f"Daily Limit:     {status['daily_limit']} calls")
        print(f"Used Today:      {status['calls_today']} calls")
        print(f"Remaining:       {status['calls_remaining']} calls", end="")
        
        if status['is_low_quota']:
            print(" ⚠️  LOW!")
        else:
            print()
        
        print(f"\nUsage by Agent:")
        for agent, count in status['calls_by_agent'].items():
            if count > 0:
                print(f"  - {agent}: {count} calls")
        
        if status['warnings_today'] > 0:
            print(f"\n⚠️  {status['warnings_today']} warning(s) today")
        
        print("="*60 + "\n")
    
    def estimate_iterations_possible(self, calls_per_iteration: int = 3) -> int:
        """
        Estimate how many iterations are possible with remaining quota
        
        Args:
            calls_per_iteration (int): Expected API calls per iteration (Auditor + Fixer + Generator)
            
        Returns:
            int: Number of possible iterations
        """
        status = self.get_status()
        return max(0, status['calls_remaining'] // calls_per_iteration)


# Global quota monitor instance
_quota_monitor = None


def get_quota_monitor() -> QuotaMonitor:
    """Get or create global quota monitor"""
    global _quota_monitor
    if _quota_monitor is None:
        _quota_monitor = QuotaMonitor()
    return _quota_monitor


def log_api_call(agent_name: str) -> Dict[str, Any]:
    """Log an API call to quota system"""
    monitor = get_quota_monitor()
    return monitor.log_api_call(agent_name)


def check_quota_before_run(iterations: int = 10, calls_per_iteration: int = 3):
    """
    Check if there's enough quota before running orchestration
    
    Args:
        iterations (int): Expected number of iterations
        calls_per_iteration (int): API calls per iteration
        
    Returns:
        bool: True if enough quota, False otherwise
    """
    monitor = get_quota_monitor()
    status = monitor.get_status()
    
    needed_calls = iterations * calls_per_iteration
    remaining = status['calls_remaining']
    
    print(f"\n📋 Quota Check:")
    print(f"   Expected calls: {needed_calls} (for {iterations} iterations @ {calls_per_iteration}/iter)")
    print(f"   Available:      {remaining}")
    
    if remaining >= needed_calls:
        print(f"   ✅ Sufficient quota\n")
        return True
    else:
        possible = monitor.estimate_iterations_possible(calls_per_iteration)
        print(f"   ❌ Insufficient quota!")
        print(f"   ⚠️  Can only run {possible} iterations with current quota\n")
        return False
