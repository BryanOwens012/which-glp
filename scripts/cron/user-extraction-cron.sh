#!/bin/bash
#
# User Extraction Cron Job with Retry Logic
#
# This script triggers the user-extraction service with automatic retries
# and exponential backoff. Designed to run as a Railway cron job.
#
# Usage:
#   ./scripts/cron-user-extraction.sh

set -euo pipefail

# Configuration
SERVICE_URL="${USER_EXTRACTION_URL:-http://localhost:8002}"
MAX_RETRIES=5
INITIAL_TIMEOUT=900   # 15 minutes (user extraction can be slow)
MAX_TIMEOUT=3600      # 60 minutes
RETRY_DELAY=60        # 1 minute initial delay
USER_LIMIT=50         # Number of users to extract per run
RATE_LIMIT_DELAY=2.0  # Delay between users (Reddit API rate limiting)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Trigger user extraction with retry logic
trigger_user_extraction() {
    local attempt=1
    local timeout=$INITIAL_TIMEOUT
    local delay=$RETRY_DELAY

    log "=========================================="
    log "USER EXTRACTION CRON JOB STARTING"
    log "Service URL: $SERVICE_URL"
    log "User limit: $USER_LIMIT users"
    log "Rate limit delay: ${RATE_LIMIT_DELAY}s"
    log "Max retries: $MAX_RETRIES"
    log "=========================================="

    while [ $attempt -le $MAX_RETRIES ]; do
        log "Attempt $attempt/$MAX_RETRIES (timeout: ${timeout}s)"

        # Check if service is already running
        log "Checking service status..."
        status_response=$(curl -s -w "\n%{http_code}" --max-time 10 "$SERVICE_URL/api/status" || echo "000")
        status_code=$(echo "$status_response" | tail -n1)
        status_body=$(echo "$status_response" | sed '$d')

        if [ "$status_code" != "200" ]; then
            log_error "Service health check failed (HTTP $status_code)"

            if [ $attempt -eq $MAX_RETRIES ]; then
                log_error "Max retries reached. Service appears to be down."
                exit 1
            fi

            log_warning "Waiting ${delay}s before retry..."
            sleep $delay
            delay=$((delay * 2))
            attempt=$((attempt + 1))
            continue
        fi

        # Check if analysis is already running
        is_running=$(echo "$status_body" | grep -o '"analysis_running":[^,}]*' | cut -d':' -f2 | tr -d ' ')

        if [ "$is_running" = "true" ]; then
            log_warning "User analysis already running. Waiting for completion..."

            # Wait for current analysis to complete (with timeout)
            local wait_time=0
            while [ $wait_time -lt $timeout ]; do
                sleep 60  # Check every minute
                wait_time=$((wait_time + 60))

                status_response=$(curl -s -w "\n%{http_code}" --max-time 10 "$SERVICE_URL/api/status" || echo "000")
                status_code=$(echo "$status_response" | tail -n1)
                status_body=$(echo "$status_response" | sed '$d')

                if [ "$status_code" = "200" ]; then
                    is_running=$(echo "$status_body" | grep -o '"analysis_running":[^,}]*' | cut -d':' -f2 | tr -d ' ')

                    if [ "$is_running" = "false" ]; then
                        log "Previous analysis completed. Proceeding..."
                        break
                    fi

                    log "Still running... waited ${wait_time}s"
                else
                    log_error "Status check failed during wait"
                    break
                fi
            done

            if [ $wait_time -ge $timeout ]; then
                log_warning "Timeout waiting for previous analysis. Skipping this run."
                exit 0
            fi
        fi

        # Check stats before triggering
        log "Checking unanalyzed user count..."
        stats_response=$(curl -s -w "\n%{http_code}" --max-time 10 "$SERVICE_URL/api/stats" || echo "000")
        stats_code=$(echo "$stats_response" | tail -n1)
        stats_body=$(echo "$stats_response" | sed '$d')

        if [ "$stats_code" = "200" ]; then
            unanalyzed=$(echo "$stats_body" | grep -o '"unanalyzed_users":[0-9]*' | cut -d':' -f2)
            total=$(echo "$stats_body" | grep -o '"total_users":[0-9]*' | cut -d':' -f2)
            log "Total users: $total, Unanalyzed: $unanalyzed"

            if [ "$unanalyzed" = "0" ]; then
                log_success "No unanalyzed users found. Skipping this run."
                exit 0
            fi
        else
            log_warning "Could not fetch stats, proceeding anyway..."
        fi

        # Trigger user extraction
        log "Triggering user analysis (limit: $USER_LIMIT users)..."

        response=$(curl -s -w "\n%{http_code}" \
            --max-time $timeout \
            -X POST "$SERVICE_URL/api/analyze" \
            -H "Content-Type: application/json" \
            -d "{\"limit\": $USER_LIMIT, \"rate_limit_delay\": $RATE_LIMIT_DELAY}" \
            || echo "000")

        http_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | sed '$d')

        if [ "$http_code" = "200" ]; then
            log_success "User extraction triggered successfully!"
            log "Response: $response_body"

            # Wait a bit then check status
            log "Waiting 10s before status check..."
            sleep 10

            status_response=$(curl -s -w "\n%{http_code}" --max-time 10 "$SERVICE_URL/api/status" || echo "000")
            status_code=$(echo "$status_response" | tail -n1)

            if [ "$status_code" = "200" ]; then
                log_success "User analysis job is running in background"
                log "=========================================="
                log "CRON JOB COMPLETED SUCCESSFULLY"
                log "=========================================="
                exit 0
            else
                log_warning "Could not verify analysis status, but trigger succeeded"
                exit 0
            fi
        elif [ "$http_code" = "409" ]; then
            log_warning "User analysis already running (409 Conflict)"
            log "Response: $response_body"
            exit 0
        else
            log_error "User extraction failed (HTTP $http_code)"
            log_error "Response: $response_body"

            if [ $attempt -eq $MAX_RETRIES ]; then
                log_error "Max retries reached. Giving up."
                exit 1
            fi

            log_warning "Waiting ${delay}s before retry..."
            sleep $delay

            # Exponential backoff
            delay=$((delay * 2))
            timeout=$((timeout < MAX_TIMEOUT ? timeout * 2 : MAX_TIMEOUT))
            attempt=$((attempt + 1))
        fi
    done

    log_error "Failed after $MAX_RETRIES attempts"
    exit 1
}

# Main execution
trigger_user_extraction
