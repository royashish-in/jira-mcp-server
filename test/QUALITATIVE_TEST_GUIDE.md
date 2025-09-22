# Qualitative Testing Guide for JIRA MCP Server

## Overview

This guide documents the qualitative testing process for validating the FastMCP JIRA server implementation beyond automated tests.

## Test Categories

### 1. MCP Protocol Integration Test

**Purpose**: Verify FastMCP protocol compliance and tool registration

```bash
# Test MCP initialization and tool listing
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | uv run python server_fastmcp.py 2>/dev/null
```

**Expected Results**:
- Proper MCP handshake response
- All 46 tools registered with auto-generated schemas
- Type validation working (string, integer, required fields)

### 2. Data Quality Assessment

**Purpose**: Validate actual JIRA data retrieval and accuracy

#### Core Operations Test
```bash
# Test user stories retrieval
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"project":"KW","limit":2}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Checklist**:
- [ ] Returns expected number of stories
- [ ] All required fields present (key, summary, status, description)
- [ ] Data format consistent
- [ ] No null/undefined values in critical fields

#### Issue Details Test
```bash
# Test specific issue retrieval
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_issue","arguments":{"key":"KW-3"}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Checklist**:
- [ ] Complete issue metadata (assignee, reporter, priority, dates)
- [ ] Proper timestamp formatting (ISO with timezone)
- [ ] Status and type information accurate
- [ ] Description handling (rich text preserved)

### 3. Search & Filtering Validation

**Purpose**: Verify JQL search accuracy and filtering

```bash
# Test JQL filtering
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_issues","arguments":{"jql":"project = KW AND status = \"In Progress\"","limit":3}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Checklist**:
- [ ] JQL query executed correctly
- [ ] All returned issues match filter criteria
- [ ] Total count matches returned count expectations
- [ ] Pagination working (limit parameter respected)

### 4. Data Consistency Verification

**Purpose**: Cross-validate data across different tools

```bash
# Test project statistics
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_project_stats","arguments":{"project":"KW"}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Process**:
1. Record total issues from `get_project_stats`
2. Sum status counts (To Do + In Progress + Done)
3. Sum type counts (Story + Task + Bug + Sub-task)
4. Verify all totals match

**Example Validation**:
```
Total Issues: 74
Status Sum: 34 + 40 + 0 = 74 ✅
Type Sum: 45 + 19 + 0 + 10 = 74 ✅
```

### 5. Workflow Operations Test

**Purpose**: Validate state management and transitions

```bash
# Test workflow transitions
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_transitions","arguments":{"key":"KW-3"}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Checklist**:
- [ ] Available transitions returned
- [ ] Transition IDs and names present
- [ ] Target statuses accurate
- [ ] Workflow logic preserved

### 6. Error Handling Assessment

**Purpose**: Verify graceful failure modes

#### Invalid Input Test
```bash
# Test invalid issue key
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_issue","arguments":{"key":"INVALID"}}}' | uv run python server_fastmcp.py 2>/dev/null
```

#### Permission/Access Test
```bash
# Test inaccessible board
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_sprints","arguments":{"board_id":"999"}}}' | uv run python server_fastmcp.py 2>/dev/null | tail -1 | jq -r '.result.content[0].text'
```

**Validation Checklist**:
- [ ] Proper error messages returned
- [ ] No server crashes on invalid input
- [ ] Graceful handling of missing data
- [ ] Informative error descriptions

## Quality Metrics

### Data Integrity Score
- **Perfect (100%)**: All cross-references match, no data inconsistencies
- **Excellent (95-99%)**: Minor formatting issues, data accurate
- **Good (90-94%)**: Some missing optional fields, core data correct
- **Poor (<90%)**: Data inconsistencies or missing critical information

### User Experience Score
- **Excellent**: Intuitive parameters, clear responses, helpful errors
- **Good**: Mostly clear, minor confusion points
- **Poor**: Confusing parameters or unclear responses

### Performance Score
- **Fast**: <1s response time for typical queries
- **Acceptable**: 1-3s response time
- **Slow**: >3s response time

## Test Execution Checklist

### Pre-Test Setup
- [ ] JIRA credentials configured in `.env`
- [ ] Test project (e.g., "KW") accessible
- [ ] FastMCP server builds without errors
- [ ] Dependencies installed (`uv sync`)

### Core Test Execution
- [ ] MCP protocol integration test passed
- [ ] Data quality assessment completed
- [ ] Search & filtering validation passed
- [ ] Data consistency verification completed
- [ ] Workflow operations test passed
- [ ] Error handling assessment completed

### Post-Test Analysis
- [ ] All test results documented
- [ ] Quality metrics calculated
- [ ] Issues identified and prioritized
- [ ] Recommendations documented

## Expected Results Summary

**Production Ready Criteria**:
- All 46 tools respond correctly
- Data integrity score ≥95%
- No critical errors in core workflows
- Graceful error handling for edge cases
- Response times <3s for typical queries

**Success Indicators**:
- ✅ MCP protocol compliance
- ✅ Accurate JIRA data retrieval
- ✅ Consistent cross-tool data
- ✅ Proper error handling
- ✅ Good user experience

## Troubleshooting Common Issues

### Connection Issues
```bash
# Test JIRA connectivity
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/myself"
```

### Permission Issues
- Verify API token has required permissions
- Check project access rights
- Validate board/sprint visibility

### Data Format Issues
- Check JIRA version compatibility
- Verify custom field mappings
- Validate rich text handling

## Automation Integration

This qualitative test process can be integrated with CI/CD:

```bash
# Run qualitative tests
./test/run_qualitative_tests.sh

# Generate quality report
./test/generate_quality_report.sh
```

## Continuous Improvement

- Update test cases when new JIRA features added
- Expand validation criteria based on user feedback
- Monitor production usage patterns
- Regular review of quality metrics