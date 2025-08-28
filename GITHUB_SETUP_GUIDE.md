
# GitHub Integration Setup Guide

This guide helps you set up the complete Jira → Replit → GitHub integration that automatically creates branches, files, and pull requests when Jira issues are created.

## 🔧 Prerequisites

1. **Replit Account** with this project running
2. **GitHub Account** with a repository for your code
3. **Jira Instance** with admin access to create webhooks
4. **GitHub Personal Access Token** with repository permissions

## 📋 Step-by-Step Setup

### 1. GitHub Setup

1. **Create/Select Repository**
   - Use an existing repository or create a new one
   - Note the owner (username/org) and repository name

2. **Create Personal Access Token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Click "Generate new token" (classic)
   - Select scopes: `repo` (Full control of private repositories)
   - Copy the generated token (save it safely!)

### 2. Replit Secrets Configuration

Add these secrets in your Replit project (🔒 Secrets tab):

```
# GitHub Integration (Required for PR creation)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_repository_name
GITHUB_BASE_BRANCH=main

# Jira Integration (Required for webhook processing)
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_jira_api_token

# AI Integration (Required for test generation)
OPENAI_API_KEY=your_openai_api_key

# Webhook Security (Recommended)
WEBHOOK_SECRET=your_random_secret_string
```

### 3. Test Your Configuration

1. **Test GitHub Integration**
   ```
   GET https://your-repl-url.replit.dev/test-github-integration
   ```

2. **Test Webhook Endpoint**
   ```
   GET https://your-repl-url.replit.dev/jira-webhook
   ```

### 4. Jira Webhook Configuration

1. **Go to Jira Admin**
   - Navigate to Settings → System → WebHooks

2. **Create New Webhook**
   - **URL**: `https://your-repl-url.replit.dev/jira-webhook`
   - **Events**: Issue → Created
   - **JQL Filter** (optional): `issuetype in ("Feature", "Task", "Story", "Bug")`

3. **Add Security** (recommended)
   - Add `?secret=your_webhook_secret` to URL
   - Or configure `X-Webhook-Secret` header if supported

### 5. Test the Complete Flow

1. **Create a Test Issue**
   - Type: Feature or Task
   - Summary: "Test GitHub integration"
   - Description: Add some details

2. **Verify Automation**
   - Check Replit console for webhook processing logs
   - Check GitHub for new branch and PR
   - Check Jira for AI analysis comment with PR link

## 🎯 What Happens Automatically

When you create a Jira issue (Feature, Task, Story, etc.):

1. **Jira sends webhook** → Replit receives it
2. **AI Analysis** → Analyzes issue and creates action plan
3. **Test Generation** → Creates comprehensive test cases
4. **GitHub Branch** → Creates `jira/ISSUE-KEY-summary` branch
5. **File Generation** → Creates:
   - `features/ISSUE-KEY.md` (specification)
   - `src/issue_key.py` (implementation scaffold)
   - `tests/test_spec_issue_key.md` (test specification)
6. **Pull Request** → Opens PR with all generated files
7. **Jira Update** → Comments on issue with PR link and AI analysis

## 📁 Generated File Structure

```
your-repo/
├── features/
│   └── ISSUE-123.md              # Feature specification
├── src/
│   └── issue_123.py              # Implementation scaffold
├── tests/
│   └── test_spec_issue_123.md    # Test specification
└── (Replit workspace)/
    ├── ai_generated_tests_issue-123.json
    ├── implementation_issue_123.py
    └── ai_analysis_issue_123.md
```

## 🔒 Security Best Practices

1. **Use Webhook Secrets** - Always validate incoming webhooks
2. **Limit GitHub Token Scope** - Only grant necessary repository permissions
3. **Review PRs** - Never auto-merge generated code
4. **Monitor Logs** - Check Replit console for any errors
5. **Test First** - Use a test repository before production

## 🐛 Troubleshooting

### Webhook Not Received
- Check Jira webhook configuration and URL
- Verify Replit app is running (click Run button)
- Check webhook secret matches

### GitHub Integration Fails
- Verify GitHub token has correct permissions
- Check repository owner/name are correct
- Ensure base branch exists

### AI Analysis Errors
- Verify OPENAI_API_KEY is set correctly
- Check API quotas and limits

### Jira Comments Not Posted
- Verify Jira credentials are correct
- Check API token permissions
- Ensure Jira URL format is correct

## 🔄 Manual Testing Commands

```bash
# Test webhook connection
curl https://your-repl-url.replit.dev/jira-webhook

# Test GitHub integration
curl https://your-repl-url.replit.dev/test-github-integration

# Test AI analysis
curl -X POST https://your-repl-url.replit.dev/ai-analyze/TEST-123 \
  -H "Content-Type: application/json" \
  -d '{"summary":"Test issue","issue_type":"Feature","description":"Test description"}'
```

## 📚 Additional Resources

- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Jira Webhook Documentation](https://developer.atlassian.com/cloud/jira/platform/webhooks/)
- [Replit Secrets Documentation](https://docs.replit.com/programming-ide/workspace-features/storing-sensitive-information-environment-variables)

---

🤖 **Ready to Code!** Once configured, your Jira issues will automatically generate GitHub PRs with AI-powered analysis and implementation scaffolds.
