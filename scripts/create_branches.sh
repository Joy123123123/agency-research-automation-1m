#!/bin/bash
# ============================================================
# Create All Git Branches — Agency Research Automation
# Owner: Md Jamil Islam
# 
# ব্যবহার (Usage):
#   bash scripts/create_branches.sh
#
# এই স্ক্রিপ্ট চালালে সব স্ট্যান্ডার্ড ব্রাঞ্চ তৈরি হবে:
#   main → develop → staging → release/v1.0
#                 ↗ hotfix
#   feature/* → develop
# ============================================================

set -e

echo "🌿 Agency Research Automation — Branch Setup"
echo "============================================"

REPO_URL=$(git remote get-url origin)
echo "Repo: $REPO_URL"
echo ""

# Get current branch (should be main or copilot/check-repo-status)
CURRENT=$(git branch --show-current)
echo "Current branch: $CURRENT"

# Ensure we're up to date
echo "Fetching latest from origin..."
git fetch origin

# ============================================================
# Function to create branch if it doesn't exist
# ============================================================
create_branch() {
    local BRANCH_NAME=$1
    local FROM_BRANCH=$2
    local DESCRIPTION=$3
    
    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
        echo "⚠️  Branch '$BRANCH_NAME' already exists locally — skipping"
    elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME"; then
        git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
        echo "✅ Checked out existing remote branch: $BRANCH_NAME"
        git checkout "$CURRENT"
    else
        git checkout -b "$BRANCH_NAME" "$FROM_BRANCH"
        git checkout "$CURRENT"
        echo "✅ Created branch: $BRANCH_NAME ($DESCRIPTION)"
    fi
}

# ============================================================
# Create all standard branches
# ============================================================

echo ""
echo "Creating standard branches..."
echo ""

# 1. develop — integration branch
create_branch "develop" "$CURRENT" "Development integration branch"

# 2. staging — pre-production
create_branch "staging" "$CURRENT" "Pre-production staging branch"

# 3. hotfix — emergency fixes
create_branch "hotfix" "$CURRENT" "Emergency hotfix branch"

# 4. release/v1.0 — current release
create_branch "release/v1.0" "$CURRENT" "Release v1.0 branch"

# 5. feature/research-engine — example feature branch
create_branch "feature/research-engine" "develop" "Example: research engine feature"

# 6. feature/ai-scoring — example feature branch
create_branch "feature/ai-scoring" "develop" "Example: AI lead scoring feature"

# ============================================================
# Push all branches to remote
# ============================================================

echo ""
echo "Pushing branches to remote..."
echo ""

for BRANCH in develop staging hotfix "release/v1.0" "feature/research-engine" "feature/ai-scoring"; do
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git push origin "$BRANCH:$BRANCH" 2>/dev/null && echo "✅ Pushed: $BRANCH" || echo "⚠️  Could not push: $BRANCH (may need permissions)"
    fi
done

# Back to original branch
git checkout "$CURRENT"

# ============================================================
# Summary
# ============================================================

echo ""
echo "🎉 Branch Setup Complete!"
echo ""
echo "📊 Branch Summary:"
echo ""
echo "  main              ← Production (stable)"
echo "  develop           ← Integration (all features merge here)"  
echo "  staging           ← Pre-production testing"
echo "  release/v1.0      ← Current release preparation"
echo "  hotfix            ← Emergency production fixes"
echo "  feature/*         ← New feature development"
echo ""
echo "📖 Git Flow:"
echo "  feature/* → develop → staging → main"
echo "  hotfix    → main + develop"
echo ""
echo "Current branches:"
git --no-pager branch -a
