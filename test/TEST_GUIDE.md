# JIRA MCP Server Test Suite

Comprehensive test suite that validates all 46 JIRA MCP tools as end users would use them.

## Usage

### Prerequisites
- Docker installed (for Docker tests)
- `.env` file with valid JIRA credentials
- JIRA project with key "KW" (or modify test parameters)

### Run Tests

```bash
# Test with Docker (recommended)
python test_suite.py

# Test locally (requires Python environment)
python test_suite.py --local
```

### Test Coverage

**46 Tools Tested Across 8 Categories:**

1. **Core JIRA Operations (10 tools)**
   - get_user_stories, get_issue, get_projects, search_issues, etc.

2. **Workflow Management (6 tools)**
   - get_transitions, transition_issue, add_comment, assign_issue, etc.

3. **File & Attachment Management (3 tools)**
   - list_attachments, upload_attachment, download_attachment

4. **Project & User Management (5 tools)**
   - get_issue_types, get_project_components, get_users, etc.

5. **Agile & Sprint Management (4 tools)**
   - get_boards, get_sprints, get_sprint_issues, add_to_sprint

6. **Issue Relationships & Hierarchy (4 tools)**
   - get_subtasks, create_subtask, link_issues, get_issue_links

7. **Batch Operations (2 tools)**
   - bulk_update_issues, clone_issue

8. **Webhooks & Notifications (3 tools)**
   - list_webhooks, add_watcher, get_watchers

9. **Reporting & Analytics (3 tools)**
   - get_time_tracking_report, get_project_roles, export_issues

10. **Advanced Admin & Edge Cases (6 tools)**
    - create_webhook, create_version, get_user_permissions, etc.

### Expected Results

- **SUCCESS**: Tool returns valid JIRA data
- **ERROR**: Tool returns error message (often due to missing data/permissions)
- **FAILED**: Tool doesn't respond or server issues

### Success Rate Interpretation

- **80%+**: Excellent - Server working well
- **60-79%**: Good - Most tools functional
- **40-59%**: Fair - Some issues need attention
- **<40%**: Poor - Major issues detected

### Sample Output

```
🧪 Starting Comprehensive JIRA MCP Server Test Suite
============================================================

📋 Core JIRA Operations
Testing get_user_stories: Fetch user stories
  ✅ SUCCESS: 1247 chars returned
Testing get_issue: Get specific issue
  ✅ SUCCESS: 892 chars returned

📊 TEST RESULTS SUMMARY
============================================================
✅ SUCCESS: 38/46 tools
⚠️  ERROR:   6/46 tools
❌ FAILED:  2/46 tools

🎯 Overall Success Rate: 82.6%
🎉 EXCELLENT: Server is working well!
```

### Customization

Edit `test_suite.py` to modify:
- Project key (default: "KW")
- Issue keys for testing
- Test parameters and arguments
- Docker image name