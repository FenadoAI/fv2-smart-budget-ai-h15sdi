"""Entitlement management and role-based access control."""

from functools import wraps
from fastapi import HTTPException
from typing import Callable


# Tier hierarchy for comparison
TIER_HIERARCHY = {"free": 0, "pro": 1, "premium": 2}


# Feature definitions per tier
TIER_FEATURES = {
    "free": {
        "csv_upload_limit_per_week": 1,
        "goal_limit": 1,
        "ai_insights_depth": "basic",
        "bank_sync_enabled": False,
        "autopilot_enabled": False,
        "export_formats": ["pdf"],
        "support_tier": "community",
        "weekly_reports": False,
        "smart_alerts": False,
        "custom_date_reports": False,
    },
    "pro": {
        "csv_upload_limit_per_week": 999,
        "goal_limit": 999,
        "ai_insights_depth": "advanced",
        "bank_sync_enabled": False,
        "autopilot_enabled": False,
        "export_formats": ["pdf"],
        "support_tier": "priority_email",
        "weekly_reports": True,
        "smart_alerts": True,
        "custom_date_reports": False,
    },
    "premium": {
        "csv_upload_limit_per_week": 999,
        "goal_limit": 999,
        "ai_insights_depth": "premium",
        "bank_sync_enabled": True,
        "autopilot_enabled": True,
        "export_formats": ["pdf", "csv", "excel"],
        "support_tier": "24x7_chat",
        "weekly_reports": True,
        "smart_alerts": True,
        "custom_date_reports": True,
    },
}


def get_entitlements(tier: str, status: str) -> dict:
    """Get entitlements for a given subscription tier."""
    # If trial or expired, downgrade to free
    if status in ["expired", "cancelled"]:
        tier = "free"

    features = TIER_FEATURES.get(tier, TIER_FEATURES["free"])

    return {
        "tier": tier,
        "status": status,
        "features": features,
        "limits": {
            "csv_uploads_per_week": features["csv_upload_limit_per_week"],
            "max_goals": features["goal_limit"],
        },
    }


def check_feature_access(user_tier: str, required_feature: str, required_tier: str = None) -> bool:
    """Check if user has access to a specific feature."""
    if required_tier:
        user_tier_level = TIER_HIERARCHY.get(user_tier, 0)
        required_tier_level = TIER_HIERARCHY.get(required_tier, 0)
        return user_tier_level >= required_tier_level

    # Check specific feature
    features = TIER_FEATURES.get(user_tier, TIER_FEATURES["free"])
    return features.get(required_feature, False)


def require_tier(minimum_tier: str):
    """Decorator to gate endpoints by subscription tier."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (injected by Depends)
            current_user = kwargs.get("current_user")
            db = kwargs.get("db") or kwargs.get("request").app.state.db

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Get user subscription
            subscription = await db.subscriptions.find_one({"user_id": current_user.id})

            user_tier = "free"
            user_status = "active"
            if subscription:
                user_tier = subscription.get("tier", "free")
                user_status = subscription.get("status", "active")

                # If status is expired or cancelled, treat as free
                if user_status in ["expired", "cancelled"]:
                    user_tier = "free"

            # Check tier hierarchy
            user_tier_level = TIER_HIERARCHY.get(user_tier, 0)
            required_tier_level = TIER_HIERARCHY.get(minimum_tier, 0)

            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_gated",
                        "message": f"This feature requires {minimum_tier.title()} subscription",
                        "current_tier": user_tier,
                        "required_tier": minimum_tier,
                        "upgrade_url": "/pricing",
                    },
                )

            # Proceed with the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_feature(feature_name: str, minimum_tier: str = "pro"):
    """Decorator to gate endpoints by specific feature."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            db = kwargs.get("db") or kwargs.get("request").app.state.db

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Get user subscription
            subscription = await db.subscriptions.find_one({"user_id": current_user.id})

            user_tier = "free"
            if subscription:
                user_tier = subscription.get("tier", "free")
                user_status = subscription.get("status", "active")

                if user_status in ["expired", "cancelled"]:
                    user_tier = "free"

            # Check feature access
            features = TIER_FEATURES.get(user_tier, TIER_FEATURES["free"])
            has_access = features.get(feature_name, False)

            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_gated",
                        "message": f"{feature_name.replace('_', ' ').title()} requires {minimum_tier.title()} subscription",
                        "current_tier": user_tier,
                        "required_tier": minimum_tier,
                        "upgrade_url": "/pricing",
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
