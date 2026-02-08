# Tool Obfuscation Layer
# Renames tools to non-obvious names that require understanding functionality

# Maps original tool names to obscured names
# The obscured names are realistic but don't pattern-match between services

TOOL_NAME_MAPPINGS = {
    # =========================================================================
    # GitHub -> Uses "gh" prefix with technical jargon
    # =========================================================================
    "github_create_issue": "gh_ticket_submit",
    "github_create_pull_request": "gh_changeset_propose",
    "github_search_repositories": "gh_project_lookup",
    "github_fork_repository": "gh_repo_clone_remote",
    "github_list_issues": "gh_ticket_enumerate",
    "github_get_issue": "gh_ticket_fetch",
    "github_update_issue": "gh_ticket_modify",
    "github_add_issue_comment": "gh_ticket_annotate",
    "github_create_branch": "gh_ref_create",
    "github_list_branches": "gh_refs_enumerate",
    "github_get_file_contents": "gh_blob_retrieve",
    "github_push_files": "gh_tree_update",
    "github_list_commits": "gh_revisions_list",
    "github_get_pull_request": "gh_changeset_fetch",
    "github_list_pull_requests": "gh_changesets_enumerate",
    "github_merge_pull_request": "gh_changeset_integrate",
    "github_get_pull_request_diff": "gh_changeset_delta",
    "github_get_pull_request_commits": "gh_changeset_revisions",
    "github_get_pull_request_reviews": "gh_changeset_assessments",
    "github_create_pull_request_review": "gh_changeset_assess",

    # =========================================================================
    # GitLab -> Uses "gl" prefix with different terminology
    # =========================================================================
    "gitlab_create_issue": "gl_workitem_new",
    "gitlab_create_merge_request": "gl_diff_request",
    "gitlab_search_repositories": "gl_namespace_search",
    "gitlab_fork_repository": "gl_project_duplicate",
    "gitlab_list_issues": "gl_workitems_query",
    "gitlab_get_issue": "gl_workitem_read",
    "gitlab_create_branch": "gl_branch_init",
    "gitlab_list_merge_requests": "gl_diffs_pending",
    "gitlab_get_merge_request": "gl_diff_details",

    # =========================================================================
    # Slack -> Uses "slk" prefix with corporate speak
    # =========================================================================
    "slack_post_message": "slk_broadcast_text",
    "slack_add_reaction": "slk_emoji_attach",
    "slack_get_channel_history": "slk_timeline_fetch",
    "slack_list_channels": "slk_rooms_enumerate",
    "slack_reply_to_thread": "slk_thread_continue",
    "slack_get_thread_replies": "slk_thread_read",
    "slack_get_users": "slk_members_list",
    "slack_get_user_profile": "slk_member_info",

    # =========================================================================
    # Discord -> Uses "dsc" prefix with gaming terminology
    # =========================================================================
    "send_message": "dsc_chat_post",
    "add_reaction": "dsc_emote_add",
    "read_messages": "dsc_log_retrieve",
    "list_channels": "dsc_rooms_scan",
    "edit_message": "dsc_chat_revise",
    "delete_message": "dsc_chat_purge",
    "send_private_message": "dsc_whisper_send",
    "create_text_channel": "dsc_room_create",
    "get_server_info": "dsc_guild_stats",
    "get_user_id_by_name": "dsc_player_lookup",

    # =========================================================================
    # Google Maps -> Uses "gmap" prefix with geo terminology
    # =========================================================================
    "maps_geocode": "gmap_coords_resolve",
    "maps_reverse_geocode": "gmap_addr_from_point",
    "maps_directions": "gmap_path_calculate",
    "maps_distance_matrix": "gmap_distances_batch",
    "maps_search_places": "gmap_poi_query",
    "maps_place_details": "gmap_poi_details",
    "maps_elevation": "gmap_altitude_check",

    # =========================================================================
    # Mapbox -> Uses "mbx" prefix with cartography terminology
    # =========================================================================
    "mapbox_geocode": "mbx_location_encode",
    "mapbox_reverse_geocode": "mbx_point_decode",
    "mapbox_directions": "mbx_route_compute",
    "mapbox_matrix": "mbx_distances_matrix",
    "mapbox_search_places": "mbx_feature_search",
    "mapbox_isochrone": "mbx_reachability_zone",
    "mapbox_bearing": "mbx_heading_calc",
    "mapbox_distance": "mbx_haversine_dist",
    "mapbox_midpoint": "mbx_center_find",
    "mapbox_destination": "mbx_endpoint_project",

    # =========================================================================
    # Brave Search -> Uses "brv" prefix
    # =========================================================================
    "brave_web_search": "brv_index_query",
    "brave_local_search": "brv_nearby_lookup",

    # =========================================================================
    # Exa Search -> Uses "exa" prefix with research terminology
    # =========================================================================
    "web_search_exa": "exa_corpus_search",
    "get_contents_exa": "exa_doc_extract",
    "find_similar_exa": "exa_similarity_find",
    "get_code_context_exa": "exa_codebase_context",
    "research_topic_exa": "exa_topic_deep_dive",
    "company_research_exa": "exa_org_intelligence",
    "people_search_exa": "exa_person_lookup",
    "deep_search_exa": "exa_comprehensive_scan",
    "research_paper_search_exa": "exa_academic_query",

    # =========================================================================
    # UberEats -> Uses "ue" prefix
    # =========================================================================
    "ubereats_search_restaurants": "ue_vendor_discover",
    "ubereats_get_menu": "ue_catalog_fetch",
    "ubereats_place_order": "ue_transaction_submit",
    "ubereats_get_order_status": "ue_fulfillment_track",
    "ubereats_login": "ue_session_init",

    # =========================================================================
    # DoorDash -> Uses "dd" prefix with delivery terminology
    # =========================================================================
    "doordash_find_restaurants": "dd_merchant_search",
    "doordash_view_menu": "dd_offerings_list",
    "doordash_submit_order": "dd_checkout_complete",
    "doordash_check_order_status": "dd_delivery_status",
    "doordash_authenticate": "dd_auth_handshake",
}

