# Test Script for Imperium API
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing Imperium Intent-Based Networking API" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:5000"

# Test 1: Health Check
Write-Host "[TEST 1] Health Check" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✓ Status: " -NoNewline -ForegroundColor Green
    Write-Host "Healthy"
    Write-Host "  Response: $($health | ConvertTo-Json -Compress)"
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Submit Intent - Priority
Write-Host "[TEST 2] Submit Intent: Prioritize temperature sensors" -ForegroundColor Yellow
try {
    $intent1 = @{
        intent = "prioritize temperature sensors"
    } | ConvertTo-Json
    
    $result1 = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents" -Method POST -Body $intent1 -ContentType "application/json"
    Write-Host "✓ Intent submitted successfully" -ForegroundColor Green
    Write-Host "  Intent ID: $($result1.intent_id)"
    Write-Host "  Status: $($result1.status)"
    Write-Host "  Generated Policies: $($result1.policies.Count)"
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Submit Intent - Bandwidth Limit
Write-Host "[TEST 3] Submit Intent: Limit cameras to 100KB/s" -ForegroundColor Yellow
try {
    $intent2 = @{
        intent = "limit camera-01 bandwidth to 100KB/s"
    } | ConvertTo-Json
    
    $result2 = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents" -Method POST -Body $intent2 -ContentType "application/json"
    Write-Host "✓ Intent submitted successfully" -ForegroundColor Green
    Write-Host "  Intent ID: $($result2.intent_id)"
    Write-Host "  Status: $($result2.status)"
    Write-Host "  Generated Policies: $($result2.policies.Count)"
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Submit Intent - Latency
Write-Host "[TEST 4] Submit Intent: Reduce latency for sensors" -ForegroundColor Yellow
try {
    $intent3 = @{
        intent = "reduce latency for sensor-A to 50ms"
    } | ConvertTo-Json
    
    $result3 = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents" -Method POST -Body $intent3 -ContentType "application/json"
    Write-Host "✓ Intent submitted successfully" -ForegroundColor Green
    Write-Host "  Intent ID: $($result3.intent_id)"
    Write-Host "  Status: $($result3.status)"
    Write-Host "  Generated Policies: $($result3.policies.Count)"
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: List All Intents
Write-Host "[TEST 5] List all intents" -ForegroundColor Yellow
try {
    $intents = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents" -Method GET
    Write-Host "✓ Retrieved $($intents.intents.Count) intents" -ForegroundColor Green
    foreach ($intent in $intents.intents) {
        Write-Host "  - $($intent.id): $($intent.original_intent) [$($intent.status)]"
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: List All Policies
Write-Host "[TEST 6] List all policies" -ForegroundColor Yellow
try {
    $policies = Invoke-RestMethod -Uri "$baseUrl/api/v1/policies" -Method GET
    Write-Host "✓ Retrieved $($policies.policies.Count) policies" -ForegroundColor Green
    foreach ($policy in $policies.policies) {
        Write-Host "  - $($policy.id): $($policy.type) [$($policy.status)]"
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Get Specific Intent
Write-Host "[TEST 7] Get specific intent details" -ForegroundColor Yellow
try {
    $intents = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents" -Method GET
    if ($intents.intents.Count -gt 0) {
        $intentId = $intents.intents[0].id
        $specificIntent = Invoke-RestMethod -Uri "$baseUrl/api/v1/intents/$intentId" -Method GET
        Write-Host "✓ Retrieved intent $intentId" -ForegroundColor Green
        Write-Host "  Original: $($specificIntent.intent.original_intent)"
        Write-Host "  Type: $($specificIntent.intent.parsed_intent.type)"
        Write-Host "  Targets: $($specificIntent.intent.parsed_intent.targets -join ', ')"
    } else {
        Write-Host "⚠ No intents available to query" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "API Testing Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open Grafana: http://localhost:3000 (admin/admin)"
Write-Host "  2. Open Prometheus: http://localhost:9090"
Write-Host "  3. Check MQTT logs: docker logs imperium-mqtt"
Write-Host ""
