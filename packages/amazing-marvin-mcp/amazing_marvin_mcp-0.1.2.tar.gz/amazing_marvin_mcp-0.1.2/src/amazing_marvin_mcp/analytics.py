"""Analytics functions for Amazing Marvin MCP."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast

from .api import MarvinAPIClient
from .cache import done_items_cache
from .date_utils import DateUtils

logger = logging.getLogger(__name__)


def get_productivity_summary(api_client: MarvinAPIClient) -> Dict[str, Any]:
    """Get productivity summary with goals progress and tracking status."""
    today = DateUtils.get_today()

    # Get goals
    goals = api_client.get_goals()

    # Get account info for streaks/stats
    account = api_client.get_account_info()

    # Get currently tracked item
    tracked_item = api_client.get_currently_tracked_item()

    return {
        "date": today,
        "active_goals": len(goals),
        "goals": goals,
        "account_stats": account,
        "currently_tracking": tracked_item,
        "summary": f"You have {len(goals)} active goals",
    }


def get_productivity_summary_for_time_range(
    api_client: MarvinAPIClient,
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a productivity summary for a specified time range using efficient API calls.

    Args:
        api_client: MarvinAPIClient instance
        days: Number of days to look back from today (default: 7 for weekly summary)
        start_date: Start date in YYYY-MM-DD format (overrides days parameter)
        end_date: End date in YYYY-MM-DD format (defaults to today if start_date provided)

    Examples:
        get_productivity_summary_for_time_range(api_client, days=30)  # Past 30 days
        get_productivity_summary_for_time_range(api_client, start_date='2025-06-01', end_date='2025-06-10')
        get_productivity_summary_for_time_range(api_client, start_date='2025-06-01')  # From June 1st to today
    """
    try:
        # Determine date range using helper function
        date_list, start, end = DateUtils.generate_date_range(
            days, start_date, end_date
        )

        range_summary = {
            "period_start": DateUtils.format_date(start),
            "period_end": DateUtils.format_date(end),
            "total_days": len(date_list),
            "total_completed": 0,
            "daily_breakdown": {},
            "by_project": {},
            "all_completed_tasks": [],  # Include all tasks for correlation
            "tasks_by_date": {},  # Tasks organized by date
            "tasks_by_project": {},  # Tasks organized by project
            "most_productive_day": None,
            "least_productive_day": None,
            "average_per_day": 0.0,
            "api_calls": 0,
        }

        # Get data for each date efficiently
        for date_str in date_list:
            _process_date_data(date_str, api_client, range_summary)

        # Calculate statistics
        _calculate_statistics(range_summary)

        # Sort projects by completion count
        by_project = cast("Dict[str, int]", range_summary["by_project"])
        range_summary["top_projects"] = sorted(
            by_project.items(), key=lambda x: x[1], reverse=True
        )[:5]  # Top 5 projects

        # Add project name resolution for better UX
        try:
            projects = api_client.get_projects()
            project_names = {
                proj.get("_id"): proj.get("title", "Unnamed Project")
                for proj in projects
            }

            range_summary["project_names"] = project_names
            top_projects = cast("List[Tuple[str, int]]", range_summary["top_projects"])
            range_summary["top_projects_with_names"] = [
                {
                    "project_id": proj_id,
                    "project_name": project_names.get(
                        proj_id,
                        "Unknown Project" if proj_id != "unassigned" else "Unassigned",
                    ),
                    "completed_count": count,
                }
                for proj_id, count in top_projects
            ]
        except Exception as e:
            logger.warning("Could not resolve project names: %s", e)
            range_summary["project_names"] = {}
            range_summary["top_projects_with_names"] = []

        # Add efficiency metrics using cache stats
        cache_stats = done_items_cache.get_stats()
        range_summary["efficiency_metrics"] = {
            "cached_dates": cache_stats["cached_dates"],
            "total_cached_items": cache_stats["total_cached_items"],
            "total_api_calls": range_summary["api_calls"],
        }

    except Exception as e:
        logger.exception("Error getting productivity summary")
        return {
            "error": str(e),
            "total_completed": 0,
            "daily_breakdown": {},
            "by_project": {},
        }
    else:
        return range_summary


