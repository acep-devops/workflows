# workflows
A centralized collection of reusable GitHub Actions workflows and automation templates for ACEP.

## Mattermost Notification Workflow
This reusable workflow standardizes Mattermost alerts across different repositories. It supports presets for common events like Pull Request reviews and Job Status updates.

### 🚀 Usage
To use this workflow, create a job in your caller workflow (e.g., `.github/workflows/deploy.yml`).

#### **Inputs**
| Input | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `preset` | Type of message: `status`, `review_request`, `review_decision`, or `custom`. | No | `custom` |
| `job_status` | The result of the previous job (`success`, `failure`). Required for `status`. | No | N/A |
| `title` | Overrides the prefix in status messages (e.g., "Production Deploy"). | No | `Action` |
| `message` | Appends a custom string or note to the bottom of any preset. | No | `""` |

#### **Secrets**

| Secret | Description | Required |
| :--- | :--- | :--- |
| `MM_WEBHOOK_URL` | The incoming webhook URL from your Mattermost channel, set this as a repository secret. | Yes |


#### **Pull Request Notifications (Requests & Decisions)**

Use this combined workflow to handle both new review requests and submitted review decisions (Approvals/Changes Requested).

```yml
name: PR Notifications

on:
  pull_request:
    types: [review_requested]
  pull_request_review:
    types: [submitted]

jobs:
  # Triggered when a reviewer is specifically requested
  notify-on-request:
    if: github.event.action == 'review_requested'
    uses: acep-devops/workflows/.github/workflows/mattermost-notify.yml@main
    with:
      preset: "review_request"
    secrets:
      MM_WEBHOOK_URL: ${{ secrets.MM_WEBHOOK_URL }}

  # Triggered when a reviewer submits an Approval or Changes Requested
  notify-on-submit:
    if: github.event.action == 'submitted'
    uses: acep-devops/workflows/.github/workflows/mattermost-notify.yml@main
    with:
      preset: "review_decision"
    secrets:
      MM_WEBHOOK_URL: ${{ secrets.MM_WEBHOOK_URL }}
```

**Example Outputs**
```md
👀 Review Requested
Repo: RepoName
PR: PR# - PR Title
Requested By: ReviewRequestByName
Reviewer: ReviewerName
[Review Now](link)
```

```md
🔄 Changes Requested
Repo: RepoName
PR: PR# - PR Title
Reviewer: ReviewerName
[Read Review](link)
```

```md
✅ PR Approved
Repo: RepoName
PR: PR# - PR Title
Reviewer: ReviewerName
[Read Review](link)
```

#### **Job Status Preset**

Use this to report whether a build, test, or deploy succeeded or failed. This can be customized by changing `if` conditions to the `notify` job.

```yml
# ... rest of workflow

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: exit 1  # Simulating a failure

  notify:
    needs: [build]
    if: always()
    uses: acep-devops/workflows/.github/workflows/mattermost-notify.yml@main
    with:
      preset: "status"
      job_status: ${{ needs.build.result }}
      title: "Docker Build"
    secrets:
      MM_WEBHOOK_URL: ${{ secrets.MM_WEBHOOK_URL }}
```

**Example Outputs**
```md
❌ CI on Push to Main Failed
Repo: RepoName
Ref: PR#/merge
Author: AuthorName
[View Logs](link)
```
```md
✅ Docker Deploy on Branch(main) Succeeded
Repo: RepoName
Ref: PR#/merge
Author: AuthorName
[View Logs](link)
```

#### **Custom Preset**

TO DO