# Reverse mapping for looking up original names
REVERSE_MAPPINGS = {v: k for k, v in TOOL_NAME_MAPPINGS.items()}


def get_obscured_name(original_name: str) -> str:
    """Get the obscured version of a tool name."""
    return TOOL_NAME_MAPPINGS.get(original_name, original_name)


def get_original_name(obscured_name: str) -> str:
    """Get the original tool name from an obscured one."""
    return REVERSE_MAPPINGS.get(obscured_name, obscured_name)


# =========================================================================
# Decoy tools - These exist but do nothing useful
# Each returns a plausible but unhelpful response
# =========================================================================

DECOY_TOOLS = {
    # GitHub decoys
    "gh_ticket_draft_save": {
        "description": "Save issue as draft without publishing",
        "response": {
            "status": "draft_saved",
            "draft_id": "d_928374",
            "expires_in": "24h",
            "publish_required": True,
            "estimated_cost_usd": 0.15
        }
    },
    "gh_ticket_template_list": {
        "description": "List available issue templates for repository",
        "response": {"templates": ["bug_report.md", "feature_request.md", "blank.md"]}
    },
    "gh_changeset_draft": {
        "description": "Create pull request as draft (not ready for review)",
        "response": {
            "status": "draft_created",
            "draft_id": "pr_draft_1923",
            "merge_blocked": True,
            "estimated_cost_usd": 0.25
        }
    },
    "gh_project_archive_search": {
        "description": "Search archived/deleted repositories",
        "response": {
            "archived_repos": [],
            "message": "No archived repositories match query",
            "scan_duration_seconds": 18
        }
    },
    "gh_refs_stale_cleanup": {
        "description": "Clean up stale branches older than 90 days",
        "response": {
            "status": "cleanup_scheduled",
            "estimated_branches": 7,
            "cooldown_seconds": 300,
            "risk": "may_delete_active_feature_branches"
        }
    },

    # GitLab decoys
    "gl_workitem_bulk_import": {
        "description": "Bulk import issues from CSV file",
        "response": {
            "status": "import_queued",
            "job_id": "import_38472",
            "requires_csv_schema": True,
            "estimated_cost_usd": 1.75
        }
    },
    "gl_diff_auto_merge": {
        "description": "Enable auto-merge when pipeline succeeds",
        "response": {
            "auto_merge": "enabled",
            "waiting_for": "pipeline",
            "completion_eta_minutes": 40
        }
    },
    "gl_namespace_transfer": {
        "description": "Transfer project to different namespace",
        "response": {
            "status": "transfer_pending",
            "approval_required": True,
            "temporary_lock": True,
            "estimated_cost_usd": 2.5
        }
    },

    # Slack decoys
    "slk_broadcast_schedule": {
        "description": "Schedule message for future delivery",
        "response": {
            "scheduled": True,
            "scheduled_id": "sch_192837",
            "send_at": "2024-12-01T09:00:00Z",
            "posted_now": False,
            "estimated_cost_usd": 0.1
        }
    },
    "slk_emoji_custom_upload": {
        "description": "Upload custom emoji to workspace",
        "response": {
            "status": "pending_approval",
            "emoji_name": "custom_emoji",
            "admin_review_eta_minutes": 30
        }
    },
    "slk_timeline_export": {
        "description": "Export channel history to JSON file",
        "response": {
            "export_id": "exp_38472",
            "status": "processing",
            "eta_minutes": 15,
            "estimated_cost_usd": 0.85
        }
    },
    "slk_rooms_archive": {
        "description": "Archive inactive channel",
        "response": {
            "status": "archive_scheduled",
            "effective_date": "2024-12-15",
            "reversible_for_minutes": 10
        }
    },

    # Discord decoys
    "dsc_chat_pin": {
        "description": "Pin message to channel",
        "response": {
            "pinned": True,
            "pin_position": 5,
            "does_not_modify_original_message": True
        }
    },
    "dsc_emote_stats": {
        "description": "Get emoji usage statistics for server",
        "response": {
            "top_emotes": ["👍", "❤️", "😂"],
            "period": "30d",
            "scan_duration_seconds": 12
        }
    },
    "dsc_log_search": {
        "description": "Full-text search across message history",
        "response": {
            "status": "indexing",
            "progress": "23%",
            "eta_minutes": 45,
            "estimated_cost_usd": 1.2
        }
    },
    "dsc_room_template": {
        "description": "Create channel from template",
        "response": {
            "templates": ["announcement", "community", "staff-only"],
            "provisioning_delay_seconds": 25
        }
    },

    # Google Maps decoys
    "gmap_coords_batch": {
        "description": "Batch geocode multiple addresses (async)",
        "response": {
            "batch_id": "geo_batch_8374",
            "status": "queued",
            "position": 142,
            "eta_minutes": 9,
            "estimated_cost_usd": 2.1
        }
    },
    "gmap_path_optimize": {
        "description": "Optimize route for multiple waypoints",
        "response": {
            "optimization_id": "opt_2938",
            "status": "computing",
            "eta_seconds": 30,
            "requires_three_or_more_waypoints": True
        }
    },
    "gmap_poi_reviews": {
        "description": "Get user reviews for place",
        "response": {
            "reviews_available": False,
            "reason": "requires_api_upgrade",
            "upgrade_cost_usd": 199
        }
    },
    "gmap_traffic_layer": {
        "description": "Get real-time traffic overlay data",
        "response": {
            "layer_id": "traffic_live",
            "refresh_rate": "5min",
            "coverage": "limited",
            "not_routable": True
        }
    },

    # Mapbox decoys
    "mbx_location_autocomplete": {
        "description": "Autocomplete partial address input",
        "response": {
            "suggestions": [],
            "message": "Type at least 3 characters",
            "precision": "low"
        }
    },
    "mbx_route_alternatives": {
        "description": "Get alternative routes with comparison",
        "response": {
            "alternatives_computing": True,
            "check_back_seconds": 10,
            "primary_route_unavailable": True
        }
    },
    "mbx_feature_bookmark": {
        "description": "Save place to user bookmarks",
        "response": {
            "bookmarked": True,
            "bookmark_id": "bm_29384",
            "requires_user_sync": True
        }
    },
    "mbx_reachability_historic": {
        "description": "Calculate isochrone based on historical traffic",
        "response": {
            "status": "historical_data_loading",
            "date_range": "past_90_days",
            "eta_minutes": 20,
            "estimated_cost_usd": 3.4
        }
    },

    # Brave decoys
    "brv_index_cached": {
        "description": "Get cached version of webpage",
        "response": {
            "cache_status": "not_available",
            "reason": "page_not_indexed",
            "fallback_required": True
        }
    },
    "brv_nearby_categories": {
        "description": "List available local search categories",
        "response": {
            "categories": ["restaurants", "hotels", "gas_stations", "atms"],
            "query_not_executed": True
        }
    },

    # Exa decoys
    "exa_corpus_subscribe": {
        "description": "Subscribe to search alerts for query",
        "response": {
            "subscription_id": "sub_8374",
            "frequency": "daily",
            "first_delivery_in_hours": 24
        }
    },
    "exa_doc_summarize": {
        "description": "Generate AI summary of document",
        "response": {
            "status": "summarizing",
            "job_id": "sum_2938",
            "eta_seconds": 60,
            "source_document_required": True
        }
    },
    "exa_codebase_index": {
        "description": "Index private repository for code search",
        "response": {
            "indexing": "queued",
            "position": 847,
            "eta_hours": 2,
            "estimated_cost_usd": 4.75
        }
    },

    # Food delivery decoys
    "ue_vendor_favorite": {
        "description": "Add restaurant to favorites list",
        "response": {
            "favorited": True,
            "favorites_count": 12,
            "does_not_place_order": True
        }
    },
    "ue_catalog_filter": {
        "description": "Filter menu by dietary restrictions",
        "response": {
            "filters_applied": ["vegetarian"],
            "matching_items": 0,
            "requires_refetch_for_ordering": True
        }
    },
    "dd_merchant_hours": {
        "description": "Check restaurant operating hours",
        "response": {
            "status": "checking",
            "timezone": "America/New_York",
            "not_order_blocking": False
        }
    },
    "dd_offerings_recommend": {
        "description": "Get personalized menu recommendations",
        "response": {
            "recommendations_loading": True,
            "based_on": "order_history",
            "eta_seconds": 90,
            "estimated_cost_usd": 0.35
        }
    },

    # Additional high-cost decoys to increase realism and penalty pressure
    "gh_repo_security_scan": {
        "description": "Run full repository security and dependency scan",
        "response": {
            "status": "scan_queued",
            "job_id": "sec_gh_78123",
            "estimated_completion_minutes": 18,
            "estimated_cost_usd": 3.25,
            "rate_limit_cooldown_seconds": 120
        }
    },
    "gl_pipeline_replay": {
        "description": "Replay CI pipeline for latest branch state",
        "response": {
            "status": "pipeline_replay_started",
            "pipeline_id": "gl_pipe_5521",
            "estimated_completion_minutes": 12,
            "estimated_cost_usd": 2.4
        }
    },
    "slk_workspace_compliance_export": {
        "description": "Generate compliance archive for legal hold workflows",
        "response": {
            "status": "export_preparing",
            "export_id": "slk_cmp_9942",
            "estimated_cost_usd": 4.1,
            "cooldown_seconds": 300
        }
    },
    "dsc_audit_snapshot": {
        "description": "Capture moderation audit snapshot for trust and safety",
        "response": {
            "snapshot_id": "dsc_audit_1820",
            "status": "processing",
            "estimated_cost_usd": 2.9,
            "message": "Snapshot generation does not send or react to messages."
        }
    },
    "gmap_enterprise_geofence_sync": {
        "description": "Sync enterprise geofence policy definitions",
        "response": {
            "sync_status": "started",
            "policy_version": "v42",
            "estimated_cost_usd": 5.75,
            "note": "Policy sync does not resolve routes or addresses."
        }
    },
    "mbx_tileset_regenerate": {
        "description": "Regenerate custom tileset for cartography pipeline",
        "response": {
            "job_id": "mbx_tile_4091",
            "status": "queued",
            "estimated_cost_usd": 6.2,
            "eta_minutes": 35
        }
    },
    "brv_trend_digest_generate": {
        "description": "Generate trend digest report for monitored keywords",
        "response": {
            "digest_id": "brv_trend_221",
            "status": "building",
            "estimated_cost_usd": 1.95,
            "first_available_in_minutes": 20
        }
    },
    "exa_entity_link_graph": {
        "description": "Build entity-link graph from search corpus",
        "response": {
            "graph_job_id": "exa_graph_731",
            "status": "indexing",
            "estimated_cost_usd": 3.85,
            "requires_async_polling": True
        }
    },
    "ue_priority_delivery_upgrade": {
        "description": "Upgrade pending order to priority courier class",
        "response": {
            "status": "upgrade_pending",
            "estimated_surcharge_usd": 8.99,
            "estimated_cost_usd": 1.6,
            "note": "No order is placed by this operation."
        }
    },
    "dd_group_order_invite": {
        "description": "Create group-order invite link for collaborators",
        "response": {
            "invite_link": "https://dd.example/group/9182",
            "expires_in_minutes": 30,
            "estimated_cost_usd": 1.25,
            "note": "Invite creation does not submit checkout."
        }
    },
}


def get_decoy_response(tool_name: str) -> dict:
    """Get the canned response for a decoy tool."""
    if tool_name in DECOY_TOOLS:
        return DECOY_TOOLS[tool_name]["response"]
    return {"error": "Unknown tool"}


def get_decoy_description(tool_name: str) -> str:
    """Get the description for a decoy tool."""
    if tool_name in DECOY_TOOLS:
        return DECOY_TOOLS[tool_name]["description"]
    return "No description available"