def get_completed_tasks(api_client: MarvinAPIClient) -> Dict[str, Any]:
    """Get completed tasks using the efficient /doneItems endpoint with date filtering.

    Returns completed tasks with efficient date-based categorization.
    """
    try:
        yesterday = DateUtils.get_yesterday()

        # Use efficient date-filtered API calls
        today_completed = api_client.get_done_items()  # Defaults to today
        yesterday_completed = api_client.get_done_items(date=yesterday)

        # For older items, we could either:
        # 1. Make additional API calls for specific dates
        # 2. Get all items and filter (less efficient but comprehensive)
        # For now, let's be comprehensive but note the efficiency trade-off
        all_done_items = api_client.get_done_items()

        # Calculate older items by exclusion
        today_ids = {item.get("_id") for item in today_completed}
        yesterday_ids = {item.get("_id") for item in yesterday_completed}

        older_completed = [
            item
            for item in all_done_items
            if item.get("_id") not in today_ids and item.get("_id") not in yesterday_ids
        ]

        today_count = len(today_completed)
        yesterday_count = len(yesterday_completed)

        return {
            "completed_tasks": all_done_items,
            "total_completed": len(all_done_items),
            "today_completed": today_completed,
            "yesterday_completed": yesterday_completed,
            "older_completed": older_completed,
            "today_count": today_count,
            "yesterday_count": yesterday_count,
            "older_count": len(older_completed),
            "date_breakdown": {
                "today": today_count,
                "yesterday": yesterday_count,
                "older": len(older_completed),
            },
            "source": "Amazing Marvin /doneItems endpoint with efficient date filtering",
            "efficiency_note": f"Today and yesterday use efficient API filtering ({today_count} + {yesterday_count}) items, older items calculated by exclusion",
        }

    except Exception as e:
        logger.exception("Error getting completed tasks")
        return {
            "completed_tasks": [],
            "total_completed": 0,
            "error": str(e),
            "source": "Error occurred",
        }


def _process_date_data(
    date_str: str, api_client: MarvinAPIClient, range_summary: Dict[str, Any]
) -> None:
    """Process data for a single date and update the range_summary dict."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = date_obj.strftime("%A")
    is_today = date_str == DateUtils.get_today()

    try:
        # Use cached API call
        items = done_items_cache.get(date_str, api_client)
        count = len(items)

        # Track API calls
        range_summary["api_calls"] += 1

        range_summary["daily_breakdown"][date_str] = {
            "count": count,
            "weekday": weekday,
            "is_today": is_today,
            "tasks": items,  # Include actual tasks
        }
        range_summary["total_completed"] += count

        # Store tasks by date
        range_summary["tasks_by_date"][date_str] = items

        # Add to all completed tasks
        range_summary["all_completed_tasks"].extend(items)

        # Track by project with detailed task info
        for item in items:
            project_id = item.get("parentId", "unassigned")

            # Count by project
            if project_id not in range_summary["by_project"]:
                range_summary["by_project"][project_id] = 0
            range_summary["by_project"][project_id] += 1

            # Store tasks by project
            if project_id not in range_summary["tasks_by_project"]:
                range_summary["tasks_by_project"][project_id] = []
            range_summary["tasks_by_project"][project_id].append(
                {"task": item, "completed_date": date_str, "weekday": weekday}
            )

    except Exception as e:
        logger.warning("Error getting done items for %s: %s", date_str, e)
        range_summary["daily_breakdown"][date_str] = {
            "count": 0,
            "weekday": weekday,
            "is_today": is_today,
            "tasks": [],
        }
        range_summary["tasks_by_date"][date_str] = []


def _calculate_statistics(range_summary: Dict[str, Any]) -> None:
    """Calculate statistics from collected data and update range_summary."""
    if range_summary["daily_breakdown"]:
        daily_counts = [
            (date, data["count"])
            for date, data in range_summary["daily_breakdown"].items()
        ]
        sorted_days = sorted(daily_counts, key=lambda x: x[1])

        range_summary["least_productive_day"] = {
            "date": sorted_days[0][0],
            "count": sorted_days[0][1],
            "weekday": range_summary["daily_breakdown"][sorted_days[0][0]]["weekday"],
        }
        range_summary["most_productive_day"] = {
            "date": sorted_days[-1][0],
            "count": sorted_days[-1][1],
            "weekday": range_summary["daily_breakdown"][sorted_days[-1][0]]["weekday"],
        }

        range_summary["average_per_day"] = range_summary["total_completed"] / len(
            daily_counts
        )
